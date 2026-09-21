"""
FoodShare — Root URL configuration.
All API endpoints are prefixed with /api/v1/.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from apps.core.views import HealthCheckView
from apps.users.views import FoodShareTokenObtainPairView
from apps.users.views import (
    FoodShareTokenObtainPairView,
    LoginOTPVerifyView,
    LoginOTPResendView,
)

urlpatterns = [
    # Django Admin
    path("django-admin/", admin.site.urls),

    # Health check
    path("api/v1/health/", HealthCheckView.as_view(), name="health-check"),

    # Authentication (JWT)
    path("api/v1/auth/token/", FoodShareTokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("api/v1/auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("api/v1/auth/login-otp/verify/", LoginOTPVerifyView.as_view(), name="auth-login-otp-verify"),
    path("api/v1/auth/login-otp/resend/", LoginOTPResendView.as_view(), name="auth-login-otp-resend"),

    # FoodShare Domain API Routes
    path("api/v1/users/", include("apps.users.urls")),
    path("api/v1/donations/", include("apps.donations.urls")),
    path("api/v1/pickups/", include("apps.pickups.urls")),
    path("api/v1/analytics/", include("apps.analytics.urls")),
]

# Media file serving in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
