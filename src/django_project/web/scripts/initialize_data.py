from web.models import Link, SocialPlatform, TechGroup


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


def run():
    create_social_platforms()
    create_groups()
