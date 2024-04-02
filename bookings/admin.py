from django.contrib import admin, messages

from bookings.models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'room', 'checkin_date', 'checkout_date')
    fields = ('id', 'user', 'room', ('checkin_date', 'checkout_date'), 'booking_date', 'status', 'price')
    readonly_fields = ('booking_date', 'id')

    def save_model(self, request, obj, form, change):
        """Override save method so checkout_date should be later than checkin date"""
        try:
            if obj.checkout_date and obj.checkout_date <= obj.checkin_date:
                raise ValueError("Checkout date must be greater than the checkin date.")
            else:
                super().save_model(request, obj, form, change)
        except ValueError as e:
            messages.set_level(request, messages.ERROR)
            messages.error(request, str(e))
