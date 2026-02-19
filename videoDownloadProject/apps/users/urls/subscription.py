from django.urls import include, path

from apps.users.views import (
    activate_pro_subscription,
    cancel_pro_subscription,
    paypal_subscription_cancel,
    paypal_subscription_return,
    poll_subscription_status,
    provider_subscription_event,
    pro_checkout,
    start_pro_checkout,
)

urlpatterns = [
    path(
        "subscription/pro/checkout/start",
        start_pro_checkout,
        name="start_pro_checkout",
    ),
    path("subscription/pro/checkout", pro_checkout, name="pro_checkout"),
    path(
        "subscription/pro/status",
        poll_subscription_status,
        name="poll_subscription_status",
    ),
    path(
        "subscription/paypal/return",
        paypal_subscription_return,
        name="paypal_subscription_return",
    ),
    path(
        "subscription/paypal/cancel",
        paypal_subscription_cancel,
        name="paypal_subscription_cancel",
    ),
    path("subscription/paypal/", include("paypal.standard.ipn.urls")),
    path(
        "subscription/pro/activate",
        activate_pro_subscription,
        name="activate_pro_subscription",
    ),
    path(
        "subscription/pro/cancel",
        cancel_pro_subscription,
        name="cancel_pro_subscription",
    ),
    path(
        "subscription/provider/event",
        provider_subscription_event,
        name="provider_subscription_event",
    ),
]
