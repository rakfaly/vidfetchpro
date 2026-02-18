from django.urls import path

from apps.users.views import change_password, close_change_password_panel

urlpatterns = [
    path("account/change-password", change_password, name="change_password"),
    path(
        "account/change-password/close",
        close_change_password_panel,
        name="change_password_close",
    ),
]
