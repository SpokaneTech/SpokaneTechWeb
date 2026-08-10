from django.utils import timezone
from zoneinfo import ZoneInfo

PACIFIC = ZoneInfo("America/Los_Angeles")


def convert_to_pacific(dt: timezone.datetime) -> timezone.datetime:
    """Convert a datetime to Pacific Time."""
    return dt.astimezone(PACIFIC)
