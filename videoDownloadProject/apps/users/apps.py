from django.apps import AppConfig


class UsersConfig(AppConfig):
    """App configuration for user-related models and views."""

    name = "apps.users"

    def ready(self) -> None:
        from apps.users import signals

