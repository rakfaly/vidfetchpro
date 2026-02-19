import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from paypal.standard.ipn.models import PayPalIPN

from apps.users.forms import CustomPayPalPaymentsForm
from apps.users.models import SubscriptionEvent, UserProfile
from apps.users.signals import handle_valid_paypal_ipn

PENDING_PRO_CHECKOUT_SESSION_KEY = "pending_pro_checkout"


def _reconcile_recent_paypal_ipn_for_user(user_id: int, limit: int = 20) -> None:
    """Process recent PayPal IPNs for this user idempotently."""
    qs = PayPalIPN.objects.filter(custom=str(user_id)).order_by("-created_at")[:limit]
    for ipn_obj in qs:
        handle_valid_paypal_ipn(sender=PayPalIPN, ipn_obj=ipn_obj)


@require_http_methods(["GET"])
def pricing(request):
    """Render pricing page with authenticated user's current subscription state."""
    current_plan = UserProfile.PLAN_FREE
    if request.user.is_authenticated:
        _reconcile_recent_paypal_ipn_for_user(request.user.id)
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        current_plan = profile.plan_tier

    return render(
        request,
        "pricing.html",
        {
            "current_plan": current_plan,
            "is_pro": current_plan == UserProfile.PLAN_PRO,
            "subscription_status": request.GET.get("subscription"),
        },
    )


@login_required(login_url=reverse_lazy("apps.downloads:index"))
@require_http_methods(["GET"])
def poll_subscription_status(request):
    """HTMX endpoint to refresh pricing page once subscription becomes Pro."""
    _reconcile_recent_paypal_ipn_for_user(request.user.id)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if profile.plan_tier == UserProfile.PLAN_PRO:
        response = HttpResponse("")
        response["HX-Redirect"] = f"{reverse('pricing')}?subscription=pro_activated"
        return response
    return HttpResponse(
        '<p class="text-xs text-slate-500 dark:text-slate-400">'
        "Waiting for PayPal confirmation...</p>"
    )


@login_required(login_url=reverse_lazy("apps.downloads:index"))
@require_http_methods(["POST"])
def start_pro_checkout(request):
    """Start Pro checkout and redirect to payment process page."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if profile.plan_tier == UserProfile.PLAN_PRO:
        return redirect(f"{reverse('pricing')}?subscription=already_pro")

    request.session[PENDING_PRO_CHECKOUT_SESSION_KEY] = True
    return redirect("apps.users:pro_checkout")


@login_required(login_url=reverse_lazy("apps.downloads:index"))
@require_http_methods(["GET"])
def pro_checkout(request):
    """Render payment process page for Pro subscription checkout."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if profile.plan_tier == UserProfile.PLAN_PRO:
        return redirect(f"{reverse('pricing')}?subscription=already_pro")

    has_pending_checkout = bool(request.session.get(PENDING_PRO_CHECKOUT_SESSION_KEY))
    if not has_pending_checkout:
        return redirect("pricing")

    paypal_receiver_email = getattr(settings, "PAYPAL_RECEIVER_EMAIL", "").strip()
    paypal_form = None
    if paypal_receiver_email:
        paypal_form = CustomPayPalPaymentsForm(
            user=request.user,
            request=request,
            initial={"amount": "9.00", "plan_name": "Pro Subscription"},
        )

    return render(
        request,
        "users/subscription_checkout.html",
        {
            "plan_name": "Pro",
            "price_label": "$9/month",
            "paypal_form": paypal_form,
            "paypal_configured": bool(paypal_receiver_email),
        },
    )


@login_required(login_url=reverse_lazy("apps.downloads:index"))
@require_http_methods(["GET"])
def paypal_subscription_return(request):
    """Redirect user after PayPal returns to the app."""
    _reconcile_recent_paypal_ipn_for_user(request.user.id)
    return redirect(f"{reverse('pricing')}?subscription=payment_submitted")


@login_required(login_url=reverse_lazy("apps.downloads:index"))
@require_http_methods(["GET"])
def paypal_subscription_cancel(request):
    """Handle cancel return from PayPal checkout."""
    request.session.pop(PENDING_PRO_CHECKOUT_SESSION_KEY, None)
    return redirect(f"{reverse('pricing')}?subscription=payment_canceled")


@login_required(login_url=reverse_lazy("apps.downloads:index"))
@require_http_methods(["POST"])
def activate_pro_subscription(request):
    """Finalize Pro activation after successful payment callback/confirmation."""
    has_pending_checkout = bool(request.session.get(PENDING_PRO_CHECKOUT_SESSION_KEY))
    if not has_pending_checkout:
        return redirect("pricing")

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    profile.apply_plan(UserProfile.PLAN_PRO)
    profile.save(update_fields=["plan_tier", "daily_limit", "max_resolution", "is_unlimited"])
    request.session.pop(PENDING_PRO_CHECKOUT_SESSION_KEY, None)
    return redirect(f"{reverse('pricing')}?subscription=pro_activated")


@login_required(login_url=reverse_lazy("apps.downloads:index"))
@require_http_methods(["POST"])
def cancel_pro_subscription(request):
    """Cancel Pro and downgrade the authenticated user to Free plan."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if profile.plan_tier != UserProfile.PLAN_PRO:
        return redirect(f"{reverse('pricing')}?subscription=already_free")

    profile.apply_plan(UserProfile.PLAN_FREE)
    profile.save(update_fields=["plan_tier", "daily_limit", "max_resolution", "is_unlimited"])
    request.session.pop(PENDING_PRO_CHECKOUT_SESSION_KEY, None)
    return redirect(f"{reverse('pricing')}?subscription=pro_canceled")


def _apply_subscription_event(profile: UserProfile, event_id: str, event_type: str, payload: dict) -> None:
    provider_customer_id = str(payload.get("provider_customer_id", "") or "")
    provider_subscription_id = str(payload.get("provider_subscription_id", "") or "")
    period_end_raw = payload.get("current_period_end")
    period_end = parse_datetime(period_end_raw) if isinstance(period_end_raw, str) else None

    if provider_customer_id:
        profile.provider_customer_id = provider_customer_id
    if provider_subscription_id:
        profile.provider_subscription_id = provider_subscription_id
    if period_end:
        profile.current_period_end = period_end
    profile.last_subscription_event_id = event_id

    if event_type in {"checkout.session.completed", "subscription.activated"}:
        profile.apply_plan(UserProfile.PLAN_PRO)
    elif event_type in {"customer.subscription.deleted", "subscription.canceled"}:
        profile.apply_plan(UserProfile.PLAN_FREE)
        profile.subscription_state = UserProfile.SUBSCRIPTION_CANCELED
    elif event_type in {"invoice.payment_failed", "subscription.payment_failed"}:
        profile.subscription_state = UserProfile.SUBSCRIPTION_PAST_DUE
    elif event_type in {"customer.subscription.updated", "subscription.updated"}:
        provider_status = str(payload.get("status", "")).lower().strip()
        if provider_status in {"active", "trialing"}:
            profile.subscription_state = UserProfile.SUBSCRIPTION_ACTIVE
        elif provider_status in {"past_due", "unpaid"}:
            profile.subscription_state = UserProfile.SUBSCRIPTION_PAST_DUE
        elif provider_status in {"canceled", "cancelled"}:
            profile.apply_plan(UserProfile.PLAN_FREE)
            profile.subscription_state = UserProfile.SUBSCRIPTION_CANCELED


@csrf_exempt
@require_http_methods(["POST"])
def provider_subscription_event(request):
    """Process provider webhook/callback events with idempotency."""
    expected_secret = settings.SUBSCRIPTION_WEBHOOK_SECRET
    received_secret = request.headers.get("X-Subscription-Webhook-Secret", "")
    if not expected_secret:
        return JsonResponse(
            {"ok": False, "error": "webhook_secret_not_configured"}, status=503
        )
    if received_secret != expected_secret:
        return JsonResponse({"ok": False, "error": "invalid_signature"}, status=403)

    try:
        body = request.body.decode("utf-8")
        payload = json.loads(body) if body else {}
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON payload")

    event_id = str(payload.get("id", "")).strip()
    event_type = str(payload.get("type", "")).strip()
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}

    if not event_id or not event_type:
        return HttpResponseBadRequest("Missing event id/type")

    event, created = SubscriptionEvent.objects.get_or_create(
        event_id=event_id,
        defaults={"event_type": event_type, "payload": payload},
    )
    if not created:
        if event.processed:
            return JsonResponse({"ok": True, "status": "duplicate"})
        event.payload = payload
        event.event_type = event_type
        event.processing_error = ""
        event.save(update_fields=["payload", "event_type", "processing_error", "updated_at"])

    user_id = data.get("user_id")
    if not user_id:
        event.processing_error = "missing user_id in event data"
        event.save(update_fields=["processing_error", "updated_at"])
        return HttpResponseBadRequest("Missing user_id in data")

    try:
        with transaction.atomic():
            profile = (
                UserProfile.objects.select_for_update()
                .select_related("user")
                .get(user_id=user_id)
            )
            _apply_subscription_event(profile, event_id, event_type, data)
            profile.save()
            event.profile = profile
            event.processed = True
            event.processing_error = ""
            event.save(update_fields=["profile", "processed", "processing_error", "updated_at"])
    except UserProfile.DoesNotExist:
        event.processing_error = "profile not found"
        event.save(update_fields=["processing_error", "updated_at"])
        return HttpResponseBadRequest("Profile not found")

    return JsonResponse({"ok": True, "status": "processed"})
