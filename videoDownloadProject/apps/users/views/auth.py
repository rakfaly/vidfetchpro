from django.contrib.auth import login, logout
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from apps.users.forms import LoginForm


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


@require_http_methods(["POST"])
def logout_user(request):
    """Log out the current user and return an HTMX-friendly response."""
    logout(request)
    if not request.htmx:
        return redirect("apps.downloads:index")

    response = HttpResponse('<div id="accountMenuRoot"></div>')
    response["HX-Redirect"] = reverse("apps.downloads:index")
    return response
