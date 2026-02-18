from django.urls import path

from apps.users.views import (
    AccountUpdateView,
    close_create_account_success_toast,
    create_account,
    create_account_success_toast,
)
from apps.users.views.account import update_account_success_toast

urlpatterns = [
    path("account/create", create_account, name="create_account"),
    path(
        "account/create/success-toast",
        create_account_success_toast,
        name="create_account_success_toast",
    ),
    path(
        "account/create/success-toast/close",
        close_create_account_success_toast,
        name="create_account_success_toast_close",
    ),
    path("account/update", AccountUpdateView.as_view(), name="update_account"),
    path(
        "account/update/success",
        update_account_success_toast,
        name="update_account_success_toast",
    ),
]
