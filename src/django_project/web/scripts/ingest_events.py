from web.models import Event, TechGroup
from web.tasks import (
    ingest_eventbrite_organization_details,
    ingest_future_eventbrite_events,
    ingest_future_meetup_events,
    ingest_meetup_group_details,
)
from web.utilities.scrapers.meetup import (
    get_event_information,
    get_event_links,
    get_group_description,
)


def ingest_meetup_data():
    """Ingest data from group meetup pages"""
    groups = TechGroup.objects.filter(enabled=True, platform__name="Meetup")
    for group in groups:
        for link in group.links.filter(name=f"""{group.name} {group.platform} page""").distinct():

            # get upcoming events from meetup
            print(f"INFO: ingest Meetup.com events for {group.name}")
            event_links = get_event_links(f"{link.url}events/?type=upcoming")
            for event_link in event_links:
                event_info = get_event_information(event_link)
                event_info["group"] = group
                if event_info:
                    print(f"INFO: \tsaving {event_info['name']} - {event_info['start_datetime']}")
                    if event_info["social_platform_id"]:
                        Event.objects.update_or_create(
                            social_platform_id=event_info["social_platform_id"], defaults=event_info
                        )
                    else:
                        Event.objects.update_or_create(
                            name=event_info["name"], start_datetime=event_info["start_datetime"], defaults=event_info
                        )


def get_eventbright_events():
    tech_group_list = TechGroup.objects.filter(enabled=True, platform__name="Eventbrite")
    for group in tech_group_list:
        job = ingest_future_eventbrite_events.s(group.pk)
        job.apply()


def get_meetup_events():
    tech_group_list = TechGroup.objects.filter(enabled=True, platform__name="Meetup")
    for group in tech_group_list:
        job = ingest_future_meetup_events.s(group.pk)
        job.apply()


def get_eventbrite_organization_details():
    for group in TechGroup.objects.filter(enabled=True, platform__name="Eventbrite"):
        job = ingest_eventbrite_organization_details.s(group.pk)
        job.apply()


def get_meetup_group_details():
    for group in TechGroup.objects.filter(enabled=True, platform__name="Meetup"):
        link = group.links.filter(name=f"{group.name} {group.platform.name} page").distinct()[0]
        job = ingest_meetup_group_details.s(group.pk, link.url)
        job.apply()


def run():
    get_eventbright_events()
    get_meetup_events()
    get_eventbrite_organization_details()
    get_meetup_group_details()
