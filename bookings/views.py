from users.models import User
from datetime import date


def get_user_bookings(user: User) -> list:
    pass


def cancel_user_booking(user: User, booking_id: int) -> None:
    pass


def book_room(user: User, room_number: int, checkin_date: date, checkout_date: date) -> None:
    pass
