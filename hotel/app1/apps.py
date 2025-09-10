from django.apps import AppConfig

class App1Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app1'
    verbose_name = "Hotel Suite"
    
    def ready(self):
        # Import signals to auto-create groups & permissions after migrations
        from . import signals  # noqa: F401
