from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_http_methods
from django.views.generic import UpdateView

from apps.users.forms import CustomUserCreationForm, CustomUserUpdateForm


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


@login_required(login_url=reverse_lazy("apps.downloads:index"))
@require_http_methods(["GET"])
def update_account_success_toast(request):
    if not request.htmx:
        return redirect("profile")
    form = CustomUserUpdateForm(instance=request.user)
    return render(request, "users/update_account.html", {"form": form})


class AccountUpdateView(LoginRequiredMixin, UpdateView):
    form_class = CustomUserUpdateForm
    template_name = "users/update_account.html"
    success_url = reverse_lazy("profile")
    login_url = reverse_lazy("apps.downloads:index")

    def get_object(self, queryset: QuerySet | None = None):
        return self.request.user

    def form_valid(self, form):
        is_htmx = bool(self.request.headers.get("HX-Request"))

        # No-op submit: keep UX explicit and avoid unnecessary DB write.
        if not form.has_changed():
            if is_htmx:
                return render(
                    self.request,
                    "users/partials/update_account_success.html",
                    {
                        "update_success": False,
                        "update_message": "No changes detected.",
                    },
                )
            messages.info(self.request, "No changes detected.")
            return super().form_valid(form)

        self.object = form.save()

        if is_htmx:
            return render(
                self.request,
                "users/partials/update_account_success.html",
                {
                    "update_success": True,
                    "update_message": "Your profile was saved successfully.",
                },
            )

        messages.success(self.request, "Profile updated successfully.")
        return super().form_valid(form)
