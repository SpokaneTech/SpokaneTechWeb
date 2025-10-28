from web.models import Link, SocialPlatform, TechGroup
from web.tasks import (
    ingest_eventbrite_organization_details,
    ingest_meetup_group_details,
)


def create_groups() -> None:
    """Create some TechGroup entries"""
    print("INFO: creating TechGroup entries")
    data_list = [
        {
            "name": "Business Brew",
            "icon": """<i class="fa-solid fa-mug-saucer"></i>""",
            "platform": "Eventbrite",
            "platform page": "https://www.eventbrite.com/o/business-brew-80655815043",
        },
        {
            "name": "Ignite Northwest",
            "icon": """<i class="fa-solid fa-fire-flame-curved"></i>""",
            "platform": "Eventbrite",
            "platform page": "https://www.eventbrite.com/o/ignite-northwest-26948291755",
        },
        {
            "name": "INCH360",
            "icon": """<i class="fa-solid fa-shield-halved"></i>""",
            "platform": "Eventbrite",
            "platform page": "https://www.eventbrite.com/o/inch360-72020528223",
        },
        {
            "name": "LaunchPad INW",
            "icon": """<i class="fa-solid fa-rocket"></i>""",
            "platform": "Eventbrite",
            "platform page": "https://www.eventbrite.com/o/launchpad-inw-637389713",
        },
        {
            "name": "Innovation Collective",
            "icon": """<i class="fa-regular fa-lightbulb"></i>""",
            "platform": "Eventbrite",
            "platform page": "https://www.eventbrite.com/o/innovation-collective-coeur-dalene-id-45018125323",
        },
        {
            "name": "SP3NW",
            "icon": """<i class="fa-solid fa-business-time"></i>""",
            "platform": "Eventbrite",
            "platform page": "https://www.eventbrite.com/o/sp3nw-33773699489",
        },
        {
            "name": "Spokane Small Business Podcast",
            "icon": """<i class="fa-solid fa-podcast"></i>""",
            "platform": "Eventbrite",
            "platform page": "https://www.eventbrite.com/o/spokane-small-business-podcast-103647763911",
        },
        {
            "name": "FUEL Coworking",
            "icon": """<i class="fa-solid fa-gas-pump"></i>""",
            "platform": "Eventbrite",
            "platform page": "https://www.eventbrite.com/o/fuel-coworking-110692675491",
        },
        {
            "name": "IntelliTect",
            "icon": """<i class="fa-solid fa-globe"></i>""",
            "platform": "Eventbrite",
            "platform page": "https://www.eventbrite.com/o/intellitect-114361599431",
        },
        {
            "name": "Greater Spokane Inc",
            "icon": """<i class="fa-solid fa-city"></i>""",
            "platform": "Other",
            "platform page": "",
        },
        {
            "name": "DC509",
            "icon": """<i class="fa-solid fa-book-skull"></i>""",
            "platform": "Meetup",
            "platform page": "https://www.meetup.com/dc-509/",
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
            "name": "What is Crypto Currency",
            "icon": """<i class="fa-brands fa-bitcoin"></i>""",
            "platform": "Meetup",
            "platform page": "https://www.meetup.com/what-is-crypto-currency/",
        },
        {
            "name": "Spokane WordPress Meetup",
            "icon": """<i class="fa-brands fa-wordpress"></i>""",
            "platform": "Meetup",
            "platform page": "https://www.meetup.com/spokane-wordpress-meetup/",
        },
        {
            "name": "Coeur d'Alene & Spokane WordPress",
            "icon": """<i class="fa-brands fa-wordpress"></i>""",
            "platform": "Meetup",
            "platform page": "https://www.meetup.com/coeur-dalene-wordpress-meetup/",
        },
    ]
    for data in data_list:
        data["platform"], _ = SocialPlatform.objects.get_or_create(name=data["platform"])
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
            "name": "Eventbrite",
            "base_url": "www.eventbrite.com",
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
    create_social_platforms()
    create_groups()
    get_eventbrite_organization_details()
    get_meetup_group_details()
