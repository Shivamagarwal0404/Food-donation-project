"""
FoodShare — Users URL configuration.
"""
from django.urls import path
from .views import (
    RegisterView,
    UserProfileView,
    AddressListCreateView,
    AddressDetailView,
    VerifyOTPView,
    ResendOTPView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    PasswordResetResendView,
    LoginOTPVerifyView,
    LoginOTPResendView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="user-register"),
    path("verify-otp/", VerifyOTPView.as_view(), name="user-verify-otp"),
    path("resend-otp/", ResendOTPView.as_view(), name="user-resend-otp"),
    path("login-otp/verify/", LoginOTPVerifyView.as_view(), name="user-login-otp-verify"),
    path("login-otp/resend/", LoginOTPResendView.as_view(), name="user-login-otp-resend"),
    path("login/verify-otp/", LoginOTPVerifyView.as_view(), name="user-login-verify-otp"),
    path("login/resend-otp/", LoginOTPResendView.as_view(), name="user-login-resend-otp"),
    path("password-reset/request/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("password-reset/resend/", PasswordResetResendView.as_view(), name="password-reset-resend"),
    path("me/", UserProfileView.as_view(), name="user-me"),
    path("me/addresses/", AddressListCreateView.as_view(), name="user-addresses"),
    path("me/addresses/<int:pk>/", AddressDetailView.as_view(), name="user-address-detail"),
]

