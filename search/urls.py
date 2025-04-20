# search/urls.py
from django.urls import path
from .views import route_search

app_name = 'search'  # Namespace for URL reversing

urlpatterns = [
    path('', route_search, name='route_search'),
]
