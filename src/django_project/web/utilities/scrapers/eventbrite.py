import random
import time
from datetime import datetime, timedelta
from typing import Any

import requests
from django.conf import settings
from django.utils import timezone
from requests.exceptions import HTTPError, RequestException


def create_google_map_link(address: str) -> str:
    """create a link to a Google map for a provided address

    Args:
        address (str): address to map to

    Returns:
        str: url to Google Map
    """
    address = address.replace(" ", "+")
    address = address.replace("#", "%23")
    link: str = f"https://www.google.com/maps?q={address}"
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
    filtered_events: list = []
    for event in events:
        created_date: datetime = datetime.strptime(event["created"], "%Y-%m-%dT%H:%M:%SZ")
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

    url: str = f"https://www.eventbrite.com/api/v3/organizers/?ids={organization_id}"
    response: requests.Response = requests.get(url, timeout=15)
    response.raise_for_status()
    return response.json()["organizers"][0]


def get_events_for_organization(organization_id: str, age: int = 14) -> list:
    """get a list of events for a given Eventbrite organization

    Args:
        organization_id (str): Eventbrite organization identifier
        age (int): number of days ago when events were created

    Returns:
        list: list of Eventbrite events created in the past <age> days
    """
    api_token: str | None = getattr(settings, "EVENTBRITE_API_KEY", None)
    if not api_token:
        return []
    start_date_range_end: str = (timezone.now() + timedelta(days=age)).strftime("%Y-%m-%dT%H:%M:%SZ")
    start_date_range_start: str = timezone.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    url: str = f"https://www.eventbriteapi.com/v3/organizers/{organization_id}/events/?start_date.range_start={start_date_range_start}&start_date.range_end={start_date_range_end}"
    headers: dict[str, str] = {"Authorization": f"Bearer {api_token}"}
    response: requests.Response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    data: dict = response.json()
    return data["events"]


def get_event_details(event_id: str) -> dict:
    """Get the details of an Eventbrite event, with retry logic for 429 errors.

    Args:
        event_id (str): Eventbrite event identifier

    Returns:
        dict: event data as available from the Eventbrite API

    Raises:
        requests.exceptions.RequestException: If the request fails after all retries
                                              for reasons other than 429, or if 429
                                              persists beyond max retries.
    """
    # --- Configuration for Retry Logic ---
    MAX_RETRIES = 5  # Maximum number of times to retry a failed request
    INITIAL_BACKOFF_TIME = 1  # Initial wait time in seconds before the first 429 retry
    MAX_BACKOFF_TIME = 60  # Maximum wait time in seconds for 429 retries

    url: str = f"https://www.eventbrite.com/api/v3/destination/events/?event_ids={event_id}&expand=primary_venue"

    # Initialize backoff time for 429 errors
    current_429_backoff_time = INITIAL_BACKOFF_TIME

    for attempt in range(MAX_RETRIES + 1):  # +1 because range(N) goes from 0 to N-1, so N attempts
        try:
            print(f"Attempt {attempt + 1}/{MAX_RETRIES + 1} for event ID {event_id}...")
            resp: requests.Response = requests.get(url, timeout=15)

            # Explicitly check for 429 before calling raise_for_status
            if resp.status_code == 429:
                print(f"Received 429 Too Many Requests for {url}.")
                retry_after_header: str | None | Any = resp.headers.get("Retry-After")
                wait_time: float = 0.0

                if retry_after_header:
                    try:
                        wait_time = float(retry_after_header)
                        print(f"Server requested to retry after {wait_time} seconds (from Retry-After header).")
                    except ValueError:
                        # Fallback if Retry-After isn't a valid integer
                        wait_time = min(
                            current_429_backoff_time + random.uniform(0, 0.5 * current_429_backoff_time),  # nosec
                            MAX_BACKOFF_TIME,
                        )
                        print(f"Invalid Retry-After header. Applying exponential backoff for {wait_time:.2f} seconds.")
                else:
                    # Apply exponential backoff with jitter
                    wait_time = min(
                        current_429_backoff_time + random.uniform(0, 0.5 * current_429_backoff_time),  # nosec
                        MAX_BACKOFF_TIME,
                    )
                    print(f"No Retry-After header. Applying exponential backoff for {wait_time:.2f} seconds.")

                # Only sleep and increment backoff time if it's not the last retry
                if attempt < MAX_RETRIES:
                    time.sleep(wait_time)
                    current_429_backoff_time *= 2  # Double for next potential 429 retry
                    continue  # Skip the rest of the loop and retry
                else:
                    print(f"Max retries ({MAX_RETRIES}) for 429 reached. Raising the last error.")
                    raise HTTPError("Max retries reached for 429 Too Many Requests.")

            # If not a 429, raise for other status codes
            resp.raise_for_status()

            # If successful, return the data
            return resp.json()["events"][0]

        except HTTPError as err:
            # Handle other HTTP errors (e.g., 400, 401, 404, 500)
            print(f"HTTP Error {err.response.status_code}: {err.response.reason} for {url}.")
            if attempt < MAX_RETRIES:
                sleep_for: float = 3 * attempt  # Keep original backoff for non-429 errors
                print(f"Waiting {sleep_for} seconds before retrying...")
                time.sleep(sleep_for)
            else:
                print(f"Max retries ({MAX_RETRIES}) reached for non-429 HTTP error. Raising the last error.")
                raise err  # Re-raise the specific HTTP error on the last attempt

        except RequestException as err:
            # Catch other request-related errors (e.g., ConnectionError, Timeout)
            print(f"An unexpected request error occurred for {url}: {err}")
            if attempt < MAX_RETRIES:
                sleep_for = 3 * attempt + random.uniform(0, 1)  # nosec # Add jitter
                print(f"Waiting {sleep_for:.2f} seconds before retrying...")
                time.sleep(sleep_for)
            else:
                print(f"Max retries ({MAX_RETRIES}) reached for request error. Raising the last error.")
                raise err  # Re-raise the error on the last attempt

    # This part should ideally not be reached if MAX_RETRIES is set up correctly
    # and errors are always re-raised on the last attempt.
    print(
        f"Function completed without returning data for event_id {event_id}. This should not happen if errors are always re-raised."
    )
    return {}  # Fallback, though an exception should ideally cover failure# Initialize backoff time for 429 errors
