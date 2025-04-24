from django.apps import AppConfig
import os

class SearchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'search'
    def ready(self):
        # Ensures graph loads once per server process
        if not os.environ.get('RUN_MAIN') or os.environ.get('RUN_MAIN') == 'true':
            from .services.path_finder import RouteService
            RouteService()  # Loads the graph into memory