import logging
import random
import re
import time
from datetime import timedelta
from typing import Any
from zoneinfo import ZoneInfo

from celery import shared_task
from django.conf import settings
from django.utils import timezone
from web.models import Event, Link, Tag, TechGroup
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

PACIFIC = ZoneInfo("America/Los_Angeles")


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
    group = TechGroup.objects.get(pk=group_pk)
    group_details = get_group_description(url)
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
        ingest_links: list = [
            url for url in get_event_links(f"{link.url}events/?type=upcoming") if numeric_event_pattern.search(url)
        ]
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

    # If the event is new, prepare the LinkedIn post data
    if is_new:
        linkedin_client.post_event_created(
            name=event.name,
            url=event.url,
            description=event.description,
            date_time=event.start_datetime,
            location_name=event.location_name,
        )
    return "Event posted to LinkedIn successfully."


@shared_task(time_limit=300, max_retries=0, name="web.post_event_reminder_to_linkedin")
def post_event_reminder_to_linkedin(event_pk: int) -> str:
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

    linkedin_client.post_event_reminder(
        name=event.name,
        date_time=event.start_datetime,
        url=event.url,
        location_name=event.location_name,
    )
    return f"Event reminder for {event.name} posted to LinkedIn successfully."


@shared_task(time_limit=900, max_retries=3, name="web.launch_event_reminders")
def launch_event_reminders() -> str:
    """parent task for ingesting details for all tech groups"""
    count: int = 0

    # Get current time in Pacific Time
    now_pacific: timezone.datetime = timezone.now().astimezone(PACIFIC)

    # Compute "tomorrow" in Pacific Time
    tomorrow_start_pacific: timezone.datetime = (now_pacific + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    tomorrow_end_pacific: timezone.datetime = tomorrow_start_pacific + timedelta(days=1)

    # Convert to UTC
    start_utc: timezone.datetime = tomorrow_start_pacific.astimezone(timezone.utc)
    end_utc: timezone.datetime = tomorrow_end_pacific.astimezone(timezone.utc)

    # Filter events that start anytime tomorrow
    for event in Event.objects.filter(start_datetime__gte=start_utc, start_datetime__lt=end_utc, group__enabled=True):
        job: Any = post_event_reminder_to_linkedin.s(event.pk)
        job.apply_async()
        count += 1
    return f"sending reminders for {count} events"
