from apps.users.urls.account import urlpatterns as account_urlpatterns
from apps.users.urls.auth import urlpatterns as auth_urlpatterns
from apps.users.urls.security import urlpatterns as security_urlpatterns
from apps.users.urls.subscription import urlpatterns as subscription_urlpatterns

app_name = "apps.users"

urlpatterns = [
    *auth_urlpatterns,
    *account_urlpatterns,
    *security_urlpatterns,
    *subscription_urlpatterns,
]
