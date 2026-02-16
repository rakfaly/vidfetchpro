from django.urls import path

from . import views

app_name = "apps.users"

urlpatterns = [
    path("login-popover/", views.login_popover, name="login_popover"),
    path("account-menu/", views.account_menu, name="account_menu"),
    path("logout-user/", views.logout_user, name="logout_user"),
    path("create-account/", views.create_account, name="create_account"),
]
