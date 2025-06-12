import re
from datetime import datetime, timedelta, timezone
from typing import Any

from bs4 import BeautifulSoup, Tag
from bs4.element import AttributeValueList, NavigableString, PageElement
from web.utilities.html_utils import fetch_content, fetch_content_with_playwright


def get_end_datetime(datetime_string: str, time_string: str) -> datetime | None:
    """create a datetime object with timezone information from information parsed from a meetup.com event page

    Args:
        datetime_string (str): string representation of a datetime; example: '2025-01-06T07:00:00-08:00'
        time_string (str): string representation of a time; example: '8:00 AM   PST'

    Returns:
        datetime: datetime object with timezone information
    """
    try:
        # Extract the date part and timezone offset from the first string
        date_part: str = datetime_string.split("T")[0]
        timezone_offset: str = datetime_string[-6:]  # Extract the offset (-08:00)

        # Convert the timezone offset into a timedelta and create a timezone object
        offset_hours, offset_minutes = map(int, timezone_offset.split(":"))
        offset = timedelta(hours=offset_hours, minutes=offset_minutes)
        tz = timezone(offset)

        # Parse the time string
        time_part: str = time_string.split("   ")[0].strip()  # Get the time part
        time_obj: datetime = datetime.strptime(time_part.replace("  ", ""), "%I:%M %p")  # Parse 12-hour format

        # Combine date and time into a new datetime object
        combined_datetime: datetime = datetime.combine(datetime.strptime(date_part, "%Y-%m-%d").date(), time_obj.time())

        # Apply the extracted timezone to the combined datetime
        combined_datetime_with_tz: datetime = combined_datetime.replace(tzinfo=tz)
        return combined_datetime_with_tz
    except Exception as err:
        print(err)
        return None


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
        page_content = fetch_content_with_playwright(url)
        # page_content: bytes | Any = fetch_content(url)
        soup = BeautifulSoup(page_content, "html.parser")

        event_info: dict = {}
        event_info["url"] = url
        event_info["name"] = soup.find("h1", class_="overflow-hidden overflow-ellipsis text-3xl font-bold leading-snug")
        if event_info["name"]:
            event_info["name"] = event_info["name"].text
        description_div: PageElement | Tag | NavigableString | None = soup.find("div", class_="break-words")
        if description_div:
            if isinstance(description_div, Tag):  # Type check for Tag
                event_info["description"] = "".join(str(child) for child in description_div.children)

        time_element: PageElement | Tag | NavigableString | None = soup.find("time")
        if time_element:
            if isinstance(time_element, Tag):  # Check if time_element is a Tag
                start_time_string: str | AttributeValueList | None = time_element.get("datetime", None)
                time_text: str = time_element.get_text(separator=" ").strip()
                end_time_string: str = time_text.split(" to ")[-1]

                if start_time_string:
                    if isinstance(start_time_string, str):  # Check if start_time_string is a str
                        event_info["start_datetime"] = datetime.fromisoformat(start_time_string)
                        event_info["end_datetime"] = get_end_datetime(start_time_string, end_time_string)
        location_div: PageElement | Tag | NavigableString | None = soup.find(
            "div", class_="overflow-hidden pl-4 md:pl-4.5 lg:pl-5"
        )

        if location_div and "Needs a location" not in location_div.text:
            if isinstance(location_div, Tag):  # Check if location_div is a Tag
                location_name: PageElement | Tag | NavigableString | None = location_div.find(
                    "a", {"data-testid": "venue-name-link"}
                )
                location_address: PageElement | Tag | NavigableString | None = location_div.find(
                    "div", {"data-testid": "location-info"}
                )
                map_link: PageElement | Tag | NavigableString | None = location_div.find(
                    "a", {"data-testid": "venue-name-link"}
                )
                if location_name:
                    event_info["location_name"] = location_name.text
                if location_address:
                    event_info["location_address"] = location_address.text
                if map_link:
                    if isinstance(map_link, Tag):  # Ensure map_link is a Tag before accessing attributes
                        event_info["map_link"] = map_link["href"]
        pattern = r"/events/([^/]+)/"
        match: re.Match[str] | None = re.search(pattern, url)
        if match:
            event_info["social_platform_id"] = match.group(1)
        return event_info
    except AttributeError as err:
        print(f"Failed to get event information: {err}")
        return {}


def get_event_links(url: str) -> list:
    """capture urls for upcoming events from a group page on meetup.com

    Args:
        url (str): url of the group page; example: "https://www.meetup.com/python-spokane/events/?type=upcoming"

    Raises:
        Exception:

    Returns:
        list: list of urls for upcoming events as available on the group page on meetup.com
    """
    page_content: str | None = fetch_content_with_playwright(url)
    if page_content:
        soup = BeautifulSoup(page_content, "html.parser")
        event_list: PageElement | Tag | NavigableString | None = soup.find(
            "ul", class_="flex w-full flex-col space-y-5 px-4 md:px-0"
        )

        if event_list and isinstance(event_list, Tag):  # Ensure event_list is a Tag
            urls: list = []
            for li in event_list.find_all("li"):  # Iterate over li elements
                if isinstance(li, Tag):  # Ensure li is a Tag
                    a: PageElement | Tag | NavigableString | None = li.find(
                        "a", href=True
                    )  # Find <a> with href attribute
                    if isinstance(a, Tag):  # Ensure a is a Tag
                        urls.append(a["href"])  # Access href attribute
            return urls
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
        "div", class_="break-words utils_description__BlOCA"
    )

    if description_div and isinstance(description_div, Tag):  # Check if description_div is a Tag
        description: str = "".join(str(child) for child in description_div.children)
        return description
    return ""  # Return an empty string if description_div is None or not a Tag
