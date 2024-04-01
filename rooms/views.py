from datetime import date
from enum import Enum

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404

from bookings.views import is_room_available_for
from rooms.models import Room


class SortType(Enum):
    NONE = 0
    COST_ASCENDING = 1
    COST_DESCENDING = 2
    CAPACITY_ASCENDING = 3
    CAPACITY_DESCENDING = 4


def get_available_rooms(checkin_date: date, checkout_date: date, min_cost: float, max_cost: float, min_capacity: int,
                        sort_type: int) -> list:
    # Validate args
    _validate_args(checkin_date, checkout_date, min_cost, max_cost, min_capacity, sort_type)
    rooms_list = Room.objects.all()

    # Filter queryset by cost
    if min_cost is not None:
        rooms_list = rooms_list.filter(Q(current_price__gte=min_cost))
    if max_cost is not None:
        rooms_list = rooms_list.filter(Q(current_price__lte=max_cost))

    # Filter by capacity
    if min_capacity is not None:
        rooms_list = rooms_list.filter(Q(capacity__gte=min_capacity))

    # Filter by dates and create return list
    lst = []
    for r in rooms_list:
        if checkin_date is not None and checkout_date is not None:
            if is_room_available_for(r, checkin_date, checkout_date):
                dic = {
                    'number': r.number,
                    'type': r.type.name,
                    'price': r.current_price,
                    'capacity': r.capacity,
                    'description': r.description,
                }
                lst.append(dic)

    # Sort return list by given sort type
    sorted_lst = _sort_rooms(lst, SortType(sort_type))
    return sorted_lst


def _validate_args(checkin_date: date, checkout_date: date, min_cost: float, max_cost: float, min_capacity: int,
                   sort_type: int) -> None:
    # Validate cost
    if min_cost is not None and max_cost is not None:
        if max_cost < min_cost:
            raise ValidationError("Max cost can't be lower than min cost")

    # Validate given dates
    difference = checkout_date - checkin_date
    if difference.days < 1:
        raise ValidationError("Checkout date can't be earlier than 1 day after an check in")
    if checkin_date < date.today() or checkout_date < date.today():
        raise ValidationError("Can't book rooms for the past")

    # Validate sort type
    if not isinstance(sort_type, int):
        raise ValidationError("Sort type must be an integer")
    if sort_type not in {st.value for st in SortType}:
        raise ValidationError("Invalid sort type")


def _sort_rooms(lst: list, sort_type: SortType) -> list:
    # Sort return list by given sort type
    if sort_type == SortType.COST_ASCENDING:
        lst = sorted(lst, key=lambda x: x['price'])
    elif sort_type == SortType.COST_DESCENDING:
        lst = sorted(lst, key=lambda x: x['price'], reverse=True)
    elif sort_type == SortType.CAPACITY_ASCENDING:
        lst = sorted(lst, key=lambda x: x['capacity'])
    elif sort_type == SortType.CAPACITY_DESCENDING:
        lst = sorted(lst, key=lambda x: x['capacity'], reverse=True)
    return lst


def get_room_by_number(room_number: int) -> dict:
    # Retrieves a room by its number.
    room = get_object_or_404(Room, number=room_number)
    dic = {
        'number': room.number,
        'type': room.type.name,
        'price': room.current_price,
        'capacity': room.capacity,
        'description': room.description,
    }
    return dic
