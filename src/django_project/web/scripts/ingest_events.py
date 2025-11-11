import time

from django.db.models.manager import BaseManager
from web.models import Event, TechGroup
from web.tasks import ingest_future_eventbrite_events, ingest_future_meetup_events


def get_eventbright_events():
    tech_group_list = TechGroup.objects.filter(enabled=True, platform__name="Eventbrite")
    for group in tech_group_list:
        print("INFO: getting upcoming events for ", group.name)
        job = ingest_future_eventbrite_events.s(group.pk)
        job.apply()
        time.sleep(1)


def get_meetup_events() -> None:
    tech_group_list = TechGroup.objects.filter(enabled=True, platform__name="Meetup")
    for group in tech_group_list:
        print("INFO: getting upcoming events for ", group.name)
        job = ingest_future_meetup_events.s(group.pk)
        job.apply()


def run():
    get_eventbright_events()
    get_meetup_events()
