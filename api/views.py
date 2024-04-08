from datetime import datetime

from django.core.exceptions import ValidationError
from rest_framework import filters, status, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as RestValidationError
from rest_framework.permissions import IsAdminUser, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from bookings.models import Booking
from rooms.models import Room
from rooms.serializers import BookingSerializer, RoomSerializer


def filter_by_price(request, rooms_queryset):
    min_price = request.query_params.get('min_price')
    max_price = request.query_params.get('max_price')
    if min_price:
        rooms_queryset = rooms_queryset.filter(current_price__gte=min_price)
    if max_price:
        rooms_queryset = rooms_queryset.filter(current_price__lte=max_price)
    return rooms_queryset


def filter_by_capacity(request, rooms_queryset):
    capacity = request.query_params.get('capacity')
    if capacity:
        rooms_queryset = rooms_queryset.filter(capacity__gte=capacity)
    return rooms_queryset


def filter_by_availability(request, rooms_queryset):
    checkin_date_str = request.query_params.get('checkin')
    checkout_date_str = request.query_params.get('checkout')
    if checkin_date_str and checkout_date_str:
        try:
            checkin_date = datetime.strptime(checkin_date_str, '%Y-%m-%d').date()
            checkout_date = datetime.strptime(checkout_date_str, '%Y-%m-%d').date()
        except ValueError:
            raise RestValidationError({'detail': "Invalid date format"})

        room_ids = [room.id for room in rooms_queryset if room.is_room_available_for(checkin_date, checkout_date)]

        rooms_queryset = rooms_queryset.filter(id__in=room_ids)
    return rooms_queryset


def sort_queryset(request, rooms_queryset):
    sort_by = request.query_params.get('sort_by')
    if sort_by:
        if sort_by == 'price_asc':
            rooms_queryset = rooms_queryset.order_by('current_price')
        elif sort_by == 'price_desc':
            rooms_queryset = rooms_queryset.order_by('-current_price')
        elif sort_by == 'capacity_asc':
            rooms_queryset = rooms_queryset.order_by('capacity')
        elif sort_by == 'capacity_desc':
            rooms_queryset = rooms_queryset.order_by('-capacity')
    return rooms_queryset


class RoomFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, rooms_queryset, view):
        rooms_queryset = filter_by_price(request, rooms_queryset)
        rooms_queryset = filter_by_capacity(request, rooms_queryset)
        rooms_queryset = filter_by_availability(request, rooms_queryset)
        rooms_queryset = sort_queryset(request, rooms_queryset)
        return rooms_queryset


class RoomModelViewSet(ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    filter_backends = [RoomFilter]

    def get_permissions(self):
        if self.action in ('create', 'update', 'destroy', 'partial_update'):
            self.permission_classes = (IsAdminUser,)
        return super(RoomModelViewSet, self).get_permissions()


class BookingModelViewSet(ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        if self.request.user.is_staff:
            return super(BookingModelViewSet, self).get_queryset()
        else:
            queryset = super(BookingModelViewSet, self).get_queryset()
            return queryset.filter(user=self.request.user)

    def get_permissions(self):
        if self.action in ('update', 'destroy',):
            self.permission_classes = (IsAdminUser,)
        return super(BookingModelViewSet, self).get_permissions()

    def create(self, request, *args, **kwargs):
        try:
            room_number = request.data['room_number']

            checkin_date = datetime.strptime(request.data['checkin_date'], '%d-%m-%Y').date()
            checkout_date = datetime.strptime(request.data['checkout_date'], '%d-%m-%Y').date()

            if not Room.objects.filter(number=room_number).exists():
                return Response({'room_number': 'There is no room with this number'},
                                status=status.HTTP_400_BAD_REQUEST)

            room = Room.objects.get(number=room_number)
            difference = checkout_date - checkin_date

            booking = Booking.objects.create(user=self.request.user, room=room, checkin_date=checkin_date,
                                             checkout_date=checkout_date, price=room.current_price * difference.days)

            serializer = self.get_serializer(booking)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError:
            return Response({'dates': "Date does not match the format %d-%m-%Y"}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({'dates': e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        booking.status = Booking.CANCELED
        booking.save(update_fields=['status'])
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
