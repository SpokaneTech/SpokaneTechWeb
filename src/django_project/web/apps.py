from django.apps import AppConfig


class App0Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "web"

    # def ready(self):
    #     import web.signals
