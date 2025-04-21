from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('start/', views.booking_start, name='start'),
    path('passengers/', views.booking_passengers, name='passengers'),
    path('confirm/', views.booking_confirm, name='confirm'),
    path('history/', views.booking_history, name='history'),
]
