from django.contrib import admin
from .models import Stop, Route, Timetable

# Register your models here.

admin.site.register(Stop)
admin.site.register(Route)
admin.site.register(Timetable)
