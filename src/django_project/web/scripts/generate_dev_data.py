import datetime
import random

import faker
from django.utils import timezone
from web.models import Event, Link, SocialPlatform, TechGroup
from web.utilities.scrapers.meetup import (
    get_event_information,
    get_event_links,
    get_group_description,
)


def create_events(qty: int = 1) -> None:
    """Create some Event entries"""
    print("INFO: creating Event entries")
    f = faker.Faker()
    current_time = timezone.now()

    for i in range(qty):
        data = {
            "name": f.sentence(),
            "description": f.paragraph(random.randint(10, 50)),
            "date_time": current_time + datetime.timedelta(days=random.randint(1, 90)),
            "duration": datetime.timedelta(hours=random.randint(1, 3)),
            "location": f.address(),
            "url": f.uri(),
            "group": TechGroup.objects.get_random_row(),
        }
        Event.objects.create(**data)


def create_groups() -> None:
    """Create some TechGroup entries"""
    print("INFO: creating TechGroup entries")
    data_list = [
        {
            "name": "Business Brew",
            "icon": """<i class="fa-solid fa-mug-saucer"></i>""",
            "platform": "Eventbright",
            "platform page": "",
        },
        {
            "name": "Greater Spokane Inc",
            "icon": """<i class="fa-solid fa-city"></i>""",
            "platform": "Other",
            "platform page": "",
        },
        {
            "name": "Ignite Northwest",
            "icon": """<i class="fa-solid fa-fire-flame-curved"></i>""",
            "platform": "Eventbright",
            "platform page": "",
        },
        {
            "name": "INCH360",
            "icon": """<i class="fa-solid fa-shield-halved"></i>""",
            "platform": "Eventbright",
            "platform page": "",
        },
        {
            "name": "SP3NW",
            "icon": """<i class="fa-solid fa-business-time"></i>""",
            "platform": "Other",
            "platform page": "",
        },
        {
            "name": "Spokane DevOps Meetup",
            "icon": """<i class="fa-solid fa-code-pull-request"></i>""",
            "platform": "Meetup",
            "platform page": "https://www.meetup.com/spokane-devops-meetup/",
        },
        {
            "name": "Spokane Go Users Group",
            "icon": """<i class="fa-brands fa-golang"></i>""",
            "platform": "Meetup",
            "platform page": "https://www.meetup.com/spokane-go-users-group/",
        },
        {
            "name": "Spokane .NET Users Group",
            "icon": """<i class="fa-brands fa-windows"></i>""",
            "platform": "Meetup",
            "platform page": "https://www.meetup.com/spokane-net-user-group/",
        },
        {
            "name": "spokaneOS",
            "icon": """<i class="fa-brands fa-apple"></i>""",
            "platform": "Discord",
            "platform page": "",
        },
        {
            "name": "Spokane Python User Group",
            "icon": """<i class="fa-brands fa-python"></i>""",
            "platform": "Meetup",
            "platform page": "https://www.meetup.com/python-spokane/",
        },
        {
            "name": "Spokane Rust User Group",
            "icon": """<i class="fa-brands fa-rust"></i>""",
            "platform": "Meetup",
            "platform page": "https://www.meetup.com/spokane-rust/",
        },
        {
            "name": "Spokane Tech Community",
            "icon": """<i class="fa-solid fa-people-roof"></i>""",
            "platform": "Meetup",
            "platform page": "https://www.meetup.com/meetup-group-sdeepfce/",
        },
        {
            "name": "Spokane UX",
            "icon": """<i class="fa-solid fa-pen-ruler"></i>""",
            "platform": "Meetup",
            "platform page": "https://www.meetup.com/Spokane-UX/",
        },
        {
            "name": "Spokane Linux User Group",
            "icon": """<i class="fa-brands fa-linux"></i>""",
            "platform": "Meetup",
            "platform page": "https://www.meetup.com/spolug/",
        },
    ]
    for data in data_list:
        data["platform"], _ = SocialPlatform.objects.get_or_create(name=data["platform"])
        # data["description"] = f.paragraph()
        platform_page = data.pop("platform page")
        tech_group, _ = TechGroup.objects.update_or_create(name=data["name"], defaults=data)
        if platform_page:
            link_data = {
                "name": f"""{data["name"]} {data["platform"]} page""",
                "description": f"""{data["platform"]} page for {data["name"]}""",
                "url": platform_page,
            }
            link, _ = Link.objects.get_or_create(
                name=link_data["name"],
                description=link_data["description"],
                url=link_data["url"],
                defaults=link_data,
            )
            if not tech_group.links.filter(name=link.name).exists():
                tech_group.links.add(link)


def create_social_platforms() -> None:
    """Create some SocialPlatform entries"""
    print("INFO: creating SocialPlatform entries")
    data_list = [
        {
            "name": "Discord",
            "base_url": "www.discord.com",
        },
        {
            "name": "EventBright",
            "base_url": "www.eventbright.com",
        },
        {
            "name": "Facebook",
            "base_url": "www.facebook.com",
        },
        {
            "name": "LinkedIn",
            "base_url": "www.linkedin.com",
        },
        {
            "name": "Meetup",
            "base_url": "www.meetup.com",
        },
        {
            "name": "Other",
        },
    ]
    for data in data_list:
        SocialPlatform.objects.update_or_create(name=data["name"], defaults=data)


def ingest_meetup_data():
    """Ingest data from group meetup pages"""
    groups = TechGroup.objects.filter(enabled=True, platform__name="Meetup")

    for group in groups:
        for link in group.links.filter(name=f"""{group.name} {group.platform} page""").distinct():
            # get group description from meetup
            group.description = get_group_description(link)
            group.save()

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


def run():
    create_social_platforms()
    create_groups()
    ingest_meetup_data()
