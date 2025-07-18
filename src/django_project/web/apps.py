from django.apps import AppConfig


class App0Config(AppConfig):
    default_auto_field: str = "django.db.models.BigAutoField"
    name = "web"

    def ready(self) -> None:
        import web.signals  # noqa: F401
