from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_http_methods

from apps.users.models import UserProfile

PENDING_PRO_CHECKOUT_SESSION_KEY = "pending_pro_checkout"


@require_http_methods(["GET"])
def pricing(request):
    """Render pricing page with authenticated user's current subscription state."""
    current_plan = UserProfile.PLAN_FREE
    if request.user.is_authenticated:
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

    return render(
        request,
        "users/subscription_checkout.html",
        {"plan_name": "Pro", "price_label": "$9/month"},
    )


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
