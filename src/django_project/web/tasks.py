import logging
import random
import re
import time
from datetime import timedelta
from typing import Any

import requests
from bs4 import BeautifulSoup
from celery import shared_task
from django.conf import settings
from django.db.models.manager import BaseManager
from django.utils import timezone

from web.models import Event, Link, Tag, TechGroup
from web.utilities.dt_utils import convert_to_pacific
from web.utilities.notifiers.discord import DiscordNotifier
from web.utilities.notifiers.linkedin import LinkedInOrganizationClient
from web.utilities.scrapers.eventbrite import (
    create_google_map_link,
    get_event_details,
    get_events_for_organization,
    get_organization_details,
)
from web.utilities.scrapers.meetup import (
    get_event_information,
    get_event_links,
    get_group_description,
)


@shared_task(time_limit=30, max_retries=0, name="web.test_task")
def test_task() -> str:
    logging.info("test task starting")
    time.sleep(3)
    logging.info("test task completed")
    return "test task completed!"


@shared_task(time_limit=900, max_retries=3, name="web.ingest_meetup_group_details")
def ingest_meetup_group_details(group_pk, url: str) -> str:
    updated = False
    group = TechGroup.objects.get(pk=group_pk)
    group_details = get_group_description(url)
    if not group_details:
        return f"no details found for {group.name}"
    if group.description != group_details:
        group.description = group_details
        group.save()
        updated = True
    if updated:
        return f"updated details for {group.name}"
    else:
        return f"no updates needed for {group.name}"


@shared_task(time_limit=900, max_retries=3, name="web.ingest_eventbrite_organization_details")
def ingest_eventbrite_organization_details(group_pk) -> str:
    updated = False
    group = TechGroup.objects.get(pk=group_pk)
    link = group.links.filter(name=f"{group.name} {group.platform.name} page").distinct()[0]
    eb_group_id = link.url.split("-")[-1]

    organization_details = get_organization_details(eb_group_id)
    description = organization_details["long_description"]["text"]
    if description:
        if group.description != description:
            group.update(description=description)
            updated = True
    if organization_details.get("website"):
        website = organization_details["website"]
        if website and not group.links.filter(url=website):
            link = Link.objects.create(url=website, name="website")
            group.links.add(link)
            updated = True
    if updated:
        return f"updated details for {group.name}"
    return f"no updates needed for {group.name}"


@shared_task(time_limit=900, max_retries=3, name="web.ingest_future_meetup_events")
def ingest_future_meetup_events(group_pk) -> str:
    group = TechGroup.objects.get(pk=group_pk)
    if not group:
        return f"group with pk {group_pk} not found"
    platform_links = group.links.filter(name=f"{group.name} {group.platform.name} page").distinct()
    if not platform_links:
        return f"no {group.platform.name} links found for {group.name}"

    event_links: list = []
    event_count: int = 0

    # filter event links for future recurring events. Meetup uses a numeric event id in the url for upcoming events
    # and a alphanumeric event id for recurring events. This is causing duplicate events to be added to the database.
    numeric_event_pattern = re.compile(r"/events/(\d+)/")

    for link in group.links.filter(name=f"{group.name} {group.platform.name} page").distinct():
        ingest_links: list = [url for url in get_event_links(link.url) if numeric_event_pattern.search(url)]
        event_links.extend(ingest_links)
        for event_link in ingest_links:
            event_info = get_event_information(event_link)
            event_info["group"] = group
            if event_info:
                if not event_info.get("name", None):
                    logging.error(f"error parsing name for event hosted by {group.name}; data = {event_info}")
                    continue
                if event_info["social_platform_id"]:
                    _, is_new = Event.objects.update_or_create(
                        social_platform_id=event_info["social_platform_id"], defaults=event_info
                    )
                else:
                    _, is_new = Event.objects.update_or_create(
                        name=event_info["name"], start_datetime=event_info["start_datetime"], defaults=event_info
                    )
                if is_new:
                    event_count += 1
    return f"found {len(event_links)} upcoming events for {group.name}; added {event_count} new events"


@shared_task(time_limit=900, max_retries=3, name="web.ingest_future_eventbrite_events")
def ingest_future_eventbrite_events(group_pk) -> str:
    group: TechGroup = TechGroup.objects.get(pk=group_pk)
    if not group:
        return f"group with pk {group_pk} not found"
    event_count = 0
    link: Any = group.links.filter(name=f"{group.name} {group.platform.name} page").distinct()[0]
    eb_group_id: str = link.url.split("-")[-1]
    event_list: list = get_events_for_organization(eb_group_id)
    for item in event_list:
        event_details: dict = get_event_details(item["id"])
        if event_details:
            location_data: dict = event_details["primary_venue"]
            tag_data: list[dict[str, Any]] = event_details["tags"]

            event_data: dict[str, Any] = {
                "group": group,
                "name": item["name"].get("text", "") if item.get("name") else "",
                "description": item["description"].get("text", "") if item.get("description") else "",
                "url": item.get("url", ""),
                "social_platform_id": item.get("id", ""),
                "start_datetime": item["start"].get("utc", "") if item.get("start") else "",
                "end_datetime": item["end"].get("utc", "") if item.get("end") else "",
                "location_name": location_data.get("name", "") if location_data else "",
                "location_address": (
                    location_data.get("address", {}).get("localized_address_display", "") if location_data else ""
                ),
                "map_link": (
                    create_google_map_link(location_data.get("address", {}).get("localized_address_display", ""))
                    if location_data
                    else ""
                ),
            }

            event, is_new = Event.objects.update_or_create(
                group=group, social_platform_id=item["id"], defaults=event_data
            )
            if is_new:
                event_count += 1
            for tag in tag_data:
                obj, _ = Tag.objects.get_or_create(value=tag["display_name"], defaults={"value": tag["display_name"]})
                event.tags.add(obj)
    return f"added {event_count} new events for {group.name}"


@shared_task(time_limit=900, max_retries=3, name="web.launch_group_detail_ingestion")
def launch_group_detail_ingestion() -> str:
    """parent task for ingesting details for all tech groups"""
    for group in TechGroup.objects.filter(enabled=True):
        for link in group.links.filter(name=f"""{group.name} {group.platform} page"""):
            if group.platform.name.lower() == "meetup":
                job = ingest_meetup_group_details.s(group.pk, link.url)
                job.apply_async()
            elif group.platform.name.lower() == "eventbrite":
                job = ingest_eventbrite_organization_details.s(group.pk)
                job.apply_async()
    return f"ingesting details for {TechGroup.objects.filter(enabled=True).count()} tech groups"


@shared_task(time_limit=900, max_retries=0, name="web.launch_meetup_event_ingestion")
def launch_meetup_event_ingestion() -> str:
    """parent task for ingesting future events for tech groups on Meetup"""
    tech_group_list = TechGroup.objects.filter(enabled=True, platform__name="Meetup")
    for group in tech_group_list:
        job = ingest_future_meetup_events.s(group.pk)
        job.apply_async()
    return f"ingesting future events for {len(tech_group_list)} tech groups on Meetup"


@shared_task(time_limit=900, max_retries=0, name="web.launch_eventbrite_event_ingestion")
def launch_eventbrite_event_ingestion() -> str:
    """parent task for ingesting future events for tech groups on Eventbrite"""

    tech_group_list = TechGroup.objects.filter(enabled=True, platform__name="Eventbrite")
    for group in tech_group_list:
        job = ingest_future_eventbrite_events.s(group.pk)
        job.apply_async()
        time.sleep(random.randint(1, 3))  # nosec
    return f"ingesting future events for {len(tech_group_list)} tech groups on Eventbrite"


@shared_task(time_limit=300, max_retries=0, name="web.post_event_to_linkedin")
def post_event_to_linkedin(event_pk: int, is_new: bool) -> str:
    event: Event = Event.objects.get(pk=event_pk)
    if not event:
        return f"Event with pk {event_pk} not found."

    # Ensure LinkedIn API credentials are set
    if not settings.LINKEDIN_ACCESS_TOKEN or not settings.LINKEDIN_ORGANIZATION_URN:
        return "LinkedIn API credentials not configured in settings. Skipping post."

    # Initialize LinkedIn client
    linkedin_client = LinkedInOrganizationClient(
        access_token=settings.LINKEDIN_ACCESS_TOKEN,
        organization_urn=settings.LINKEDIN_ORGANIZATION_URN,
    )

    linkedin_client.post_event(
        event=event,
        is_new=is_new,
    )
    if is_new:
        return f"Event created message for {event.name} posted to LinkedIn successfully."
    return f"Event reminder for {event.name} posted to LinkedIn successfully."


@shared_task(time_limit=300, max_retries=0, name="web.post_event_to_discord")
def post_event_to_discord(event_pk: int, is_new: bool = True) -> str:
    """post an event to Discord via webhook"""
    event: Event = Event.objects.get(pk=event_pk)
    if not event:
        return f"Event with pk {event_pk} not found."

    # Ensure Discord webhook URL is set
    if not settings.DISCORD_WEBHOOK_URL:
        return "Discord webhook URL not configured in settings. Skipping post."

    discord_notifier = DiscordNotifier(webhook_url=settings.DISCORD_WEBHOOK_URL)
    discord_notifier.post_event(
        event=event,
        is_new=is_new,
    )
    if is_new:
        return f"Event created message for {event.name} posted to Discord successfully."
    return f"Event reminder for {event.name} posted to Discord successfully."


@shared_task(time_limit=900, max_retries=3, name="web.launch_reminders_for_tomorrows_events")
def launch_reminders_for_tomorrows_events() -> str:
    """parent task for posting reminders for events happening tomorrow"""

    # Get current time in Pacific Time
    now_pacific: timezone.datetime = convert_to_pacific(timezone.now())

    # Compute "tomorrow" in Pacific Time
    tomorrow_start_pacific: timezone.datetime = (now_pacific + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    tomorrow_end_pacific: timezone.datetime = tomorrow_start_pacific + timedelta(days=1)

    # Convert to UTC
    start_utc: timezone.datetime = convert_to_pacific(tomorrow_start_pacific).astimezone(timezone.utc)
    end_utc: timezone.datetime = convert_to_pacific(tomorrow_end_pacific).astimezone(timezone.utc)

    # Filter events that start anytime tomorrow
    event_list: BaseManager[Event] = Event.objects.filter(
        start_datetime__gte=start_utc, start_datetime__lt=end_utc, group__enabled=True
    )
    for event in event_list:
        # post reminders to Discord
        discord_job: Any = post_event_to_discord.s(event.pk, is_new=False)
        discord_job.apply_async()

        # post reminders to LinkedIn
        linkedin_job: Any = post_event_to_linkedin.s(event.pk, is_new=False)
        linkedin_job.apply_async()

    return f"sending reminders for {event_list.count()} events"


@shared_task(time_limit=900, max_retries=3, name="web.post_event_to_spug_task")
def post_event_to_spug_task(event_pk: int) -> str:
    """post an event to SPUG via their API"""
    event: Event = Event.objects.get(pk=event_pk)
    if not event:
        return f"Event with pk {event_pk} not found."
    spug_url: str | None = getattr(settings, "SPUG_API_URL", None)
    spug_token: str | None = getattr(settings, "SPUG_API_TOKEN", None)
    if not spug_url or not spug_token:
        raise ValueError("SPUG API URL or token not configured in settings.")

    payload: dict[str, Any] = {
        "description": BeautifulSoup(event.description, "html.parser").get_text(),
        "end_date_time": event.end_datetime.isoformat() if event.end_datetime else None,
        "location": event.location_name,
        "name": event.name,
        "start_date_time": event.start_datetime.isoformat() if event.start_datetime else None,
        "url": event.url,
    }
    headers: dict[str, str] = {
        "Authorization": f"Token {spug_token}",
        "Content-Type": "application/json",
    }
    response: requests.Response = requests.post(spug_url, json=payload, headers=headers, timeout=15)
    response.raise_for_status()
    return f"Event {event.name} posted to SPUG successfully."


@shared_task(time_limit=900, max_retries=3, name="web.post_weekly_event_summary_to_discord")
def post_weekly_event_summary_to_discord() -> str:
    """Posts a summary of the week's events to Discord."""
    # Get the current time in Pacific Time
    now_pacific: timezone.datetime = convert_to_pacific(timezone.now())

    # Compute the start and end of the week in Pacific Time
    week_start_pacific: timezone.datetime = now_pacific - timezone.timedelta(days=now_pacific.weekday())
    week_end_pacific: timezone.datetime = week_start_pacific + timezone.timedelta(days=7)

    # Convert to UTC
    start_utc: timezone.datetime = convert_to_pacific(week_start_pacific).astimezone(timezone.utc)
    end_utc: timezone.datetime = convert_to_pacific(week_end_pacific).astimezone(timezone.utc)

    # Filter events that start within the week
    event_list: BaseManager[Event] = Event.objects.filter(
        start_datetime__gte=start_utc, start_datetime__lt=end_utc, group__enabled=True
    )
    if not event_list.exists():
        return "No events found for the week."

    # Build and send the summary message to Discord
    discord_notifier = DiscordNotifier(webhook_url=settings.DISCORD_WEBHOOK_URL)
    discord_notifier.post_weekly_summary(event_list=event_list)

    return "Weekly event summary posted to Discord successfully."
