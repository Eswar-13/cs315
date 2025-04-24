from django.db import models
from django.conf import settings
import uuid

class Booking(models.Model):
    booking_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    train = models.ForeignKey('search.Train', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    source = models.ForeignKey('search.Station', on_delete=models.CASCADE, related_name='departures')
    destination = models.ForeignKey('search.Station', on_delete=models.CASCADE, related_name='arrivals')
    no_of_passengers = models.PositiveIntegerField()
    passengers = models.ManyToManyField('Passenger', through='Seating')
    status = models.CharField(max_length=10,default='Pending')


    class Meta:
        pass

    def __str__(self):
        return f"{self.train.number} - {self.source} to {self.destination}"

class Passenger(models.Model):
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)

    class Meta:
        unique_together = ('user', 'name', 'age')

    def __str__(self):
        return f"{self.name} ({self.age})"

class Seating(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    passenger = models.ForeignKey(Passenger, on_delete=models.CASCADE)
    seat_no = models.CharField(max_length=10)

    class Meta:
        unique_together = ('booking', 'seat_no')

    def __str__(self):
        return f"Seat {self.seat_no} - {self.passenger.name}"
