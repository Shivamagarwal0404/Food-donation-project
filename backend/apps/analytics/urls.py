"""
FoodShare — Analytics URL configuration.
"""
from django.urls import path
from .views import PlatformImpactView

urlpatterns = [
    path("impact/", PlatformImpactView.as_view(), name="analytics-impact"),
]

