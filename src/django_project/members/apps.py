from django.apps import AppConfig


class MembersConfig(AppConfig):
    default_auto_field: str = "django.db.models.BigAutoField"
    name = "members"

    def ready(self) -> None:
        import members.signals  # noqa: F401
