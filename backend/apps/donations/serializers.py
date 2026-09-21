"""
FoodShare — Donations serializers.
"""
from rest_framework import serializers
from django.utils import timezone
from apps.users.serializers import UserSerializer
from .models import FoodCategory, FoodDonation, DonationRequest, DonationStatus


class FoodCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodCategory
        fields = ["id", "name", "slug", "description", "icon", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class DonationRequestSerializer(serializers.ModelSerializer):
    receiver_details = UserSerializer(source="receiver", read_only=True)
    donation_title = serializers.CharField(source="donation.title", read_only=True)

    class Meta:
        model = DonationRequest
        fields = [
            "id",
            "donation",
            "donation_title",
            "receiver",
            "receiver_details",
            "requested_servings",
            "message",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "receiver", "status", "created_at", "updated_at"]

    def validate(self, attrs):
        donation = attrs.get("donation")
        request = self.context.get("request")
        user = request.user if request else None

        requested_servings = attrs.get("requested_servings")
        if requested_servings is not None:
            if requested_servings <= 0:
                raise serializers.ValidationError({"requested_servings": "Requested servings must be greater than zero."})
            if donation and requested_servings > donation.servings:
                raise serializers.ValidationError({
                    "requested_servings": f"Requested servings ({requested_servings}) cannot exceed available servings ({donation.servings})."
                })

        if donation.status not in [DonationStatus.AVAILABLE, DonationStatus.REQUESTED]:
            raise serializers.ValidationError(
                f"Donation '{donation.title}' is not open for requests (current status: {donation.status})."
            )
        if donation.is_expired or donation.expiry_at <= timezone.now() or donation.status == DonationStatus.EXPIRED:
            raise serializers.ValidationError("Cannot request an expired donation.")

        if user and user.is_authenticated:
            if donation.donor == user:
                raise serializers.ValidationError({"donation": "Donors cannot request their own donation."})

            existing_active = DonationRequest.objects.filter(
                donation=donation,
                receiver=user,
                status__in=[DonationRequest.RequestStatus.PENDING, DonationRequest.RequestStatus.ACCEPTED],
            ).exists()
            if existing_active:
                raise serializers.ValidationError({"donation": "You already have an active request for this donation."})

        return attrs


class FoodDonationSerializer(serializers.ModelSerializer):
    donor_details = UserSerializer(source="donor", read_only=True)
    category_details = FoodCategorySerializer(source="category", read_only=True)
    requests = DonationRequestSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = FoodDonation
        fields = [
            "id",
            "title",
            "description",
            "donor",
            "donor_details",
            "category",
            "other_food_item",
            "category_details",
            "dietary_type",
            "quantity",
            "unit",
            "servings",
            "prepared_at",
            "expiry_at",
            "pickup_address",
            "pickup_city",
            "pickup_contact_phone",
            "image",
            "status",
            "status_display",
            "special_instructions",
            "requests",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "donor", "status", "created_at", "updated_at"]

    def validate(self, attrs):
        if self.instance and self.instance.status not in [DonationStatus.AVAILABLE, DonationStatus.REQUESTED]:
            raise serializers.ValidationError(
                f"Donations cannot be modified once they have transitioned to {self.instance.status}."
            )

        quantity = attrs.get("quantity")
        if quantity is not None and quantity <= 0:
            raise serializers.ValidationError({"quantity": "Quantity must be strictly greater than 0."})

        servings = attrs.get("servings")
        if servings is not None and servings < 1:
            raise serializers.ValidationError({"servings": "Servings must be at least 1."})

        if "expiry_at" in attrs and attrs["expiry_at"] <= timezone.now():
            raise serializers.ValidationError({"expiry_at": "Expiration date/time must be strictly in the future."})

        # Category & other_food_item logic
        category = attrs.get("category")
        if category and not category.is_active:
            raise serializers.ValidationError({"category": "Selected category is inactive and cannot be chosen for donations."})
        if not category and self.instance:
            category = self.instance.category

        if category:
            is_other = category.slug == "other" or category.name.strip().lower() == "other"
            if is_other:
                other_food_item = attrs.get("other_food_item")
                if other_food_item is None and self.instance:
                    other_food_item = self.instance.other_food_item

                if other_food_item is None:
                    raise serializers.ValidationError({
                        "other_food_item": "Please specify the food item when selecting 'Other'."
                    })
                trimmed = str(other_food_item).strip()
                if not trimmed:
                    raise serializers.ValidationError({
                        "other_food_item": "Please specify the food item when selecting 'Other'."
                    })
                if len(trimmed) > 100:
                    raise serializers.ValidationError({
                        "other_food_item": "Specified food item cannot exceed 100 characters."
                    })
                attrs["other_food_item"] = trimmed
            else:
                attrs["other_food_item"] = None

        return attrs

    def update(self, instance, validated_data):
        # Strictly prevent modifying donor or arbitrary lifecycle status directly
        validated_data.pop("donor", None)
        validated_data.pop("status", None)
        return super().update(instance, validated_data)


class FoodDonationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodDonation
        fields = [
            "id",
            "category",
            "other_food_item",
            "title",
            "description",
            "dietary_type",
            "quantity",
            "unit",
            "servings",
            "prepared_at",
            "expiry_at",
            "pickup_address",
            "pickup_city",
            "pickup_contact_phone",
            "special_instructions",
            "status",
        ]
        read_only_fields = ["id", "status"]

    def validate(self, attrs):
        quantity = attrs.get("quantity")
        if quantity is not None and quantity <= 0:
            raise serializers.ValidationError({"quantity": "Quantity must be strictly greater than 0."})

        servings = attrs.get("servings")
        if servings is not None and servings < 1:
            raise serializers.ValidationError({"servings": "Servings must be at least 1."})

        expiry_at = attrs.get("expiry_at")
        if expiry_at and expiry_at <= timezone.now():
            raise serializers.ValidationError({"expiry_at": "Expiration date/time must be strictly in the future."})

        category = attrs.get("category")
        if category and not category.is_active:
            raise serializers.ValidationError({"category": "Selected category is inactive and cannot be chosen for new donations."})

        other_food_item = attrs.get("other_food_item")

        is_other = False
        if category:
            is_other = category.slug == "other" or category.name.strip().lower() == "other"

        if is_other:
            if other_food_item is None:
                raise serializers.ValidationError({
                    "other_food_item": "Please specify the food item when selecting 'Other'."
                })
            trimmed = str(other_food_item).strip()
            if not trimmed:
                raise serializers.ValidationError({
                    "other_food_item": "Please specify the food item when selecting 'Other'."
                })
            if len(trimmed) > 100:
                raise serializers.ValidationError({
                    "other_food_item": "Specified food item cannot exceed 100 characters."
                })
            attrs["other_food_item"] = trimmed
        else:
            attrs["other_food_item"] = None

        return attrs

