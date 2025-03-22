import logging
import re
import time

from celery import shared_task
from web.models import Event, Link, Tag, TechGroup
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
def test_task():
    logging.info("test task starting")
    time.sleep(3)
    logging.info("test task completed")
    return "test task completed!"


@shared_task(time_limit=900, max_retries=3, name="web.ingest_meetup_group_details")
def ingest_meetup_group_details(group_pk, url: str):
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
def ingest_eventbrite_organization_details(group_pk):
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
def ingest_future_meetup_events(group_pk):
    group = TechGroup.objects.get(pk=group_pk)
    if not group:
        return f"group with pk {group_pk} not found"
    event_links = []
    event_count = 0
    for link in group.links.filter(name=f"{group.name} {group.platform.name} page").distinct():
        event_count = 0
        event_links = get_event_links(f"{link.url}events/?type=upcoming")

        # filter event links for future recurring events. Meetup uses a numeric event id in the url for upcoming events
        # and a alphanumeric event id for recurring events. This is causing duplicate events to be added to the database.
        numeric_event_pattern = re.compile(r"/events/(\d+)/")
        event_links = [url for url in event_links if numeric_event_pattern.search(url)]

        for event_link in event_links:
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
def ingest_future_eventbrite_events(group_pk):
    group = TechGroup.objects.get(pk=group_pk)
    if not group:
        return f"group with pk {group_pk} not found"
    event_count = 0
    link = group.links.filter(name=f"{group.name} {group.platform.name} page").distinct()[0]
    eb_group_id = link.url.split("-")[-1]
    event_list = get_events_for_organization(eb_group_id)
    for item in event_list:
        event_details = get_event_details(item["id"])
        location_data = event_details["primary_venue"]
        tag_data = event_details["tags"]

        event_data = {
            "group": group,
            "name": item["name"]["text"],
            "description": item["description"]["text"],
            "url": item["url"],
            "social_platform_id": item["id"],
            "start_datetime": item["start"]["utc"],
            "end_datetime": item["end"]["utc"],
            "location_name": location_data["name"],
            "location_address": location_data["address"]["localized_address_display"],
            "map_link": create_google_map_link(location_data["address"]["localized_address_display"]),
        }

        event, is_new = Event.objects.update_or_create(group=group, social_platform_id=item["id"], defaults=event_data)
        if is_new:
            event_count += 1
        for tag in tag_data:
            obj = Tag.objects.get_or_create(value=tag["display_name"], defaults={"value": tag["display_name"]})[0]
            event.tags.add(obj)
    return f"added {event_count} new events for {group.name}"


@shared_task(time_limit=900, max_retries=3, name="web.launch_group_detail_ingestion")
def launch_group_detail_ingestion():
    """parent task for ingesting details for all tech groups"""
    for group in TechGroup.objects.filter(enabled=True):
        for link in group.links.filter(name=f"""{group.name} {group.platform} page"""):
            if group.platform.name.lower() == "meetup":
                job = ingest_meetup_group_details.s(group.pk, link.url)
                job.apply_async()
            elif group.platform.name.lower() == "eventbrite":
                job = ingest_eventbrite_organization_details.s(group.pk)
                job.apply_async()


@shared_task(time_limit=900, max_retries=0, name="web.launch_meetup_event_ingestion")
def launch_meetup_event_ingestion():
    """parent task for ingesting future events for tech groups on Meetup"""
    tech_group_list = TechGroup.objects.filter(enabled=True, platform__name="Meetup")
    for group in tech_group_list:
        job = ingest_future_meetup_events.s(group.pk)
        job.apply_async()


@shared_task(time_limit=900, max_retries=0, name="web.launch_eventbrite_event_ingestion")
def launch_eventbrite_event_ingestion():
    """parent task for ingesting future events for tech groups on Eventbrite"""

    tech_group_list = TechGroup.objects.filter(enabled=True, platform__name="Eventbrite")
    for group in tech_group_list:
        job = ingest_future_eventbrite_events.s(group.pk)
        job.apply_async()
