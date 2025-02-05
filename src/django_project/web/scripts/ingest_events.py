from web.models import Event, TechGroup
from web.tasks import ingest_future_eventbrite_events, ingest_future_meetup_events


def get_eventbright_events():
    tech_group_list = TechGroup.objects.filter(enabled=True, platform__name="Eventbrite")
    for group in tech_group_list:
        job = ingest_future_eventbrite_events.s(group.pk)
        job.apply()


def get_meetup_events():
    tech_group_list = TechGroup.objects.filter(enabled=True)
    for group in tech_group_list:
        job = ingest_future_meetup_events.s(group.pk)
        job.apply()


def run():
    get_eventbright_events()
    get_meetup_events()
