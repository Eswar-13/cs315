from django.db import models


class Station(models.Model):
    name = models.CharField(max_length=100, primary_key=True)
    state = models.CharField(max_length=50)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

class Train(models.Model):
    number = models.CharField(max_length=20)
    origin_date = models.DateField()
    end_date = models.DateField()
    seats_available = models.IntegerField()

    class Meta:
        unique_together = [('number', 'origin_date')]
        indexes = [
            models.Index(fields=['number']),
            models.Index(fields=['origin_date']),
        ]

class Schedule(models.Model):
    train = models.ForeignKey(Train, on_delete=models.CASCADE, related_name='schedules')
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    arrival_time = models.DateTimeField(null=True, blank=True)
    departure_time = models.DateTimeField(null=True, blank=True)
    distance_from_src = models.DecimalField(max_digits=8, decimal_places=2)
    stop_order = models.PositiveIntegerField()

    class Meta:
        unique_together = [('train', 'station'), ('train', 'stop_order')]
        ordering = ['stop_order']
