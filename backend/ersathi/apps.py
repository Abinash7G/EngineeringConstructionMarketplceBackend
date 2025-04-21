from django.apps import AppConfig


class ErsathiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ersathi'
    
    def ready(self):
        import ersathi.signals