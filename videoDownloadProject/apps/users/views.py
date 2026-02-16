from django.contrib import messages
from django.contrib.auth import login, logout
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import CustomUserCreationForm, LoginForm


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
            return redirect("apps.downloads:index")

    return render(request, "users/create_account.html", {"form": form})


@require_http_methods(["POST"])
def logout_user(request):
    logout(request)
    if not request.htmx:
        return HttpResponse("")

    # Create an empty div
    response = HttpResponse('<div id="accountMenuRoot"></div>')
    # Refresh at the same page
    response["HX-Redirect"] = request.headers.get("HX-Current-URL", "/")
    return response
