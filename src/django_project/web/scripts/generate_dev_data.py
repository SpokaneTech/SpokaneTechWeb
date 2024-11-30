import datetime
import random

import faker
from django.utils import timezone
from web.models import Event, SocialPlatform, TechGroup


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
    f = faker.Faker()
    data_list = [
        {
            "name": "Business Brew",
            "icon": """<i class="fa-solid fa-mug-saucer"></i>""",
            "platform": "Eventbright",
        },
        {
            "name": "Greater Spokane Inc",
            "icon": """<i class="fa-solid fa-city"></i>""",
            "platform": "Other",
        },
        {
            "name": "Ignite Northwest",
            "icon": """<i class="fa-solid fa-fire-flame-curved"></i>""",
            "platform": "Eventbright",
        },
        {
            "name": "INCH360",
            "icon": """<i class="fa-solid fa-shield-halved"></i>""",
            "platform": "Eventbright",
        },
        {
            "name": "SP3NW",
            "icon": """<i class="fa-solid fa-business-time"></i>""",
            "platform": "Other",
        },
        {
            "name": "Spokane DevOps Meetup",
            "icon": """<i class="fa-solid fa-code-pull-request"></i>""",
            "platform": "Meetup",
        },
        {
            "name": "Spokane Go Users Group",
            "icon": """<i class="fa-brands fa-golang"></i>""",
            "platform": "Meetup",
        },
        {
            "name": "Spokane .NET Users Group",
            "icon": """<i class="fa-brands fa-windows"></i>""",
            "platform": "Meetup",
        },
        {
            "name": "spokaneOS",
            "icon": """<i class="fa-brands fa-apple"></i>""",
            "platform": "Discord",
        },
        {
            "name": "Spokane Python User Group",
            "icon": """<i class="fa-brands fa-python"></i>""",
            "platform": "Meetup",
        },
        {
            "name": "Spokane Rust User Group",
            "icon": """<i class="fa-brands fa-rust"></i>""",
            "platform": "Meetup",
        },
        {
            "name": "Spokane Tech Community",
            "icon": """<i class="fa-solid fa-people-roof"></i>""",
            "platform": "Meetup",
        },
        {
            "name": "Spokane UX",
            "icon": """<i class="fa-solid fa-pen-ruler"></i>""",
            "platform": "Meetup",
        },
        {
            "name": "Spokane Linux User Group",
            "icon": """<i class="fa-brands fa-linux"></i>""",
            "platform": "Meetup",
        },
    ]
    for data in data_list:
        data["platform"], _ = SocialPlatform.objects.get_or_create(name=data["platform"])
        data["description"] = f.paragraph()
        TechGroup.objects.update_or_create(name=data["name"], defaults=data)


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
            "base_url": None,
        },
    ]
    for data in data_list:
        SocialPlatform.objects.update_or_create(name=data["name"], defaults=data)


def run():
    create_social_platforms()
    create_groups()
    create_events(qty=10)
