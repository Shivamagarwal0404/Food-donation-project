"""
FoodShare — Donations admin configuration.
"""
from django.contrib import admin
from .models import FoodCategory, FoodDonation, DonationRequest


@admin.register(FoodCategory)
class FoodCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "icon", "created_at")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "description")


class DonationRequestInline(admin.TabularInline):
    model = DonationRequest
    extra = 0
    readonly_fields = ("receiver", "requested_servings", "status", "created_at")


@admin.register(FoodDonation)
class FoodDonationAdmin(admin.ModelAdmin):
    inlines = [DonationRequestInline]
    list_display = (
        "title",
        "donor",
        "category",
        "quantity",
        "unit",
        "dietary_type",
        "status",
        "expiry_at",
        "created_at",
    )
    list_filter = ("status", "category", "dietary_type", "pickup_city")
    search_fields = ("title", "description", "donor__email", "pickup_address")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(DonationRequest)
class DonationRequestAdmin(admin.ModelAdmin):
    list_display = ("donation", "receiver", "requested_servings", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("donation__title", "receiver__email")

