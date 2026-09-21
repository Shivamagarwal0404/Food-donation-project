"""
FoodShare — Users admin configuration.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, DonorProfile, NGOProfile, VolunteerProfile, Address


class DonorProfileInline(admin.StackedInline):
    model = DonorProfile
    can_delete = False
    extra = 0


class NGOProfileInline(admin.StackedInline):
    model = NGOProfile
    can_delete = False
    extra = 0


class VolunteerProfileInline(admin.StackedInline):
    model = VolunteerProfile
    can_delete = False
    extra = 0


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [DonorProfileInline, NGOProfileInline, VolunteerProfileInline]
    list_display = ("email", "first_name", "last_name", "role", "is_active", "is_staff", "created_at")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("email", "first_name", "last_name", "phone_number")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at", "last_login")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "phone_number")}),
        (_("Role & Permissions"), {"fields": ("role", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "role", "is_active", "is_staff"),
            },
        ),
    )


@admin.register(DonorProfile)
class DonorProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "organization_name", "donor_type", "fssai_license", "created_at")
    list_filter = ("donor_type",)
    search_fields = ("user__email", "organization_name")


@admin.register(NGOProfile)
class NGOProfileAdmin(admin.ModelAdmin):
    list_display = ("organization_name", "user", "registration_number", "is_verified", "created_at")
    list_filter = ("is_verified",)
    search_fields = ("organization_name", "registration_number", "user__email")
    actions = ["verify_ngos"]

    @admin.action(description="Verify selected NGOs")
    def verify_ngos(self, request, queryset):
        queryset.update(is_verified=True)


@admin.register(VolunteerProfile)
class VolunteerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "vehicle_type", "is_available", "deliveries_completed", "created_at")
    list_filter = ("vehicle_type", "is_available")
    search_fields = ("user__email", "user__first_name", "user__last_name")


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("contact_person", "user", "label", "city", "state", "pincode", "is_default")
    list_filter = ("label", "state", "is_default")
    search_fields = ("contact_person", "contact_phone", "city", "user__email")

