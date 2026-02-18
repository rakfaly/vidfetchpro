from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_http_methods
from django.views.generic import UpdateView

from .forms import (
    CustomPasswordChangeForm,
    CustomUserCreationForm,
    CustomUserUpdateForm,
    LoginForm,
)


@require_http_methods(["GET", "POST"])
def login_popover(request):
    """
    Return the login popover fragment for HTMX.

    GET parameters:
    - close=1: return the closed/hidden popover wrapper.
    """
    if not request.htmx:
        return HttpResponse("")
    if request.GET.get("close") == "1":
        return HttpResponse('<div id="loginModalRoot"></div>')

    form = LoginForm(data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        response = HttpResponse("")
        response["HX-Redirect"] = request.headers.get("HX-Current-URL", "/")
        return response

    return render(request, "users/login_popover.html", {"form": form})


def account_menu(request):
    """
    Return the account menu modal for authenticated users.

    GET parameters:
    - close=1: return the closed/hidden wrapper.
    """
    if not request.htmx or not request.user.is_authenticated:
        return HttpResponse("")
    if request.GET.get("close") == "1":
        return HttpResponse('<div id="accountMenuRoot"></div>')
    return render(request, "users/account_menu.html")


def create_account(request):
    """Create a new user account and log them in if the form is valid."""
    if request.user.is_authenticated:
        return redirect("apps.downloads:index")

    form = CustomUserCreationForm(request.POST or None)
    if request.method == "POST":
        is_checked = "checkbox_policy_terms" in request.POST
        if not is_checked:
            messages.warning(request, "Please accept Terms and Privacy Policy.")
        if is_checked and form.is_valid():
            user = form.save()
            login(request, user)
            request.session["show_create_account_success_toast"] = True
            if request.htmx:
                response = HttpResponse("")
                response["HX-Redirect"] = reverse("apps.downloads:index")
                return response
            return redirect("apps.downloads:index")

    return render(request, "users/create_account.html", {"form": form})


@require_http_methods(["GET"])
def create_account_success_toast(request):
    if not request.htmx:
        return HttpResponse("")
    return render(request, "users/partials/create_account_success.html")


@require_http_methods(["GET"])
def close_create_account_success_toast(request):
    if not request.htmx:
        return HttpResponse("")
    return HttpResponse("")


class AccountUpdateView(LoginRequiredMixin, UpdateView):
    form_class = CustomUserUpdateForm
    template_name = "users/update_account.html"
    success_url = reverse_lazy("profile")
    login_url = reverse_lazy("apps.downloads:index")

    def get_object(self, queryset: QuerySet | None = None):
        return self.request.user


@login_required(login_url=reverse_lazy("apps.downloads:index"))
@require_http_methods(["GET", "POST"])
def change_password(request):
    form = CustomPasswordChangeForm(user=request.user, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        if request.htmx:
            return render(request, "users/partials/change_password_success.html")
        messages.success(request, "Password updated successfully.")
        return redirect("profile")

    template_name = (
        "users/partials/change_password_panel.html"
        if request.htmx
        else "users/change_password.html"
    )
    return render(request, template_name, {"form": form})


@login_required(login_url=reverse_lazy("apps.downloads:index"))
@require_http_methods(["GET"])
def close_change_password_panel(request):
    if not request.htmx:
        return redirect("profile")
    return HttpResponse("")


@require_http_methods(["POST"])
def logout_user(request):
    """Log out the current user and return an HTMX-friendly response."""
    logout(request)
    if not request.htmx:
        return redirect("apps.downloads:index")

    # Create an empty div
    response = HttpResponse('<div id="accountMenuRoot"></div>')
    # Redirect to a public route after logout.
    response["HX-Redirect"] = reverse("apps.downloads:index")
    return response
