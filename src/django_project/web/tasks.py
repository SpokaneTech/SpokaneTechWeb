import logging
import time

from celery import shared_task
from web.models import Event, TechGroup
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
    group = TechGroup.objects.get(pk=group_pk)
    group.description = get_group_description(url)
    group.save()
    return f"updated details for {group.name}"


@shared_task(time_limit=900, max_retries=3, name="web.ingest_future_meetup_events")
def ingest_future_meetup_events(group_pk):
    group = TechGroup.objects.get(pk=group_pk)
    if not group:
        return f"group with pk {group_pk} not found"
    event_count = 0
    for link in group.links.filter(name=f"""{group.name} {group.platform} page""").distinct():
        event_links = get_event_links(f"{link.url}events/?type=upcoming")
        for event_link in event_links:
            event_info = get_event_information(event_link)
            event_info["group"] = group
            if event_info:
                event_count += 1
                if event_info["social_platform_id"]:
                    Event.objects.update_or_create(
                        social_platform_id=event_info["social_platform_id"], defaults=event_info
                    )
                else:
                    Event.objects.update_or_create(
                        name=event_info["name"], start_datetime=event_info["start_datetime"], defaults=event_info
                    )
    return f"added {event_count}/{len(event_links)} for {group.name}"


@shared_task(time_limit=900, max_retries=3, name="web.launch_group_detail_ingestion")
def launch_group_detail_ingestion():
    """parent task for ingesting details for all tech groups"""
    tech_group_list = TechGroup.objects.filter(enabled=True, platform__name="Meetup")
    for group in tech_group_list:
        for link in group.links.filter(name=f"""{group.name} {group.platform} page"""):
            job = ingest_meetup_group_details.s(group.pk, link.url)
            job.apply_async()


@shared_task(time_limit=900, max_retries=0, name="web.launch_event_ingestion")
def launch_event_ingestion():
    """parent task for ingesting future events for all tech groups"""
    tech_group_list = TechGroup.objects.filter(enabled=True, platform__name="Meetup")
    for group in tech_group_list:
        job = ingest_future_meetup_events.s(group.pk)
        job.apply_async()
