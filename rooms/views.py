from datetime import date
from typing import Literal

from rooms.models import Room

SORT = Literal[None, 'min_to_max', 'max_to_min', 'capacity']


def get_rooms(checkin_date: date, checkout_date: date, min_cost: float, max_cost: float, min_capacity: int,
              sort_type: SORT) -> list:
    pass


def get_room_by_number(room_number: int) -> Room:
    pass
