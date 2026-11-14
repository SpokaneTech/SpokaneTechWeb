import time

from web.models import TechGroup
from web.tasks import (
    ingest_future_eventbrite_events,
    ingest_future_luma_events,
    ingest_future_meetup_events,
)


def get_eventbrite_events():
    tech_group_list = TechGroup.objects.filter(
        enabled=True, platform__name="Eventbrite"
    )
    for group in tech_group_list:
        print("INFO: getting upcoming events for ", group.name)
        job = ingest_future_eventbrite_events.s(group.pk, synchronous_images=True)
        job.apply(throw=True)
        time.sleep(1)


def get_meetup_events() -> None:
    tech_group_list = TechGroup.objects.filter(enabled=True, platform__name="Meetup")
    for group in tech_group_list:
        print("INFO: getting upcoming events for ", group.name)
        job = ingest_future_meetup_events.s(group.pk, synchronous_images=True)
        job.apply(throw=True)


def get_luma_events() -> None:
    tech_group_list = TechGroup.objects.filter(enabled=True, platform__name="Luma")
    for group in tech_group_list:
        print("INFO: getting upcoming events for ", group.name)
        job = ingest_future_luma_events.s(group.pk)
        job.apply(throw=True)


def run():
    get_eventbrite_events()
    get_meetup_events()
    get_luma_events()
