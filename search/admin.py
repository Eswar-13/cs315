from django.contrib import admin
from .models import Station
from .models import Schedule
from .models import Train


admin.site.register(Station)
admin.site.register(Schedule)
admin.site.register(Train)

