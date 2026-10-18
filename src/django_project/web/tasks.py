from __future__ import annotations

import logging
import random
import re
import time
from datetime import timedelta
from datetime import timezone as datetime_timezone
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from celery import shared_task
from django.conf import settings
from django.db.models.manager import BaseManager
from django.utils import timezone

from web.event_ingestion import save_source_event
from web.models import Event, IntegrationCredential, Link, TechGroup
from web.utilities.dt_utils import convert_to_pacific
from web.utilities.event_images import eventbrite_image_url
from web.utilities.event_status import source_event_status
from web.utilities.notifiers.discord import DiscordNotifier
from web.utilities.notifiers.linkedin import LinkedInOrganizationClient
from web.utilities.scrapers.eventbrite import (
    create_google_map_link,
    get_event_details,
    get_event_record,
    get_events_for_organization,
    get_organization_details,
)
from web.utilities.scrapers.meetup import (
    get_event_information,
    get_event_links,
    get_group_description,
)

logger = logging.getLogger(__name__)


def _get_eventbrite_organization_id(url: str) -> str | None:
    """Extract the numeric organizer ID from an Eventbrite organization URL."""
    parsed_url = urlparse(url)
    if parsed_url.hostname not in {"eventbrite.com", "www.eventbrite.com"}:
        return None
    path_parts = parsed_url.path.rstrip("/").split("/")
    if len(path_parts) != 3 or path_parts[1] != "o":
        return None
    organization_slug = path_parts[2]
    organization_id = organization_slug.rsplit("-", maxsplit=1)[-1]
    return organization_id if organization_id.isdigit() else None


@shared_task(time_limit=30, max_retries=0, name="web.test_task")
def test_task() -> str:
    logger.info("test task starting")
    time.sleep(3)
    logger.info("test task completed")
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
    eb_group_id = _get_eventbrite_organization_id(link.url)
    if not eb_group_id:
        return f"invalid Eventbrite organization URL for {group.name}"

    organization_details = get_organization_details(eb_group_id)
    description = organization_details["long_description"]["text"]
    if description and group.description != description:
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
def ingest_future_meetup_events(group_pk, *, synchronous_images: bool = False) -> str:
    group = TechGroup.objects.get(pk=group_pk)
    links = group.links.filter(name=f"{group.name} {group.platform.name} page").distinct()
    if not links:
        return f"no {group.platform.name} links found for {group.name}"
    discovered: set[str] = set()
    for link in links:
        try:
            discovered.update(url for url in get_event_links(link.url) if re.search(r"/events/(\d+)/", url))
        except Exception:
            logger.exception("Meetup discovery failed for group %s; rechecking stored events", group.pk)
    known: dict[str, int] = {}
    for event in Event.objects.filter(group=group, start_datetime__gte=timezone.now()):
        url = event.url
        if not url and event.social_platform_id.isdigit():
            base = re.sub(r"/events/?$", "", links[0].url.rstrip("/"))
            url = f"{base}/events/{event.social_platform_id}/"
        if url and urlparse(url).hostname in {"meetup.com", "www.meetup.com"}:
            known[url] = event.pk
    event_count = 0
    for url in sorted(discovered | known.keys()):
        try:
            info = dict(get_event_information(url) or {})
        except Exception:
            logger.exception("Meetup detail fetch failed for group %s; preserving stored event", group.pk)
            continue
        if not info:
            continue
        image_url = info.pop("image_url", "")
        tags = info.pop("tags", None)
        if not info.pop("tags_complete", True):
            tags = None
        complete = info.pop("location_complete", any(info.get(key) for key in ("location_name", "location_address")))
        _, is_new = save_source_event(
            group,
            info,
            tags=tags,
            image_url=image_url,
            location_complete=complete,
            synchronous_images=synchronous_images,
            existing_pk=known.get(url),
        )
        event_count += int(is_new)
    return f"found {len(discovered)} upcoming events for {group.name}; added {event_count} new events"


def _save_eventbrite_snapshot(
    group: TechGroup,
    item: dict[str, Any],
    details: dict[str, Any],
    *,
    synchronous_images: bool = False,
    existing_pk: int | None = None,
) -> tuple[Event | None, bool]:
    # Detail responses take precedence; absent keys in a partial response do not erase list data.
    snapshot = {**item, **details}
    data: dict[str, Any] = {}
    for key in ("name", "description"):
        if key in snapshot:
            value = snapshot[key]
            data[key] = value.get("text", "") if isinstance(value, dict) else value
    for key in ("start", "end"):
        if snapshot.get(key):
            data[f"{key}_datetime"] = snapshot[key].get("utc")
    for key, field in (("url", "url"), ("id", "social_platform_id")):
        if key in snapshot:
            data[field] = str(snapshot[key])
    statuses = [source_event_status(details), source_event_status(item)]
    status = "cancelled" if "cancelled" in statuses else next((value for value in statuses if value), None)
    if status:
        data["status"] = status
    venue = snapshot.get("primary_venue") or snapshot.get("venue") or {}
    address = venue.get("address") or {}
    location_address = address.get("localized_address_display", "")
    name = venue.get("name") or ""
    online = snapshot.get("online_event") is True or name.casefold() in {"online", "online event"}
    data.update(
        location_name="Online event" if online and not name else name,
        location_address="" if online else location_address,
        map_link=create_google_map_link(location_address) if location_address and not online else "",
    )
    raw_tags = snapshot.get("tags")
    tags = (
        [tag.get("display_name") for tag in raw_tags if isinstance(tag, dict)] if isinstance(raw_tags, list) else None
    )
    return save_source_event(
        group,
        data,
        tags=tags,
        image_url=eventbrite_image_url(details) or eventbrite_image_url(item),
        location_complete=online or bool(name and location_address),
        synchronous_images=synchronous_images,
        existing_pk=existing_pk,
    )


@shared_task(time_limit=900, max_retries=3, name="web.ingest_future_eventbrite_events")
def ingest_future_eventbrite_events(group_pk, *, synchronous_images: bool = False) -> str:
    group = TechGroup.objects.get(pk=group_pk)
    link = group.links.filter(name=f"{group.name} {group.platform.name} page").distinct().first()
    if not link:
        return f"no {group.platform.name} links found for {group.name}"
    organizer_id = _get_eventbrite_organization_id(link.url)
    if not organizer_id:
        return f"invalid Eventbrite organization URL for {group.name}"
    known = {
        event.social_platform_id: event.pk
        for event in Event.objects.filter(group=group, start_datetime__gte=timezone.now()).exclude(
            social_platform_id=""
        )
    }
    try:
        event_list = get_events_for_organization(organizer_id)
    except Exception:
        logger.exception("Eventbrite discovery failed for group %s; rechecking stored events", group.pk)
        event_list = []
    event_count = 0
    checked: set[str] = set()
    for item in event_list:
        event_id = str(item.get("id") or "")
        if not event_id or event_id in checked:
            continue
        checked.add(event_id)
        try:
            details = get_event_details(event_id)
        except Exception:
            logger.exception("Eventbrite detail fetch failed for event %s; preserving stored details", event_id)
            continue
        # An empty detail response is not evidence of deletion or cancellation.
        if not details:
            continue
        _, is_new = _save_eventbrite_snapshot(
            group,
            item,
            details,
            synchronous_images=synchronous_images,
            existing_pk=known.get(event_id),
        )
        event_count += int(is_new)
    for event_id in known.keys() - checked:
        try:
            snapshot = get_event_record(event_id)
        except Exception:
            logger.exception("Eventbrite recheck failed for event %s; retaining current status", event_id)
            continue
        if snapshot:
            _save_eventbrite_snapshot(
                group,
                {"id": event_id},
                snapshot,
                synchronous_images=synchronous_images,
                existing_pk=known[event_id],
            )
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
def post_event_to_linkedin(
    event_pk: int, is_new: bool, *, change_message: str | None = None, change_version: int | None = None
) -> str:
    event: Event = Event.objects.get(pk=event_pk)
    if not event:
        return f"Event with pk {event_pk} not found."

    if not settings.POST_TO_LINKEDIN:
        return f"POST_TO_LINKEDIN is False. Skipping LinkedIn post for event with pk {event_pk}."

    linkedin_credential = IntegrationCredential.objects.filter(provider="linkedin").first()
    access_token = linkedin_credential.access_token if linkedin_credential else settings.LINKEDIN_ACCESS_TOKEN
    refresh_token = linkedin_credential.refresh_token if linkedin_credential else settings.LINKEDIN_REFRESH_TOKEN

    if not settings.LINKEDIN_ORGANIZATION_URN:
        return f"LinkedIn organization URN not configured in settings. Skipping post for event with pk {event_pk}."

    if not access_token and not (refresh_token and settings.LINKEDIN_CLIENT_ID and settings.LINKEDIN_CLIENT_SECRET):
        return "LinkedIn API credentials not configured in settings. Skipping post."

    if change_version is not None and event.change_version != change_version:
        return "Event change message is obsolete."
    if event.is_cancelled and not change_message:
        return "Event is cancelled. Skipping LinkedIn post."

    # Initialize LinkedIn client
    linkedin_client = LinkedInOrganizationClient(
        access_token=access_token,
        organization_urn=settings.LINKEDIN_ORGANIZATION_URN,
        client_id=settings.LINKEDIN_CLIENT_ID,
        client_secret=settings.LINKEDIN_CLIENT_SECRET,
        refresh_token=refresh_token,
        env_path=getattr(settings, "ENV_PATH", None),
        credential=linkedin_credential,
    )

    if change_message:
        linkedin_client.post_organization_post(commentary=change_message[:3000])
        return f"Event change for {event.name} posted to LinkedIn successfully."
    linkedin_client.post_event(event=event, is_new=is_new)
    if is_new:
        return f"Event created message for {event.name} posted to LinkedIn successfully."
    return f"Event reminder for {event.name} posted to LinkedIn successfully."


@shared_task(time_limit=300, max_retries=0, name="web.post_event_to_discord")
def post_event_to_discord(
    event_pk: int, is_new: bool = True, *, change_message: str | None = None, change_version: int | None = None
) -> str:
    """post an event to Discord via webhook"""
    if not settings.POST_TO_DISCORD:
        return f"POST_TO_DISCORD is False. Skipping Discord post for event with pk {event_pk}."

    event: Event = Event.objects.get(pk=event_pk)
    if not event:
        return f"Event with pk {event_pk} not found."

    if change_version is not None and event.change_version != change_version:
        return "Event change message is obsolete."
    if event.is_cancelled and not change_message:
        return "Event is cancelled. Skipping Discord post."

    # Ensure Discord webhook URL is set
    if not settings.DISCORD_WEBHOOK_URL:
        return "Discord webhook URL not configured in settings. Skipping post."

    discord_notifier = DiscordNotifier(webhook_url=settings.DISCORD_WEBHOOK_URL)
    if change_message:
        payload = {"content": change_message[:1900], "allowed_mentions": {"parse": []}}
        discord_notifier.send_message(payload)
        if event.group and event.group.discord_webhook_url:
            discord_notifier.send_message(payload, url=event.group.discord_webhook_url)
        return f"Event change for {event.name} posted to Discord successfully."
    discord_notifier.post_event(event=event, is_new=is_new)
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
    start_utc: timezone.datetime = convert_to_pacific(tomorrow_start_pacific).astimezone(datetime_timezone.utc)
    end_utc: timezone.datetime = convert_to_pacific(tomorrow_end_pacific).astimezone(datetime_timezone.utc)

    # Filter events that start anytime tomorrow
    event_list: BaseManager[Event] = Event.objects.filter(
        start_datetime__gte=start_utc, start_datetime__lt=end_utc, group__enabled=True, status=Event.Status.ACTIVE
    )
    for event in event_list:
        # post reminders to Discord
        if settings.POST_TO_DISCORD:
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
    if event.is_cancelled:
        return "Event is cancelled. Skipping SPUG post."
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
    if not settings.POST_TO_DISCORD:
        return "POST_TO_DISCORD is False. Skipping weekly Discord summary."
    if not settings.DISCORD_WEBHOOK_URL:
        return "Discord webhook URL not configured in settings. Skipping post."

    # Get the current time in Pacific Time
    now_pacific: timezone.datetime = convert_to_pacific(timezone.now())

    # Compute the start and end of the week in Pacific Time
    week_start_pacific: timezone.datetime = now_pacific - timezone.timedelta(days=now_pacific.weekday())
    week_end_pacific: timezone.datetime = week_start_pacific + timezone.timedelta(days=7)

    # Convert to UTC
    start_utc: timezone.datetime = convert_to_pacific(week_start_pacific).astimezone(datetime_timezone.utc)
    end_utc: timezone.datetime = convert_to_pacific(week_end_pacific).astimezone(datetime_timezone.utc)

    # Filter events that start within the week
    event_list: BaseManager[Event] = Event.objects.filter(
        start_datetime__gte=start_utc, start_datetime__lt=end_utc, group__enabled=True, status=Event.Status.ACTIVE
    ).select_related("group")
    if not event_list.exists():
        return "No events found for the week."

    # Build and send the summary message to Discord
    discord_notifier = DiscordNotifier(webhook_url=settings.DISCORD_WEBHOOK_URL)
    discord_notifier.post_weekly_summary(event_list=event_list)

    return "Weekly event summary posted to Discord successfully."
