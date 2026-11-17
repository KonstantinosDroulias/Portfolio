from django.apps import AppConfig


class KdConfig(AppConfig):
    name = "kd"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from . import signals  # noqa: F401
