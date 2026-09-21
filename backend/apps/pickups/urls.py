"""
FoodShare — Pickups URL configuration.
"""
from django.urls import path
from .views import (
    PickupListView,
    PickupDetailView,
    AvailablePickupsListView,
    MyPickupsListView,
    PickupAssignView,
    PickupMarkPickedUpView,
    PickupMarkDeliveredView,
    PickupMarkCompletedView,
    PickupStatusUpdateView,
)

urlpatterns = [
    path("", PickupListView.as_view(), name="pickup-list"),
    path("<int:pk>/", PickupDetailView.as_view(), name="pickup-detail"),
    path("available/", AvailablePickupsListView.as_view(), name="pickup-available-list"),
    path("my-pickups/", MyPickupsListView.as_view(), name="my-pickups-list"),
    path("<int:pk>/assign/", PickupAssignView.as_view(), name="pickup-assign"),
    path("<int:pk>/pickup/", PickupMarkPickedUpView.as_view(), name="pickup-mark-picked-up"),
    path("<int:pk>/deliver/", PickupMarkDeliveredView.as_view(), name="pickup-mark-delivered"),
    path("<int:pk>/complete/", PickupMarkCompletedView.as_view(), name="pickup-mark-completed"),
    path("<int:pk>/status/", PickupStatusUpdateView.as_view(), name="pickup-status-update"),
]
