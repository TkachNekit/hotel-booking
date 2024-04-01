from django.core.exceptions import ValidationError
from django.db.models.query import QuerySet

from bookings.models import Booking
from rooms.models import Room
from users.models import User
from datetime import date


def get_user_bookings(user: User) -> QuerySet:
    return Booking.objects.filter(user=user)


def cancel_user_booking(user: User, booking_id: int) -> None:
    # Validate booking id
    if not Booking.objects.filter(id=booking_id):
        raise ValidationError("Booking doesn't exist.")

    # Validate if it's user's booking
    booking = Booking.objects.get(id=booking_id)
    if booking.user != user:
        raise ValidationError("User can only cancel his bookings.")

    # Cancel booking
    booking.status = Booking.CANCELED
    booking.save()


def book_room(user: User, room_number: int, checkin_date: date, checkout_date: date) -> None:
    # Validate room number
    if not Room.objects.filter(number=room_number).exists():
        raise ValidationError("Room with given room number doesn't exist.")
    room = Room.objects.get(number=room_number)

    # Validate given dates
    difference = checkout_date - checkin_date
    if difference.days < 1:
        raise ValidationError("Checkout date can't be earlier than 1 day after an check in.")
    if checkin_date < date.today() or checkout_date < date.today():
        raise ValidationError("Can't book rooms for the past")

    # Check if room is free for this dates or booking for this room is canceled
    if not is_room_available_for(room, checkin_date, checkout_date):
        raise ValidationError("Room unavailable for this dates")

    # creates booking
    booking = Booking.objects.create(user=user, room=room, checkin_date=checkin_date, checkout_date=checkout_date,
                                     price=room.current_price * difference.days)


def is_room_available_for(room: Room, checkin_date: date, checkout_date: date) -> bool:
    def _find_intersection(c_in1: date, c_out1: date, c_in2: date, c_out2: date):
        latest_start = max(c_in1, c_in2)
        earliest_end = min(c_out1, c_out2)

        if latest_start <= earliest_end:
            intersection = (earliest_end - latest_start).days + 1
            return intersection
        else:
            return 0

    room_bookings = Booking.objects.filter(room=room)
    if room_bookings.exists():
        for booking in room_bookings:
            if booking.status == Booking.BOOKED:
                if _find_intersection(checkin_date, checkout_date, booking.checkin_date, booking.checkout_date) > 1:
                    return False
    return True
