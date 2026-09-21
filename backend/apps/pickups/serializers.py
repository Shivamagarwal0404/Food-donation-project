"""
FoodShare — Pickups serializers.
"""
from rest_framework import serializers
from apps.users.serializers import UserSerializer
from apps.donations.serializers import FoodDonationSerializer
from .models import Pickup


class PickupSerializer(serializers.ModelSerializer):
    donation_details = FoodDonationSerializer(source="donation", read_only=True)
    volunteer_details = UserSerializer(source="volunteer", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Pickup
        fields = [
            "id",
            "donation",
            "donation_details",
            "volunteer",
            "volunteer_details",
            "pickup_location",
            "delivery_location",
            "scheduled_time",
            "status",
            "status_display",
            "notes",
            "picked_up_at",
            "delivered_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "donation",
            "volunteer",
            "status",
            "picked_up_at",
            "delivered_at",
            "created_at",
            "updated_at",
        ]

