from django.contrib import admin
from .models import Booking
from .models import Passenger
from .models import Seating

# Register your models here.
admin.site.register(Booking)
admin.site.register(Passenger)
admin.site.register(Seating)