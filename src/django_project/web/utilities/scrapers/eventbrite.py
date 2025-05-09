import time
from datetime import datetime, timedelta

import requests
from django.conf import settings
from django.utils import timezone


def create_google_map_link(address: str) -> str:
    """create a link to a Google map for a provided address

    Args:
        address (str): address to map to

    Returns:
        str: url to Google Map
    """
    address = address.replace(" ", "+")
    address = address.replace("#", "%23")
    link = f"https://www.google.com/maps?q={address}"
    return link


def filter_events_by_date(events: list, date_filter: timezone) -> list:
    """
    Filters a list of event instances by a provided datetime.

    Args:
        events (list): List of dictionaries, each representing an event with 'name', 'description', and 'created' keys.
        date_filter (datetime): A datetime object to filter events created after this date.

    Returns:
        List of events created after the date_filter.
    """
    filtered_events = []
    for event in events:
        created_date = datetime.strptime(event["created"], "%Y-%m-%dT%H:%M:%SZ")
        created_date = timezone.make_aware(created_date, timezone.utc)
        if created_date > date_filter:
            filtered_events.append(event)
    return filtered_events


def get_organization_details(organization_id: str) -> dict:
    """get the details of an Eventbrite organization

    Args:
        organization_id (str): Eventbrite organization identifier

    Returns:
        dict: organizers block of json data as available from the Eventbrite API
    """

    url = f"https://www.eventbrite.com/api/v3/organizers/?ids={organization_id}"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return response.json()["organizers"][0]


def get_events_for_organization(organization_id: str, age: int = 7) -> list:
    """get a list of events for a given Eventbrite organization

    Args:
        organization_id (str): Eventbrite organization identifier
        age (int): number of days ago when events were created

    Returns:
        list: list of Eventbrite events created in the past <age> days
    """
    api_token = getattr(settings, "EVENTBRITE_API_KEY", None)
    if not api_token:
        return []
    url = f"https://www.eventbriteapi.com/v3/organizers/{organization_id}/events/"
    headers = {"Authorization": f"Bearer {api_token}"}
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    data = response.json()
    event_list = data["events"]
    age_datetime = timezone.now() - timedelta(days=age)
    return filter_events_by_date(event_list, age_datetime)


def get_event_details(event_id: str) -> dict:
    """get the details of an Eventbrite event

    Args:
        event_id (str): Eventbrite event identifier

    Returns:
        dict: event data as available from the Eventbrite API
    """
    url = f"https://www.eventbrite.com/api/v3/destination/events/?event_ids={event_id}&expand=primary_venue"
    attempts = 3
    for attempt in range(attempts):
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            return resp.json()["events"][0]
        except requests.exceptions.RequestException as err:
            if attempt < attempts - 1:
                time.sleep(2 * attempt)
                continue
            else:
                raise err
    return {}
