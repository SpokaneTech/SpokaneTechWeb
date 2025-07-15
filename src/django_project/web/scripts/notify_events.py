from django.utils import timezone
from requests import post
from bs4 import BeautifulSoup
from zoneinfo import ZoneInfo

from django.conf import settings
from web.models import Event


# Clean HTML text content (used for event.description)
def clean_html(text):
  """Clean HTML text content."""
  soup = BeautifulSoup(text, "html.parser")
  return soup.get_text()


# Utility to convert datetimes to the desired display timezone
def to_display_timezone(dt):
  """
  Convert a timezone-aware datetime to the configured display timezone.
  """
  if dt is None:
    return None
  # If dt is naive, assume it's in UTC
  if dt.tzinfo is None:
    dt = dt.replace(tzinfo=timezone.utc)

  # Note: theoretically this timezone should come from the event itself.
  #       but for now, since the current discord channel is for users in Spokane, WA
  #       we will hard-code the American/Los_Angeles timezone.
  #tz_name = getattr(settings, "TIME_ZONE", "UTC")
  tz_name = "America/Los_Angeles"
  return dt.astimezone(ZoneInfo(tz_name))


# Get an event as object data for the JSON payload
def get_event_object(event):
  """get an event as object data for the JSON payload."""
  local_dt = to_display_timezone(event.start_datetime)
  event_data = {
    "title": event.name,
    "description": clean_html(event.description),
    "url": event.url,
    "thumbnail": event.image.url if event.image else None,
    "color": 0x00ff00, # todo: get custom colors from event host
    "fields": [
      {
        "name": "When",
        "value": f"{local_dt.strftime('%A, %B %d %I:%M %p %Z')}",
        "inline": False
      },
      {
        "name": "Where",
        "value": f"**{event.location_name}**\n[{event.location_address}]({event.map_link})",
        "inline": False
      }
    ],
    "footer": {
      "text": f"{event.group.name}"
    }
  }
  return event_data


# Get all events as an object for the JSON payload (loops them through get_event_object() )
def get_events_as_object():
  """Get all events as an object for the JSON payload."""
  events = Event.objects.filter(start_datetime__gte=timezone.now())
  return [get_event_object(event) for event in events]


# Send an event notification to the discord webhook
def notify_discord():
  """Notify discord about upcoming events."""
  discord_url = getattr(settings, 'DISCORD_EVENTS_WEBHOOK_URL', None)
  if not discord_url:
    print("Discord webhook URL not set")
    return

  events = get_events_as_object()
  if not events:
    print("No events to notify")
    return

  payload = {
    "username": "Event Notifier 🤖",
    "content": "_Here are the upcoming Spokane Tech events for this week:_\n\n",
    "embeds": events
  }

  # send the request
  response = post(discord_url, json=payload)

  # Log if the response was unsuccessful
  if response.status_code > 299:
    print(f"Failed to notify discord: {response.status_code}")
    return


# Run the script
def run():
  notify_discord()
