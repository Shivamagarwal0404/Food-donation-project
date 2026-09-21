"""
FoodShare — Donations views.
Handles food listing, donor submissions, NGO claim requests, donor approvals, and cancellations.
"""
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone

from apps.users.models import UserRole
from apps.users.permissions import (
    IsPlatformAdmin,
    IsDonor,
    IsNGOReceiver,
    IsVerifiedNGO,
    is_admin_or_staff,
)
from .models import FoodCategory, FoodDonation, DonationRequest, DonationStatus
from .serializers import (
    FoodCategorySerializer,
    FoodDonationSerializer,
    FoodDonationCreateSerializer,
    DonationRequestSerializer,
)


class FoodCategoryListCreateView(generics.ListCreateAPIView):
    """
    GET: List all active food categories (public).
    POST: Platform administrator creates a food category.
    """

    queryset = FoodCategory.objects.all()
    serializer_class = FoodCategorySerializer

    def get_queryset(self):
        if self.request.user and is_admin_or_staff(self.request.user):
            return FoodCategory.objects.all()
        return FoodCategory.objects.filter(is_active=True)

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsPlatformAdmin()]
        return [permissions.AllowAny()]


class FoodCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve food category details (public).
    PUT / PATCH / DELETE: Platform administrator manages category.
    """

    queryset = FoodCategory.objects.all()
    serializer_class = FoodCategorySerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsPlatformAdmin()]
        return [permissions.AllowAny()]


class FoodDonationListCreateView(generics.ListCreateAPIView):
    """
    GET: List active donations (public or filtered).
    POST: Authenticated donor creates a food donation.
    """

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "category", "dietary_type", "pickup_city"]
    search_fields = ["title", "description", "pickup_city"]
    ordering_fields = ["created_at", "expiry_at", "quantity"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = FoodDonation.objects.select_related("donor", "category").prefetch_related("requests")
        status_param = self.request.query_params.get("status")
        if not status_param:
            queryset = queryset.filter(status__in=[DonationStatus.AVAILABLE, DonationStatus.REQUESTED])
        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return FoodDonationCreateSerializer
        return FoodDonationSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        user = self.request.user
        if not (user.is_donor or is_admin_or_staff(user)):
            raise PermissionDenied("Only registered food donors can create food donations.")
        serializer.save(donor=user)


class FoodDonationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or cancel a specific food donation."""

    queryset = FoodDonation.objects.select_related("donor", "category").prefetch_related("requests")
    serializer_class = FoodDonationSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if request.method in ["PUT", "PATCH", "DELETE"]:
            if obj.donor != request.user and not is_admin_or_staff(request.user):
                raise PermissionDenied("You can only modify or delete your own food donations.")

    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.status not in [DonationStatus.AVAILABLE, DonationStatus.REQUESTED]:
            raise PermissionDenied(
                f"Cannot modify donation once it has reached {instance.status} status."
            )
        serializer.save()

    def perform_destroy(self, instance):
        if instance.donor != self.request.user and not is_admin_or_staff(self.request.user):
            raise PermissionDenied("You can only cancel your own food donations.")
        cancellable_statuses = [
            DonationStatus.AVAILABLE,
            DonationStatus.REQUESTED,
            DonationStatus.ACCEPTED,
            DonationStatus.PICKUP_ASSIGNED,
        ]
        if instance.status not in cancellable_statuses:
            if instance.status == DonationStatus.PICKED_UP:
                raise PermissionDenied("Cannot cancel a donation that has already been picked up.")
            raise PermissionDenied(f"Cannot cancel a donation that is already {instance.status}.")
        with transaction.atomic():
            instance.transition_to(DonationStatus.CANCELLED)
            # Cancel any pending requests
            instance.requests.filter(status=DonationRequest.RequestStatus.PENDING).update(
                status=DonationRequest.RequestStatus.CANCELLED
            )
            from apps.pickups.models import Pickup, PickupStatus
            try:
                pickup = instance.pickup
                if pickup.status not in [PickupStatus.COMPLETED, PickupStatus.CANCELLED]:
                    pickup.transition_to(PickupStatus.CANCELLED)
            except Pickup.DoesNotExist:
                pass


class DonationCancelView(APIView):
    """Explicit cancellation endpoint for donors and platform administrators."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        donation = get_object_or_404(FoodDonation, pk=pk)
        if donation.donor != request.user and not is_admin_or_staff(request.user):
            raise PermissionDenied("You can only cancel your own food donations.")

        cancellable_statuses = [
            DonationStatus.AVAILABLE,
            DonationStatus.REQUESTED,
            DonationStatus.ACCEPTED,
            DonationStatus.PICKUP_ASSIGNED,
        ]
        if donation.status not in cancellable_statuses:
            if donation.status == DonationStatus.PICKED_UP:
                error_msg = "Cannot cancel a donation that has already been picked up."
            elif donation.status in [DonationStatus.DELIVERED, DonationStatus.COMPLETED]:
                error_msg = f"Cannot cancel a donation that is already {donation.status}."
            elif donation.status == DonationStatus.CANCELLED:
                error_msg = "Donation is already cancelled."
            elif donation.status == DonationStatus.EXPIRED:
                error_msg = "Cannot cancel an expired donation."
            else:
                error_msg = f"Cannot cancel donation with status {donation.status}."
            return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            donation.transition_to(DonationStatus.CANCELLED)
            donation.requests.filter(status=DonationRequest.RequestStatus.PENDING).update(
                status=DonationRequest.RequestStatus.CANCELLED
            )
            from apps.pickups.models import Pickup, PickupStatus
            try:
                pickup = donation.pickup
                if pickup.status not in [PickupStatus.COMPLETED, PickupStatus.CANCELLED]:
                    pickup.transition_to(PickupStatus.CANCELLED)
            except Pickup.DoesNotExist:
                pass

        return Response(
            {"message": f"Donation '{donation.title}' has been cancelled.", "status": donation.status},
            status=status.HTTP_200_OK,
        )


class DonationRequestCreateView(generics.CreateAPIView):
    """
    NGO / Receiver submits a claim request for an available food donation.
    """

    queryset = DonationRequest.objects.all()
    serializer_class = DonationRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        if not (user.is_ngo or is_admin_or_staff(user)):
            raise PermissionDenied("Only registered NGOs and community receivers can request food donations.")

        if user.is_ngo and not is_admin_or_staff(user):
            ngo_profile = getattr(user, "ngo_profile", None)
            if not ngo_profile or not ngo_profile.is_verified:
                raise PermissionDenied("Only verified NGOs can request food donations. Platform admin verification is required.")

        donation = serializer.validated_data.get("donation")

        with transaction.atomic():
            serializer.save(receiver=user, donation=donation)
            if donation.status == DonationStatus.AVAILABLE:
                donation.transition_to(DonationStatus.REQUESTED)


class DonationRequestAcceptView(APIView):
    """
    Donor accepts a specific NGO's claim request.
    Transitions donation to ACCEPTED, rejects other pending requests, and creates a Pickup record.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        with transaction.atomic():
            req = (
                DonationRequest.objects.select_for_update()
                .select_related("donation", "receiver")
                .filter(pk=pk)
                .first()
            )
            if not req:
                return Response({"error": "Donation request not found."}, status=status.HTTP_404_NOT_FOUND)

            donation = FoodDonation.objects.select_for_update().get(pk=req.donation_id)

            if donation.donor != request.user and not is_admin_or_staff(request.user):
                raise PermissionDenied("Only the donation owner can accept claim requests.")

            if req.status != DonationRequest.RequestStatus.PENDING:
                return Response(
                    {"error": f"Cannot accept request with status '{req.status}'. Only PENDING requests can be accepted."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if donation.status not in [DonationStatus.AVAILABLE, DonationStatus.REQUESTED]:
                return Response(
                    {"error": f"Cannot accept claim for donation with status {donation.status}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Mark this request as accepted
            req.status = DonationRequest.RequestStatus.ACCEPTED
            req.save(update_fields=["status", "updated_at"])

            # Reject other pending requests for this donation
            DonationRequest.objects.filter(
                donation=donation,
                status=DonationRequest.RequestStatus.PENDING,
            ).exclude(pk=req.pk).update(status=DonationRequest.RequestStatus.REJECTED)

            # Transition donation status
            donation.transition_to(DonationStatus.ACCEPTED)

            # Auto-create Pickup record in apps.pickups
            from apps.pickups.models import Pickup, PickupStatus
            Pickup.objects.get_or_create(
                donation=donation,
                defaults={
                    "pickup_location": donation.pickup_address,
                    "status": PickupStatus.PENDING,
                },
            )

        return Response(
            {
                "message": f"Claim accepted for {req.receiver.full_name}. Status moved to ACCEPTED.",
                "donation_id": donation.id,
                "status": donation.status,
            },
            status=status.HTTP_200_OK,
        )


class DonationRequestRejectView(APIView):
    """
    Donor rejects a specific NGO's claim request.
    If no other pending requests exist, donation status reverts to AVAILABLE.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        req = get_object_or_404(DonationRequest.objects.select_related("donation", "receiver"), pk=pk)
        donation = req.donation

        if donation.donor != request.user and not is_admin_or_staff(request.user):
            raise PermissionDenied("Only the donation owner can reject claim requests.")

        if req.status != DonationRequest.RequestStatus.PENDING:
            return Response(
                {"error": f"Cannot reject request that is currently '{req.status}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            req.status = DonationRequest.RequestStatus.REJECTED
            req.save(update_fields=["status", "updated_at"])

            # If no pending requests remain on this donation, revert donation to AVAILABLE
            has_pending = DonationRequest.objects.filter(
                donation=donation,
                status=DonationRequest.RequestStatus.PENDING,
            ).exists()
            if not has_pending and donation.status == DonationStatus.REQUESTED:
                donation.transition_to(DonationStatus.AVAILABLE)

        return Response(
            {
                "message": f"Claim request from {req.receiver.full_name} has been rejected.",
                "request_id": req.id,
                "status": req.status,
                "donation_status": donation.status,
            },
            status=status.HTTP_200_OK,
        )


class DonationRequestCancelView(APIView):
    """
    NGO cancels its own pending claim request.
    If no other pending requests remain, donation status reverts to AVAILABLE.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        req = get_object_or_404(DonationRequest.objects.select_related("donation", "receiver"), pk=pk)
        donation = req.donation

        if req.receiver != request.user and not is_admin_or_staff(request.user):
            raise PermissionDenied("You can only cancel your own claim requests.")

        if req.status != DonationRequest.RequestStatus.PENDING:
            return Response(
                {"error": f"Cannot cancel request that is currently '{req.status}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            req.status = DonationRequest.RequestStatus.CANCELLED
            req.save(update_fields=["status", "updated_at"])

            # If no pending requests remain on this donation, revert donation to AVAILABLE
            has_pending = DonationRequest.objects.filter(
                donation=donation,
                status=DonationRequest.RequestStatus.PENDING,
            ).exists()
            if not has_pending and donation.status == DonationStatus.REQUESTED:
                donation.transition_to(DonationStatus.AVAILABLE)

        return Response(
            {
                "message": "Your claim request has been cancelled.",
                "request_id": req.id,
                "status": req.status,
                "donation_status": donation.status,
            },
            status=status.HTTP_200_OK,
        )


class MyDonationsListView(generics.ListAPIView):
    """List all donations posted by the authenticated donor."""

    serializer_class = FoodDonationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            FoodDonation.objects.filter(donor=self.request.user)
            .select_related("category")
            .prefetch_related("requests")
            .order_by("-created_at")
        )


class MyRequestsListView(generics.ListAPIView):
    """List all claim requests submitted by the authenticated NGO."""

    serializer_class = DonationRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            DonationRequest.objects.filter(receiver=self.request.user)
            .select_related("donation", "donation__donor")
            .order_by("-created_at")
        )
