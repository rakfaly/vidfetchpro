from decimal import Decimal
from uuid import uuid4

from django.conf import settings
from django.urls import reverse
from paypal.standard.forms import PayPalPaymentsForm


class CustomPayPalPaymentsForm(PayPalPaymentsForm):
    """Preconfigured PayPal subscription form for Pro checkout."""

    def __init__(self, *args, user, request, **kwargs):
        initial = kwargs.pop("initial", {}) or {}
        amount = Decimal(str(initial.pop("amount", "9.00")))
        plan_name = initial.pop("plan_name", "Pro Subscription")
        invoice = initial.pop("invoice", f"sub-{user.id}-{uuid4()}")

        initial.update(
            {
                "cmd": "_xclick-subscriptions",
                "business": getattr(settings, "PAYPAL_RECEIVER_EMAIL", ""),
                "a3": f"{amount:.2f}",
                "p3": 1,
                "t3": "M",
                "src": "1",
                "sra": "1",
                "no_note": "1",
                "item_name": plan_name,
                "invoice": invoice,
                "custom": str(user.id),
                "notify_url": request.build_absolute_uri(
                    reverse("apps.users:paypal-ipn")
                ),
                "return": request.build_absolute_uri(
                    reverse("apps.users:paypal_subscription_return")
                ),
                "cancel_return": request.build_absolute_uri(
                    reverse("apps.users:paypal_subscription_cancel")
                ),
            }
        )

        kwargs["initial"] = initial
        kwargs.setdefault("button_type", "subscribe")
        super().__init__(*args, **kwargs)
