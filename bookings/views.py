from datetime import date

from django.core.exceptions import ValidationError

from bookings.models import Booking, TelegramBooking
from rooms.models import Room
from users.models import TelegramUser, User


def get_user_active_bookings(user: TelegramUser) -> list:
    user = User.objects.get(username=user.username)
    return [TelegramBooking(booking) for booking in Booking.objects.filter(user=user) if
            booking.status == Booking.BOOKED]


def cancel_user_booking(user: TelegramUser, booking_id: int) -> None:
    # Validate booking id
    if not Booking.objects.filter(id=booking_id):
        raise ValidationError("Booking doesn't exist.")

    # Validate if it's user's booking
    booking = Booking.objects.get(id=booking_id)

    user = User.objects.get(username=user.username)
    if booking.user != user:
        raise ValidationError("User can only cancel his bookings.")

    # Cancel booking
    booking.status = Booking.CANCELED
    booking.save()


def book_room(user: TelegramUser, room_number: int, checkin_date: date, checkout_date: date) -> None:
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

    # Check if room is available for these dates or booking for this room is canceled
    if not room.is_room_available_for(checkin_date, checkout_date):
        raise ValidationError("Room unavailable for these dates")

    # creates booking
    user = User.objects.get(username=user.username)
    Booking.objects.create(user=user, room=room, checkin_date=checkin_date, checkout_date=checkout_date,
                           price=room.current_price * difference.days)


