from django.apps import AppConfig


class AAuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'a_auth'

    def ready(self):
        import a_auth.signals
