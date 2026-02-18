from django.urls import path

from . import views

app_name = "apps.users"

urlpatterns = [
    path("login/", views.login_popover, name="login_popover"),
    path("account/menu/", views.account_menu, name="account_menu"),
    path("account/logout/", views.logout_user, name="logout_user"),
    path("account/create", views.create_account, name="create_account"),
    path(
        "account/create/success-toast",
        views.create_account_success_toast,
        name="create_account_success_toast",
    ),
    path(
        "account/create/success-toast/close",
        views.close_create_account_success_toast,
        name="create_account_success_toast_close",
    ),
    path("account/update", views.AccountUpdateView.as_view(), name="update_account"),
    path("account/change-password", views.change_password, name="change_password"),
    path(
        "account/change-password/close",
        views.close_change_password_panel,
        name="change_password_close",
    ),
]
