from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "pos_service.core"
    label = "pos_core"
    verbose_name = "Core (base models, utils, services)"
