from web.models import Event, TechGroup
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


def ingest_eventbright_data():
    groups = TechGroup.objects.filter(enabled=True, platform__name="Eventbrite")
    for group in groups:
        for link in group.links.filter(name=f"""{group.name} {group.platform} page""").distinct():
            print(f"INFO: ingest Eventbright.com events for {group.name}")


def run():
    # ingest_meetup_data()
    ingest_eventbright_data()
