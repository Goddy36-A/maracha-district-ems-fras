from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Convenient console email backend for local development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
