from datetime import date
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class RoomType(models.Model):
    name = models.CharField(max_length=128, null=False, blank=False, unique=True)

    def __str__(self):
        return self.name


class Room(models.Model):
    number = models.PositiveSmallIntegerField(null=False, blank=False, unique=True)
    type = models.ForeignKey(to=RoomType, on_delete=models.CASCADE)
    current_price = models.DecimalField(decimal_places=2, max_digits=9, validators=[MinValueValidator(Decimal('0.01'))])
    capacity = models.PositiveSmallIntegerField(null=False, blank=False, validators=[MinValueValidator(1)])
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Room №{self.number} | Type: {self.type.name}"

    def is_room_available_for(self, checkin_date: date, checkout_date: date) -> bool:
        from bookings.models import Booking

        def _find_intersection(c_in1: date, c_out1: date, c_in2: date, c_out2: date):
            latest_start = max(c_in1, c_in2)
            earliest_end = min(c_out1, c_out2)

            if latest_start <= earliest_end:
                intersection = (earliest_end - latest_start).days + 1
                return intersection
            else:
                return 0

        room_bookings = Booking.objects.filter(room=self)
        if room_bookings.exists():
            for booking in room_bookings:
                if booking.status == Booking.BOOKED:
                    if _find_intersection(checkin_date, checkout_date, booking.checkin_date, booking.checkout_date) > 1:
                        return False
        return True


class TelegramRoom:
    def __init__(self, room):
        self.number = room.number
        self.type = room.type.name
        self.price = room.current_price
        self.capacity = room.capacity
        self.description = room.description if room.description else "No description"

    def __str__(self):
        return f"Room №{self.number} | Type: {self.type} | Cost for one night: {self.price} | " \
               f"Capacity: {self.capacity} | Description: {self.description}"
