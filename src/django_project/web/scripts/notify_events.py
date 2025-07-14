from django.utils import timezone
from requests import post

from django.conf import settings
from web.models import Event


# returns an array of events from the database
def get_events():
  # retrieve events from the database
  events = Event.objects.filter(start_datetime__gte=timezone.now())

  return events


def get_events_object(event):
    return {
        "name": event.name,
        "description": event.description,
        "color": 0x00ff00,
        "fields": [
            {
                "name": "Start Time",
                "value": event.start_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                "inline": False
            },
            {
                "name": "End Time",
                "value": event.end_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                "inline": False
            }
        ]
    }

def get_events_as_json():
    events = get_events()
    return [get_events_object(event) for event in events]


def notify_discord():
    """Notify discord about upcoming events."""
    discord_url = getattr(settings, 'DISCORD_EVENTS_WEBHOOK_URL', None)
    if not discord_url:
        print("Discord webhook URL not set")
        return

    embeds = get_events_as_json()
    if not embeds:
        print("No events to notify")
        return

    payload = {
        "content": "Upcoming events:",
        "embeds": embeds
    }

    response = post(discord_url, json=payload)
    print(response.status_code)
    print(response.content)


def run():
  notify_discord()
