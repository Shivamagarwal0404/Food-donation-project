"""
FoodShare — Pickups admin configuration.
"""
from django.contrib import admin
from .models import Pickup


@admin.register(Pickup)
class PickupAdmin(admin.ModelAdmin):
    list_display = (
        "donation",
        "volunteer",
        "status",
        "scheduled_time",
        "picked_up_at",
        "delivered_at",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("donation__title", "volunteer__email", "pickup_location", "delivery_location")
    readonly_fields = ("picked_up_at", "delivered_at", "created_at", "updated_at")

