from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods

from apps.users.forms import CustomPasswordChangeForm


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
