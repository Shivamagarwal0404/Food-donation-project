"""
FoodShare — Donations URL configuration.
"""
from django.urls import path
from .views import (
    FoodCategoryListCreateView,
    FoodCategoryDetailView,
    FoodDonationListCreateView,
    FoodDonationDetailView,
    DonationCancelView,
    DonationRequestCreateView,
    DonationRequestAcceptView,
    DonationRequestRejectView,
    DonationRequestCancelView,
    MyDonationsListView,
    MyRequestsListView,
)

urlpatterns = [
    # Categories (Public view, Admin management)
    path("categories/", FoodCategoryListCreateView.as_view(), name="donation-categories"),
    path("categories/<int:pk>/", FoodCategoryDetailView.as_view(), name="donation-category-detail"),

    # Donations (Public view, Donor creation, Detail, Donor update/cancel)
    path("", FoodDonationListCreateView.as_view(), name="donation-list-create"),
    path("<int:pk>/", FoodDonationDetailView.as_view(), name="donation-detail"),
    path("<int:pk>/cancel/", DonationCancelView.as_view(), name="donation-cancel"),
    path("my-donations/", MyDonationsListView.as_view(), name="my-donations"),

    # Requests (NGO submission, Donor accept/reject, NGO cancel)
    path("requests/", DonationRequestCreateView.as_view(), name="donation-request-create"),
    path("requests/<int:pk>/accept/", DonationRequestAcceptView.as_view(), name="donation-request-accept"),
    path("requests/<int:pk>/reject/", DonationRequestRejectView.as_view(), name="donation-request-reject"),
    path("requests/<int:pk>/cancel/", DonationRequestCancelView.as_view(), name="donation-request-cancel"),
    path("my-requests/", MyRequestsListView.as_view(), name="my-requests"),
]
