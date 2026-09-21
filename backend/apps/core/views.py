"""
FoodShare — Core views.
Provides health check and system diagnostic status.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.db import connection


class HealthCheckView(APIView):
    """System health check verifying database and application connectivity."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        db_healthy = True
        db_error = None
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception as e:
            db_healthy = False
            db_error = str(e)

        overall_status = "healthy" if db_healthy else "unhealthy"
        http_status = status.HTTP_200_OK if db_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

        return Response(
            {
                "status": overall_status,
                "database": "connected" if db_healthy else f"error: {db_error}",
                "platform": "FoodShare Food Donation API",
                "version": "1.0.0",
            },
            status=http_status,
        )

