"""
FoodShare — Production settings.
All secrets MUST come from environment variables — never hard-coded here.
"""
from decouple import Csv, config
from .base import *  # noqa

DEBUG = config("DJANGO_DEBUG", default=False, cast=bool)

# Security settings — configurable for HTTP initial deployment, easily switched to HTTPS
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# SSL & HTTPS redirect (default False for initial HTTP-only EC2 deployment)
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=False, cast=bool)
SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", default=False, cast=bool)
CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", default=False, cast=bool)

if SECURE_SSL_REDIRECT:
    SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=31536000, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
else:
    SECURE_HSTS_SECONDS = 0

# Gunicorn / Nginx proxy headers
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Static files served by Nginx in production
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

# Media storage: Local Docker volume (USE_S3=False) for this deployment
USE_S3 = config("USE_S3", default=False, cast=bool)
