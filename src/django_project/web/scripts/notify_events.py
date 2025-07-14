from django.utils import timezone
from requests import post
from bs4 import BeautifulSoup

from django.conf import settings
from web.models import Event

def clean_html(text):
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text()


# returns an array of events from the database
def get_events():
  # retrieve events from the database
  events = Event.objects.filter(start_datetime__gte=timezone.now())

  return events


# todo: this template needs cleanup.
def get_event_object(event):
    event_data = {
        "title": event.name,
        "description": clean_html(event.description),
        "url": event.url,
        "thumbnail": event.image.url if event.image else None,
        "color": 0x00ff00, # todo: get custom colors from event host
        "fields": [
            {
              "name": "When",
              "value": f"{event.start_datetime.strftime('%A, %B %d %H:%M')}",
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


def run():
  notify_discord()
