"""
Attendance-rate calculation.

Per spec Section 19: "Do not assume weekends, public holidays, or
institutional schedules without configuring them appropriately." This
module makes that configuration explicit rather than hard-coding it.
"""
from datetime import timedelta

from django.conf import settings

from .models import Attendance

# Configurable: which weekday numbers (Mon=0 ... Sun=6) count as
# non-working days by default. Override via settings.WORKING_DAYS if MIU's
# policy differs (e.g. a 6-day week).
DEFAULT_NON_WORKING_WEEKDAYS = getattr(settings, "NON_WORKING_WEEKDAYS", (5, 6))  # Sat, Sun

# Public holidays are NOT assumed. Supply a list of `date` objects via
# settings.PUBLIC_HOLIDAYS (or extend this function) once MIU's official
# academic/institutional calendar is available.
PUBLIC_HOLIDAYS = getattr(settings, "PUBLIC_HOLIDAYS", [])


def expected_working_days(start_date, end_date):
    """Count expected working days in [start_date, end_date], inclusive."""
    if end_date < start_date:
        return 0
    count = 0
    current = start_date
    while current <= end_date:
        if current.weekday() not in DEFAULT_NON_WORKING_WEEKDAYS and current not in PUBLIC_HOLIDAYS:
            count += 1
        current += timedelta(days=1)
    return count


def attendance_rate(employee, start_date, end_date):
    """
    Attendance Rate = Days Present / Expected Working Days × 100
    Returns a dict with the raw numbers and the percentage, so callers
    (reports/dashboards) can display both the metric and its basis rather
    than a bare, unexplained percentage.
    """
    expected = expected_working_days(start_date, end_date)
    present_days = Attendance.objects.filter(
        employee=employee, date__range=(start_date, end_date), status="PRESENT",
    ).count()

    rate = round((present_days / expected) * 100, 2) if expected else None

    return {
        "expected_working_days": expected,
        "present_days": present_days,
        "attendance_rate": rate,
    }
