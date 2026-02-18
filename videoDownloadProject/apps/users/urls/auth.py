from django.urls import path

from apps.users.views import account_menu, login_popover, logout_user

urlpatterns = [
    path("login/", login_popover, name="login_popover"),
    path("account/menu/", account_menu, name="account_menu"),
    path("account/logout/", logout_user, name="logout_user"),
]
