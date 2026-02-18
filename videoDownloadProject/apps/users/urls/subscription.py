from django.urls import path

from apps.users.views import (
    activate_pro_subscription,
    cancel_pro_subscription,
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
        "subscription/pro/activate",
        activate_pro_subscription,
        name="activate_pro_subscription",
    ),
    path(
        "subscription/pro/cancel",
        cancel_pro_subscription,
        name="cancel_pro_subscription",
    ),
]
