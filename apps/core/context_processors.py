"""
Injects MIU branding configuration into every template's context so the
institution name, system name, logo path, and color palette can be
changed from one place (settings.DISTRICT_BRANDING) without touching templates.
"""
from django.conf import settings


def miu_branding(request):
    return {
        "branding": settings.DISTRICT_BRANDING,
    }
