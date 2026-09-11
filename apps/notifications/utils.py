from .models import Notification


def notify(recipient, message, link=""):
    """No-op safely if recipient is None (e.g. employee has no linked user account)."""
    if recipient is None:
        return None
    return Notification.objects.create(recipient=recipient, message=message, link=link)
