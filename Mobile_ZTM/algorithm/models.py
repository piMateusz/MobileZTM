from django.db import models
from django.utils import timezone
# Create your models here.


class Stop(models.Model):
    stopId = models.IntegerField()
    stopDesc = models.CharField(max_length=100, default="")
    stopLat = models.FloatField()
    stopLon = models.FloatField()
    onDemand = models.BooleanField(blank=True, null=True)
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f'stop name: {self.stopDesc}'


class Route(models.Model):
    routeId = models.IntegerField()     # wewnętrzny identyfikator linii unikalny w skali Trójmiasta; liczba całkowita
    routeShortName = models.CharField(max_length=10)    # numer linii używany m.in. na przystankach; ciąg znaków
    routeLongName = models.CharField(max_length=200)    # opis linii najczęściej składający się z nazw przystanków krańcowych; ciąg znaków.
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"route number: {self.routeShortName}, route name: {self.routeLongName}"


class Timetable(models.Model):
    stop = models.ForeignKey(Stop, on_delete=models.CASCADE)
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    stopSequence = models.IntegerField()
    arrivalTime = models.DateTimeField()
    date = models.DateField()
    busServiceName = models.CharField(max_length=10)
    order = models.IntegerField()

    def __str__(self):
        return f"date: {self.date}, {str(self.stop)}, {str(self.route)}"
