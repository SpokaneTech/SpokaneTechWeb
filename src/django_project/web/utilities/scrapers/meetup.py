from __future__ import annotations

import html
import json
import re
from datetime import datetime, timedelta
from typing import Any

from bs4 import BeautifulSoup, Tag
from bs4.element import NavigableString, PageElement

from web.utilities.event_status import source_event_status
from web.utilities.html_utils import fetch_content, fetch_content_with_playwright

_TBD_LOCATION_NAMES = {"tbd", "tdb", "to be determined"}


def _iter_mappings(value: Any):
    """Yield every dictionary contained in a decoded Meetup data payload."""
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _iter_mappings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_mappings(child)


def _requested_event_data(soup: BeautifulSoup, url: str):
    """Ignore recommended events and group-level status in page JSON."""
    match = re.search(r"/events/([^/]+)/", url)
    event_id = match.group(1) if match else None
    for script in soup.find_all("script"):
        try:
            payload = json.loads(script.get_text())
        except (json.JSONDecodeError, TypeError):
            continue
        for item in _iter_mappings(payload):
            if item.get("__typename") == "Event" and str(item.get("id")) == event_id:
                yield item
            elif item.get("@type") == "Event":
                item_url = item.get("url") or item.get("@id")
                if isinstance(item_url, str) and item_url.rstrip("/") == url.rstrip("/"):
                    yield item


def _get_event_tags(soup: BeautifulSoup, url: str) -> list[str]:
    """Read only the requested event's topics, resolving Meetup's Apollo references."""
    match = re.search(r"/events/([^/]+)/", url)
    event_id = match.group(1) if match else None
    tags: list[str] = []
    seen: set[str] = set()
    for script in soup.find_all("script"):
        try:
            payload = json.loads(script.get_text())
        except (json.JSONDecodeError, TypeError):
            continue
        if not isinstance(payload, dict):
            continue
        props = payload.get("props") or {}
        page_props = props.get("pageProps") or {} if isinstance(props, dict) else {}
        if not isinstance(page_props, dict):
            page_props = {}
        raw_cache = page_props.get("__APOLLO_STATE__", payload.get("__APOLLO_STATE__", {}))
        topic_cache: dict[str, Any] = raw_cache if isinstance(raw_cache, dict) else {}

        def resolve(value: Any, cache: dict[str, Any] = topic_cache) -> Any:
            if isinstance(value, dict) and "__ref" in value:
                return cache.get(value["__ref"], {})
            return value

        candidates = [page_props.get("event"), payload.get("event")]
        candidates.extend(
            item
            for item in _iter_mappings(payload)
            if item.get("__typename") == "Event" and str(item.get("id")) == event_id
        )
        for candidate in candidates:
            event = resolve(candidate)
            if not isinstance(event, dict) or (event.get("id") is not None and str(event["id"]) != event_id):
                continue
            topics = resolve(event.get("topics", []))
            if isinstance(topics, dict):
                topics = topics.get("edges", topics.get("nodes", []))
            if not isinstance(topics, list):
                continue
            for topic in topics:
                topic = resolve(topic)
                if isinstance(topic, dict):
                    topic = resolve(topic.get("node", topic))
                name = topic.get("name") if isinstance(topic, dict) else topic
                if not isinstance(name, str):
                    continue
                name = " ".join(html.unescape(name).split())
                if name and name.casefold() not in seen:
                    tags.append(name)
                    seen.add(name.casefold())
    return tags


def _get_event_image(soup: BeautifulSoup, url: str) -> str:
    match = re.search(r"/events/([^/]+)/", url)
    event_id = match.group(1) if match else None
    for script in soup.find_all("script"):
        try:
            payload = json.loads(script.get_text())
        except (json.JSONDecodeError, TypeError):
            continue
        mappings = list(_iter_mappings(payload))
        photos = {}
        for mapping in mappings:
            for key, value in mapping.items():
                if isinstance(value, dict) and value.get("__typename") == "PhotoInfo":
                    photos[key] = value
        for item in mappings:
            if item.get("__typename") != "Event" or str(item.get("id")) != event_id:
                continue
            for key in ("featuredEventPhoto", "displayPhoto"):
                photo = item.get(key)
                if isinstance(photo, dict) and "__ref" in photo:
                    photo = photos.get(photo["__ref"])
                if isinstance(photo, dict) and isinstance(photo.get("source"), str):
                    return photo["source"]
    return ""


def _get_venue(page_content: str, soup: BeautifulSoup) -> dict[str, Any] | None:
    """Find Meetup's Venue object without depending on JSON field order."""
    for script in soup.find_all("script"):
        if not script.string:
            continue
        try:
            payload = json.loads(script.string)
        except json.JSONDecodeError:
            continue
        for item in _iter_mappings(payload):
            if item.get("__typename") == "Venue":
                return item

    # Meetup sometimes embeds serialized JSON in its page data rather than a
    # standalone JSON script. Decode the Venue object when it is available.
    venue_match = re.search(r'\{[^{}]*"__typename"\s*:\s*"Venue"[^{}]*\}', page_content)
    if venue_match:
        try:
            return json.loads(venue_match.group())
        except json.JSONDecodeError:
            pass
    return None


def _format_venue_address(venue: dict[str, Any]) -> str:
    """Return the display address supplied by Meetup, or an empty string."""
    address = venue.get("address")
    if isinstance(address, dict):
        return str(address.get("localized_address_display") or address.get("display") or "")
    if address:
        country = venue.get("country")
        parts = [
            address,
            venue.get("city"),
            venue.get("state"),
            country.upper() if isinstance(country, str) else country,
        ]
        return ", ".join(str(part) for part in parts if part)
    return ""


def get_event_information(url: str) -> dict:
    """capture information about an event from a meetup.com page

    Args:
        url (str): url of the event page

    Raises:
        Exception:

    Returns:
        dict: dictionary of information about the event as available on meetup.com
    """

    try:
        page_content: str = fetch_content_with_playwright(url)
        soup = BeautifulSoup(page_content, "html.parser")

        event_info: dict = {}
        requested_data = list(_requested_event_data(soup, url))
        statuses = [source_event_status(item) for item in requested_data]
        if "cancelled" in statuses:
            event_info["status"] = "cancelled"
        elif "active" in statuses:
            event_info["status"] = "active"
        event_info["tags_complete"] = any("topics" in item for item in requested_data)
        event_info["tags"] = _get_event_tags(soup, url)
        event_info["image_url"] = _get_event_image(soup, url)
        event_info["url"] = url
        event_info["name"] = soup.find("h1", class_="ds2-b32 text-ds2-text-fill-primary-enabled lg:ds2-b48")
        if event_info["name"]:
            event_info["name"] = event_info["name"].text
        description_div: PageElement | Tag | NavigableString | None = soup.find(
            "div", class_="w-full break-words transition-all duration-300 line-clamp-[15]"
        )
        if description_div and isinstance(description_div, Tag):  # Type check for Tag
            event_info["description"] = "".join(str(child) for child in description_div.children)

        time_element: PageElement | Tag | NavigableString | None = soup.find("time", class_="block")
        if time_element and isinstance(time_element, Tag):  # Check if time_element is a Tag
            start_time_string: Any = time_element.get("datetime", None)
            time_text: str = time_element.get_text(separator=" ").strip()

            if start_time_string and isinstance(start_time_string, str):
                start_dt = datetime.fromisoformat(start_time_string)
                event_info["start_datetime"] = start_dt

                # Parse duration from the time text which shows times in UTC
                # Format: "Friday, Feb 13 · 2:00 AM to 3:00 AM UTC"
                # We calculate the duration and add it to start_dt to preserve timezone
                if " to " in time_text:
                    time_parts = time_text.split(" to ")
                    if len(time_parts) == 2:
                        # Extract start time from text (in UTC)
                        start_match = re.search(r"(\d{1,2}):(\d{2})\s*([APap][Mm])", time_parts[0])
                        # Extract end time from text (in UTC)
                        end_match = re.search(r"(\d{1,2}):(\d{2})\s*([APap][Mm])", time_parts[1])

                        if start_match and end_match:
                            # Parse start time (UTC)
                            start_hour = int(start_match.group(1))
                            start_minute = int(start_match.group(2))
                            start_period = start_match.group(3).upper()
                            if start_period == "PM" and start_hour != 12:
                                start_hour += 12
                            elif start_period == "AM" and start_hour == 12:
                                start_hour = 0

                            # Parse end time (UTC)
                            end_hour = int(end_match.group(1))
                            end_minute = int(end_match.group(2))
                            end_period = end_match.group(3).upper()
                            if end_period == "PM" and end_hour != 12:
                                end_hour += 12
                            elif end_period == "AM" and end_hour == 12:
                                end_hour = 0

                            # Calculate duration in minutes
                            start_minutes = start_hour * 60 + start_minute
                            end_minutes = end_hour * 60 + end_minute

                            # Handle overnight events
                            if end_minutes <= start_minutes:
                                end_minutes += 24 * 60

                            duration_minutes = end_minutes - start_minutes

                            # Add duration to start_dt to get end_dt in the same timezone
                            end_dt = start_dt + timedelta(minutes=duration_minutes)
                            event_info["end_datetime"] = end_dt
                        else:
                            event_info["end_datetime"] = None
                    else:
                        event_info["end_datetime"] = None

        venue = _get_venue(page_content, soup)
        location_name: str = ""
        location_address: str = ""
        is_tbd_location = False
        if venue:
            location_name = str(venue.get("name") or "").strip()
            location_address = _format_venue_address(venue)

            # Meetup uses TBD for events whose physical location is not yet
            # announced. Treat it as no location rather than displaying it.
            if location_name.casefold() in _TBD_LOCATION_NAMES:
                is_tbd_location = True
                location_name = ""
                location_address = ""
        if not location_name and not is_tbd_location:
            online_p = soup.find("p", class_="ds2-k16 text-ds2-text-fill-primary-enabled")
            if online_p and online_p.get_text(strip=True) == "Online event":
                location_name = "Online event"
        event_info["location_complete"] = bool(
            is_tbd_location or location_name == "Online event" or (venue and location_name and location_address)
        )
        event_info["location_name"] = location_name
        event_info["location_address"] = location_address

        map_link: str = ""
        map_link_match: re.Match[str] | None = re.search(
            r'<a[^>]*data-testid="map-link"[^>]*href="([^"]+)"', page_content
        )
        if map_link_match:
            raw_link: str | Any = map_link_match.group(1)
            map_link = html.unescape(raw_link)
        event_info["map_link"] = map_link

        pattern = r"/events/([^/]+)/"
        match = re.search(pattern, url)
        if match:
            event_info["social_platform_id"] = match.group(1)
        return event_info
    except AttributeError as err:
        print(f"Failed to get event information: {err}")
        return {}


def get_event_links(url: str) -> list:
    """capture urls for upcoming events from a group page on meetup.com

    Args:
        url (str): url of the group page; example: "https://www.meetup.com/python-spokane/events/"

    Raises:
        Exception:

    Returns:
        list: list of urls for upcoming events as available on the group page on meetup.com
    """
    page_content: str | None = fetch_content_with_playwright(f"{url}/events/?type=upcoming")
    if page_content:
        event_urls: list[Any] = re.findall(r'"eventUrl":"(https://www\.meetup\.com/[^/]+/events/\d+/)"', page_content)
        return [url for url in event_urls]
    return []


def get_group_description(url: str) -> str:
    """capture the description of a group from a meetup.com page

    Args:
        url (str): url of the group page

    Raises:
        Exception:

    Returns:
        str: html from the description of the group as available on meetup.com
    """
    page_content: bytes | Any = fetch_content(url)
    soup = BeautifulSoup(page_content, "html.parser")
    description_div: PageElement | Tag | NavigableString | None = soup.find(
        "div", class_="ds2-r16 break-words utils_description__BlOCA"
    )

    if description_div and isinstance(description_div, Tag):  # Check if description_div is a Tag
        description: str = "".join(str(child) for child in description_div.children)
        return description
    return ""  # Return an empty string if description_div is None or not a Tag
