"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from apps.downloads.views import DownloadView
from apps.users.views import AccountUpdateView, pricing

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", DownloadView.as_view(), name="index"),
    path("downloads/", include("apps.downloads.urls")),
    path("history/", include("apps.history.urls")),
    path("users/", include("apps.users.urls")),
    path(
        "terms/", TemplateView.as_view(template_name="legal/terms.html"), name="terms"
    ),
    path(
        "privacy/",
        TemplateView.as_view(template_name="legal/privacy.html"),
        name="privacy",
    ),
    path("help/", TemplateView.as_view(template_name="help.html"), name="help"),
    path(
        "features/",
        TemplateView.as_view(template_name="features.html"),
        name="features",
    ),
    path(
        "formats/", TemplateView.as_view(template_name="formats.html"), name="formats"
    ),
    path("pricing/", pricing, name="pricing"),
    path(
        "profile/",
        AccountUpdateView.as_view(
            template_name="users/profile.html",
            success_url="/profile/",
        ),
        name="profile",
    ),
]

if settings.DEBUG:
    # Include django_browser_reload URLs only in DEBUG mode
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]
