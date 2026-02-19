import logging
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from paypal.standard.ipn.models import PayPalIPN
from paypal.standard.ipn.signals import valid_ipn_received

from .models import SubscriptionEvent, UserProfile

logger = logging.getLogger(__name__)


# Automatically create a Profile when a User is created"""
@receiver(post_save, sender=get_user_model())
def create_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


def _paypal_event_id(ipn_obj: Any) -> str:
    ipn_track_id = str(getattr(ipn_obj, "ipn_track_id", "") or "").strip()
    txn_id = str(getattr(ipn_obj, "txn_id", "") or "").strip()
    subscr_id = str(getattr(ipn_obj, "subscr_id", "") or "").strip()
    invoice = str(getattr(ipn_obj, "invoice", "") or "").strip()
    txn_type = str(getattr(ipn_obj, "txn_type", "") or "").strip() or "unknown"

    suffix = ipn_track_id or txn_id or f"{subscr_id}:{invoice}" or invoice or "no-id"
    event_id = f"paypal:{txn_type}:{suffix}"
    return event_id[:128]


def _resolve_profile(ipn_obj: Any) -> UserProfile | None:
    custom = str(getattr(ipn_obj, "custom", "") or "").strip()
    if custom.isdigit():
        return UserProfile.objects.filter(user_id=int(custom)).first()

    invoice = str(getattr(ipn_obj, "invoice", "") or "").strip()
    if invoice.startswith("sub-"):
        # Expected format from checkout form: sub-<user_id>-<uuid>
        parts = invoice.split("-", 2)
        if len(parts) >= 2 and parts[1].isdigit():
            return UserProfile.objects.filter(user_id=int(parts[1])).first()

    subscr_id = str(getattr(ipn_obj, "subscr_id", "") or "").strip()
    if subscr_id:
        return UserProfile.objects.filter(provider_subscription_id=subscr_id).first()
    return None


def _normalize_paypal_event(ipn_obj: Any) -> str | None:
    txn_type = str(getattr(ipn_obj, "txn_type", "") or "").strip().lower()
    payment_status = str(getattr(ipn_obj, "payment_status", "") or "").strip().lower()

    if txn_type in {"subscr_cancel", "subscr_eot"}:
        return "subscription.canceled"
    if txn_type == "subscr_failed":
        return "subscription.payment_failed"
    if txn_type in {"subscr_signup", "subscr_modify"}:
        return "subscription.updated"
    if txn_type == "subscr_payment":
        if payment_status in {"completed", "processed"}:
            return "subscription.activated"
        if payment_status in {"failed", "denied"}:
            return "subscription.payment_failed"
        return "subscription.updated"
    return None


def _apply_subscription_event(profile: UserProfile, event_id: str, event_type: str, payload: dict) -> None:
    provider_customer_id = str(payload.get("provider_customer_id", "") or "")
    provider_subscription_id = str(payload.get("provider_subscription_id", "") or "")

    if provider_customer_id:
        profile.provider_customer_id = provider_customer_id
    if provider_subscription_id:
        profile.provider_subscription_id = provider_subscription_id
    profile.last_subscription_event_id = event_id

    if event_type == "subscription.activated":
        profile.apply_plan(UserProfile.PLAN_PRO)
    elif event_type == "subscription.canceled":
        profile.apply_plan(UserProfile.PLAN_FREE)
        profile.subscription_state = UserProfile.SUBSCRIPTION_CANCELED
    elif event_type == "subscription.payment_failed":
        profile.subscription_state = UserProfile.SUBSCRIPTION_PAST_DUE
    elif event_type == "subscription.updated":
        provider_status = str(payload.get("status", "")).lower().strip()
        if provider_status in {"active", "trialing"}:
            profile.subscription_state = UserProfile.SUBSCRIPTION_ACTIVE
        elif provider_status in {"past_due", "unpaid"}:
            profile.subscription_state = UserProfile.SUBSCRIPTION_PAST_DUE
        elif provider_status in {"canceled", "cancelled"}:
            profile.apply_plan(UserProfile.PLAN_FREE)
            profile.subscription_state = UserProfile.SUBSCRIPTION_CANCELED


@receiver(valid_ipn_received, dispatch_uid="users.paypal.valid_ipn")
def handle_valid_paypal_ipn(sender, **kwargs):
    """Bridge PayPal IPN events into SubscriptionEvent/UserProfile updates."""
    ipn_obj = kwargs.get("ipn_obj")
    if ipn_obj is None:
        return

    expected_receiver = str(getattr(settings, "PAYPAL_RECEIVER_EMAIL", "") or "").strip().lower()
    if not expected_receiver:
        logger.warning("Skipping PayPal IPN: PAYPAL_RECEIVER_EMAIL is not configured")
        return

    receiver_email = str(getattr(ipn_obj, "receiver_email", "") or "").strip().lower()
    if receiver_email != expected_receiver:
        logger.warning(
            "Skipping PayPal IPN: receiver email mismatch (got=%s expected=%s)",
            receiver_email,
            expected_receiver,
        )
        return

    event_type = _normalize_paypal_event(ipn_obj)
    if not event_type:
        return

    profile = _resolve_profile(ipn_obj)
    if profile is None:
        logger.warning("Skipping PayPal IPN: unable to resolve profile")
        return

    provider_customer_id = str(
        getattr(ipn_obj, "payer_id", "") or getattr(ipn_obj, "payer_email", "") or ""
    ).strip()
    provider_subscription_id = str(getattr(ipn_obj, "subscr_id", "") or "").strip()
    provider_status = str(getattr(ipn_obj, "payment_status", "") or "").strip()
    event_id = _paypal_event_id(ipn_obj)
    payload = {
        "user_id": profile.user_id,
        "provider_customer_id": provider_customer_id,
        "provider_subscription_id": provider_subscription_id,
        "status": provider_status,
        "txn_type": str(getattr(ipn_obj, "txn_type", "") or ""),
        "txn_id": str(getattr(ipn_obj, "txn_id", "") or ""),
        "invoice": str(getattr(ipn_obj, "invoice", "") or ""),
        "mc_gross": str(getattr(ipn_obj, "mc_gross", "") or ""),
        "mc_currency": str(getattr(ipn_obj, "mc_currency", "") or ""),
    }

    event, created = SubscriptionEvent.objects.get_or_create(
        event_id=event_id,
        defaults={"event_type": event_type, "payload": payload, "profile": profile},
    )
    if not created and event.processed:
        return

    if not created:
        event.event_type = event_type
        event.payload = payload
        event.profile = profile
        event.processing_error = ""
        event.save(update_fields=["event_type", "payload", "profile", "processing_error", "updated_at"])

    try:
        with transaction.atomic():
            locked_profile = UserProfile.objects.select_for_update().get(pk=profile.pk)
            _apply_subscription_event(locked_profile, event_id, event_type, payload)
            locked_profile.save()
            event.processed = True
            event.processing_error = ""
            event.save(update_fields=["processed", "processing_error", "updated_at"])
    except Exception as exc:  # pragma: no cover - defensive logging path
        event.processing_error = str(exc)
        event.save(update_fields=["processing_error", "updated_at"])
        logger.exception("PayPal IPN processing failed for event_id=%s", event_id)


@receiver(post_save, sender=PayPalIPN, dispatch_uid="users.paypal.ipn_post_save")
def handle_paypal_ipn_post_save(sender, instance: PayPalIPN, created: bool, **kwargs):
    """
    Fallback bridge for environments where `valid_ipn_received` may be missed.

    Idempotency is enforced by SubscriptionEvent.event_id uniqueness.
    """
    if getattr(instance, "flag", False):
        return
    handle_valid_paypal_ipn(sender=sender, ipn_obj=instance)
