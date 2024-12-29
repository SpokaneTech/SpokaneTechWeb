import re
from datetime import datetime, timedelta, timezone

from bs4 import BeautifulSoup
from web.utilities.html_utils import fetch_content, fetch_content_with_playwright


def get_end_datetime(datetime_string: str, time_string: str) -> datetime:
    """create a datetime object with timezone information from infromation parsed from a meetup.com event page

    Args:
        datetime_string (str): string representation of a datetime; example: '2025-01-06T07:00:00-08:00'
        time_string (str): string representation of a time; example: '8:00 AM   PST'

    Returns:
        datetime: datetime object with timezone information
    """

    # Extract the date part and timezone offset from the first string
    date_part = datetime_string.split("T")[0]
    timezone_offset = datetime_string[-6:]  # Extract the offset (-08:00)

    # Convert the timezone offset into a timedelta and create a timezone object
    offset_hours, offset_minutes = map(int, timezone_offset.split(":"))
    offset = timedelta(hours=offset_hours, minutes=offset_minutes)
    tz = timezone(offset)

    # Parse the time string
    time_part = time_string.split("   ")[0].strip()  # Get the time part
    time_obj = datetime.strptime(time_part, "%I:%M %p")  # Parse 12-hour format

    # Combine date and time into a new datetime object
    combined_datetime = datetime.combine(datetime.strptime(date_part, "%Y-%m-%d").date(), time_obj.time())

    # Apply the extracted timezone to the combined datetime
    combined_datetime_with_tz = combined_datetime.replace(tzinfo=tz)
    return combined_datetime_with_tz


def get_event_information(url: str) -> dict:
    """capture information about an event from a meetup.com page

    Args:
        url (str): url of the event page

    Raises:
        Exception:

    Returns:
        dict: dictionary of information about the event as availble on meetup.com
    """
    try:
        page_content = fetch_content_with_playwright(url)
        soup = BeautifulSoup(page_content, "html.parser")

        event_info: dict = {}
        event_info["url"] = url
        event_info["name"] = soup.find(
            "h1", class_="overflow-hidden overflow-ellipsis text-3xl font-bold leading-snug"
        ).text
        description_div = soup.find("div", class_="break-words")
        event_info["description"] = "".join(str(child) for child in description_div.children)
        start_time_string = soup.find("time")["datetime"]
        time_element = soup.find("time")
        if time_element:
            time_text = time_element.get_text(separator=" ").strip()
            end_time_string = time_text.split(" to ")[-1]

        event_info["start_datetime"] = datetime.fromisoformat(start_time_string)
        event_info["end_datetime"] = get_end_datetime(start_time_string, end_time_string)
        location_div = soup.find("div", class_="overflow-hidden pl-4 md:pl-4.5 lg:pl-5")

        if "Needs a location" not in location_div.text:
            location_name = location_div.find("a", {"data-testid": "venue-name-link"}) if location_div else None
            location_address = location_div.find("div", {"data-testid": "location-info"}) if location_div else None
            map_link = location_div.find("a", {"data-testid": "venue-name-link"})["href"] if location_div else None

            event_info["location_name"] = location_name.text if location_name else ""
            event_info["location_address"] = location_address.text if location_address else ""
            event_info["map_link"] = map_link if map_link else ""
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
        url (str): url of the group page; example: "https://www.meetup.com/python-spokane/events/?type=upcoming"

    Raises:
        Exception:

    Returns:
        list: list of urls for upcoming events as availble on the group page on meetup.com
    """
    page_content = fetch_content_with_playwright(url)
    soup = BeautifulSoup(page_content, "html.parser")
    event_list = soup.find("ul", class_="flex w-full flex-col space-y-5 px-4 md:px-0")
    if event_list:
        return [li.find("a")["href"] for li in event_list.find_all("li") if li.find("a", href=True)]
    return []


def get_group_description(url: str) -> str:
    """capture the description of a group from a meetup.com page

    Args:
        url (str): url of the group page

    Raises:
        Exception:

    Returns:
        str: html from the description of the group as availble on meetup.com
    """
    page_content = fetch_content(url)
    soup = BeautifulSoup(page_content, "html.parser")

    description_div = soup.find("div", class_="break-words utils_description__BlOCA")
    description = "".join(str(child) for child in description_div.children)
    return description