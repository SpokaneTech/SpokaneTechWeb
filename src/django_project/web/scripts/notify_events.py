from django.utils import timezone
from requests import post

from django.conf import settings
from web.models import Event


# returns an array of events from the database
def get_events():
  # retrieve events from the database
  events = Event.objects.filter(start_datetime__gte=timezone.now())

  return events


# todo: this template needs cleanup.
def get_event_object(event):
    return {
        "name": event.name,
        "description": event.description, # todo: handle the html content and post to discord accordingly
        "color": 0x00ff00,
        "fields": [ # todo: clean up these start / end fields.
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

def get_events_as_object():
    events = get_events()
    return [get_event_object(event) for event in events]


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
        "content": "Upcoming events:",
        "embeds": events
    }

    # send the request
    response = post(discord_url, json=payload)

    # Log if the response was unsuccessful
    if response.status_code > 299:
        print(f"Failed to notify discord: {response.status_code}")
        return


def run():
  notify_discord()
