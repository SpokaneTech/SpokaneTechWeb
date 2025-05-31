import random

from allauth.socialaccount.models import OAuth2Provider, SocialAccount
from django.conf import settings
from django.utils.timezone import make_aware
from faker import Faker
from members.models import (
    CareerLevel,
    Member,
    MemberInterest,
    MemberLink,
    MemberSkill,
    SkillLevel,
    TechnicalArea,
)

zip_codes: list[str] = [
    # Spokane, WA area
    "99201",
    "99202",
    "99203",
    "99204",
    "99205",
    "99206",
    "99207",
    "99208",
    "99212",
    "99216",
    "99217",
    "99218",
    "99223",
    "99224",
    "99001",
    "99003",
    "99004",
    "99005",
    "99006",
    "99008",
    "99009",
    "99011",
    "99012",
    "99013",
    "99014",
    "99016",
    "99018",
    "99019",
    "99020",
    "99021",
    "99022",
    "99023",
    "99025",
    "99026",
    "99027",
    "99029",
    "99030",
    "99031",
    "99036",
    "99037",
    "99039",
    # Coeur d'Alene, ID area
    "83814",
    "83815",
    "83816",
    "83835",
    "83854",
    "83877",
    "83858",
    "83801",
    "83869",
    "83876",
]


def create_oauth2_providers() -> None:
    """Create some OAuth2Provider entries"""
    print("INFO: creating OAuth2Provider entries")

    data_list: list[dict[str, str]] = [
        # {
        #     "name": "GitHub",
        #     "client_id": "github_client_id",
        #     "client_secret": "github_client_secret",
        #     "redirect_uri": "https://example.com/oauth2/github/callback",
        # },
        {
            "name": "Google",
            "client_id": "google_client_id",
            "client_secret": "google_client_secret",
            "redirect_uri": "https://example.com/oauth2/google/callback",
        },
    ]
    for data in data_list:
        provider, _ = OAuth2Provider.objects.update_or_create(name=data["name"], defaults=data)
        SocialAccount.objects.update_or_create(provider=provider, defaults={"provider": provider})


def create_career_levels() -> None:
    """Create some CareerLevel entries"""
    print("INFO: creating CareerLevel entries")
    data_list: list[dict[str, str]] = [
        {
            "name": "Student",
            "description": "Student or intern",
        },
        {
            "name": "Early",
            "description": "Early career",
        },
        {
            "name": "Mid",
            "description": "Mid-level",
        },
        {
            "name": "Senior",
            "description": "Senior-level",
        },
        {
            "name": "Retired",
            "description": "Retired",
        },
    ]
    for data in data_list:
        CareerLevel.objects.update_or_create(name=data["name"], defaults=data)


def create_members(qty=15) -> None:
    """Create some Member entries"""
    print("INFO: creating Member entries")

    for _ in range(qty):
        faker = Faker()
        data: dict = {
            "email": faker.email(),
            "first_name": faker.first_name(),
            "last_name": faker.last_name(),
            "zip_code": random.choice(zip_codes),
            "last_login": make_aware(faker.date_time()),
            "career_level": CareerLevel.objects.get_random_row(),
        }
        member, is_new = Member.objects.update_or_create(email=data["email"], defaults=data)
        if is_new:
            # add random interests
            for i in range(random.randint(3, 10)):
                interest: TechnicalArea = TechnicalArea.objects.get_random_row()
                interest_level: int = random.randint(1, 5)
                MemberInterest.objects.update_or_create(
                    member=member,
                    interest=interest,
                    defaults={
                        "interest_level": interest_level,
                    },
                )

            # add random skills
            for i in range(random.randint(3, 10)):
                skill: TechnicalArea = TechnicalArea.objects.get_random_row()
                skill_level: SkillLevel = SkillLevel.objects.get_random_row()
                yoe: int = random.randint(0, 20)
                MemberSkill.objects.update_or_create(
                    member=member,
                    skill=skill,
                    defaults={
                        "level": skill_level,
                        "yoe": yoe,
                    },
                )
            # add random links
            for i in range(random.randint(1, 5)):
                link_data: dict = {
                    "member": member,
                    "name": faker.word(),
                    "description": faker.sentence(),
                    "url": faker.url(),
                    "is_public": random.choice([True, False]),
                }
                MemberLink.objects.update_or_create(
                    member=member,
                    name=link_data["name"],
                    defaults=link_data,
                )


def create_member_interests() -> None:
    """Create some MemberInterest entries"""
    print("INFO: creating MemberInterest entries")
    data_list: list[dict[str, str]] = [
        {
            "member": 1,
            "interest": 1,
            "interest_level": 3,
        },
        {
            "member": 1,
            "interest": 2,
            "interest_level": 4,
        },
        {
            "member": 2,
            "interest": 3,
            "interest_level": 5,
        },
    ]
    for data in data_list:
        MemberInterest.objects.update_or_create(member=data["member"], interest=data["interest"], defaults=data)


def create_skill_levels() -> None:
    """Create some SkillLevel entries"""
    print("INFO: creating SkillLevel entries")
    data_list: list[dict[str, str]] = [
        {
            "name": "Beginner",
            "description": "Just starting out.",
        },
        {
            "name": "Intermediate",
            "description": "Some experience.",
        },
        {
            "name": "Advanced",
            "description": "Very experienced.",
        },
        {
            "name": "Expert",
            "description": "Top of the field.",
        },
    ]
    for data in data_list:
        SkillLevel.objects.update_or_create(name=data["name"], defaults=data)


def create_technical_areas() -> None:
    """Create some TechnicalArea entries"""
    print("INFO: creating TechnicalArea entries")
    data_list: list[dict[str, str]] = [
        {
            "name": "Web Development",
            "description": "Building and maintaining websites.",
        },
        {
            "name": "Backend Development",
            "description": "Server-side development.",
        },
        {
            "name": "Frontend Development",
            "description": "Client-side development.",
        },
        {
            "name": "Full Stack Development",
            "description": "Both frontend and backend development.",
        },
        {
            "name": "Database Management",
            "description": "Managing databases.",
        },
        {
            "name": "API Development",
            "description": "Creating APIs for applications.",
        },
        {
            "name": "Cloud Services",
            "description": "Using cloud platforms for development.",
        },
        {
            "name": "Artificial Intelligence",
            "description": "Creating intelligent systems.",
        },
        {
            "name": "Mobile Development",
            "description": "Creating applications for mobile devices.",
        },
        {
            "name": "Data Science",
            "description": "Extracting insights from data.",
        },
        {
            "name": "Machine Learning",
            "description": "Creating algorithms that learn from data.",
        },
        {
            "name": "DevOps",
            "description": "Combining software development and IT operations.",
        },
        {
            "name": "Cloud Computing",
            "description": "Using remote servers for data storage and processing.",
        },
        {
            "name": "Cybersecurity",
            "description": "Protecting systems and networks from digital attacks.",
        },
        {
            "name": "Blockchain",
            "description": "Distributed ledger technology.",
        },
        {
            "name": "Artificial Intelligence",
            "description": "Simulating human intelligence in machines.",
        },
        {
            "name": "Internet of Things",
            "description": "Connecting physical devices to the internet.",
        },
        {
            "name": "Game Development",
            "description": "Creating video games.",
        },
        {
            "name": "Augmented Reality",
            "description": "Overlaying digital information on the real world.",
        },
        {
            "name": "Virtual Reality",
            "description": "Creating immersive digital environments.",
        },
        {
            "name": "UI/UX Design",
            "description": "Designing user interfaces and experiences.",
        },
        {
            "name": "Software Testing",
            "description": "Ensuring software quality through testing.",
        },
        {
            "name": "Project Management",
            "description": "Planning and executing projects.",
        },
        {
            "name": "Agile Methodologies",
            "description": "Iterative and incremental development.",
        },
        {
            "name": "Microservices",
            "description": "Architectural style that structures an application as a collection of services.",
        },
        {
            "name": "Serverless Computing",
            "description": "Running applications without managing servers.",
        },
        {
            "name": "Big Data",
            "description": "Handling large volumes of data.",
        },
        {
            "name": "Natural Language Processing",
            "description": "Interacting with computers using natural language.",
        },
        {
            "name": "Computer Vision",
            "description": "Enabling computers to interpret visual information.",
        },
        {
            "name": "Robotics",
            "description": "Designing and building robots.",
        },
        {
            "name": "3D Printing",
            "description": "Creating three-dimensional objects from digital files.",
        },
        {
            "name": "Quantum Computing",
            "description": "Using quantum-mechanical phenomena to perform computation.",
        },
        {
            "name": "Edge Computing",
            "description": "Processing data near the source of data generation.",
        },
        {
            "name": "Web Analytics",
            "description": "Analyzing web data to improve performance.",
        },
        {
            "name": "User Research",
            "description": "Understanding user needs and behaviors.",
        },
        {
            "name": "A/B Testing",
            "description": "Comparing two versions of a webpage to see which performs better.",
        },
        {
            "name": "python",
            "description": "A high-level programming language.",
        },
        {
            "name": "javascript",
            "description": "A programming language for web development.",
        },
        {
            "name": "java",
            "description": "A high-level programming language used for building applications.",
        },
        {
            "name": "csharp",
            "description": "A programming language developed by Microsoft.",
        },
        {
            "name": "c++",
            "description": "A general-purpose programming language.",
        },
        {
            "name": "html",
            "description": "The standard markup language for creating web pages.",
        },
        {
            "name": "css",
            "description": "A style sheet language used for describing the presentation of a document.",
        },
        {
            "name": "sql",
            "description": "A domain-specific language used in programming and managing relational databases.",
        },
        {
            "name": "ruby",
            "description": "A dynamic, open-source programming language.",
        },
        {
            "name": "php",
            "description": "A popular general-purpose scripting language.",
        },
        {
            "name": "swift",
            "description": "A general-purpose programming language developed by Apple.",
        },
        {
            "name": "go",
            "description": "An open-source programming language that makes it easy to build simple, reliable, and efficient software.",
        },
        {
            "name": "rust",
            "description": "A systems programming language focused on safety and performance.",
        },
        {
            "name": "typescript",
            "description": "A strict syntactical superset of JavaScript that adds optional static typing.",
        },
    ]
    for data in data_list:
        TechnicalArea.objects.update_or_create(name=data["name"], defaults=data)


def run() -> None:
    """Run the script"""
    print("INFO: Initializing member data")
    create_skill_levels()
    create_technical_areas()
    create_career_levels()
    create_members()
