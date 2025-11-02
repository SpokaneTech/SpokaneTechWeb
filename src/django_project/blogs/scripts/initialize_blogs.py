from blogs.models import BlogPlatform, BlogPost, BlogSeries, BlogTag


def create_blog_tags() -> None:
    """Create some BlogTag entries"""
    tags_list: list[dict[str, str]] = [
        {"value": "API"},
        {"value": "Asynchronous"},
        {"value": "Backend"},
        {"value": "BeautifulSoup"},
        {"value": "Bootstrap"},
        {"value": "CI/CD"},
        {"value": "CSS"},
        {"value": "Celery"},
        {"value": "Cloud"},
        {"value": "Community"},
        {"value": "Django"},
        {"value": "Database"},
        {"value": "Data Collection"},
        {"value": "Data Modeling"},
        {"value": "DevOps"},
        {"value": "Docker"},
        {"value": "Docker Compose"},
        {"value": "Event-Driven"},
        {"value": "Frontend"},
        {"value": "Full-Stack"},
        {"value": "Git"},
        {"value": "GitHub"},
        {"value": "Grafana"},
        {"value": "GUI"},
        {"value": "HTML"},
        {"value": "HTMX"},
        {"value": "JavaScript"},
        {"value": "Microservices"},
        {"value": "Monitoring"},
        {"value": "Open Source"},
        {"value": "OpenTelemetry"},
        {"value": "Playwright"},
        {"value": "PostgreSQL"},
        {"value": "Prometheus"},
        {"value": "Python"},
        {"value": "Redis"},
        {"value": "Scheduling"},
        {"value": "Scraping"},
        {"value": "Testing"},
        {"value": "Version Control"},
        {"value": "Web Development"},
    ]

    for tag_data in tags_list:
        BlogTag.objects.get_or_create(value=tag_data["value"], defaults=tag_data)


def create_blog_platforms() -> None:
    """Create blog platforms"""
    platforms: list[dict[str, str]] = [
        {"name": "Medium", "website_url": "https://medium.com"},
        {"name": "Dev.to", "website_url": "https://dev.to"},
    ]

    for platform_data in platforms:
        BlogPlatform.objects.get_or_create(name=platform_data["name"], defaults=platform_data)


def create_blog_series() -> None:
    """Create some BlogSeries entries"""
    series_list: list[dict[str, str]] = [
        {
            "name": "Building SpokaneTech",
            "description": "The Spokane Tech website is a project for the community made by the community. The aim of the project is to deliver a community resource for all things tech in the Inland Northwest while providing an opportunity for contributes to gain real-world experience in a shared open source project.",
        },
    ]
    for series_data in series_list:
        BlogSeries.objects.get_or_create(name=series_data["name"], defaults=series_data)


def create_blog_posts() -> None:
    """Create some BlogPost entries"""
    posts_list: list[dict[str, str]] = [
        # introduction
        {
            "platform": "Medium",
            "title": "Introduction",
            "description": "Explore how the project defines its vision and phases—building a unified hub for tech events in the Inland Northwest, empowering early-career devs with real-world open-source experience, and evolving community-driven features.",
            "url": "https://dbslusser.medium.com/spokane-tech-introduction-0ccf3762112d",
            "author": "Spokane Tech Team",
            "series": "Building SpokaneTech",
            "tags": ["Community", "Open Source", "Web Development"],
        },
        # part 1: tech stack
        {
            "platform": "Medium",
            "title": "Part 1: Tech Stack",
            "description": "Discover how the tech stack behind the project, including Django, Celery, Redis, PostgreSQL, and HTMX powers data ingestion, backend logic and dynamic front-end updates.",
            "url": "https://dbslusser.medium.com/part-1-tech-stack-spokane-tech-blog-9ecd015c21d9",
            "author": "Spokane Tech Team",
            "series": "Building SpokaneTech",
            "tags": ["Python", "Django", "Redis", "PostgreSQL", "HTMX"],
        },
        # part 2: project structure
        {
            "platform": "Medium",
            "title": "Part 2: Project Structure",
            "description": "Explore how the Django-based repo for Spokane Tech is structured - from src/ split into project apps and tests, to the docker/ and envs/ directories - offering clear patterns for scalable, organized development.",
            "url": "https://dbslusser.medium.com/part-2-project-structure-spokane-tech-blog-8da22251f604",
            "author": "Spokane Tech Team",
            "series": "Building SpokaneTech",
            "tags": ["Git", "GitHub", "Version Control"],
        },
        # part 3: running locally
        {
            "platform": "Medium",
            "title": "Part 3: Running Locally",
            "description": "Dive into the nitty-gritty of getting the SpokaneTechWeb app up and running locally—cloning, setting up Python, installing dependencies, configuring Playwright for event scraping, and launching with Django migrations for full dev access.",
            "url": "https://dbslusser.medium.com/building-spokane-tech-part-3-4b1a8c0ccdfb",
            "author": "Spokane Tech Team",
            "series": "Building SpokaneTech",
            "tags": [
                "Python",
                "Django",
                "Full-Stack",
            ],
        },
        # part 4: data modeling
        {
            "platform": "Medium",
            "title": "Part 4: Data Modeling",
            "description": "Dive into the modeling phase of the Spokane Tech Web App project - discover how the core Django models (Event, Link, SocialPlatform, Tag, TechGroup) to structure community and event data in a clean and scalable way.",
            "url": "https://dbslusser.medium.com/building-spokane-tech-part-4-306889b0aa2c",
            "author": "Spokane Tech Team",
            "series": "Building SpokaneTech",
            "tags": ["Django", "Data Modeling", "Database"],
        },
        # part 5: gui
        {
            "platform": "Medium",
            "title": "Part 5: GUI Development",
            "description": "Discover how to build the interactive front-end for the SpokaneTechWeb app using modern tools like HTMX and Bootstrap 5; perfect for devs curious about dynamic UIs and streamlined workflows.",
            "url": "https://dbslusser.medium.com/part-5-gui-spokane-tech-blog-d5a8b9bc78f4",
            "author": "Spokane Tech Team",
            "series": "Building SpokaneTech",
            "tags": ["GUI", "HTMX", "Bootstrap", "Frontend"],
        },
        # part 6: data collection
        {
            "platform": "Medium",
            "title": "Part 6: Data Collection",
            "description": "Learn how data from Eventbrite and Meetup is scraped and parsed using tools like Playwright and BeautifulSoup, then stored in the database for the app.",
            "url": "https://dbslusser.medium.com/building-spokane-tech-part-6-6a80e0d65f6e",
            "author": "Spokane Tech Team",
            "series": "Building SpokaneTech",
            "tags": ["Data Collection", "Scraping", "Playwright"],
        },
        # part 7: scheduling tasks
        {
            "platform": "Medium",
            "title": "Part 7: Scheduling Tasks",
            "description": "Explore integrating Celery with Django - setting up scheduled tasks, asynchronous jobs, and live monitoring to automate and scale background workflows with ease.",
            "url": "https://dbslusser.medium.com/building-spokane-tech-part-7-f729be78157c",
            "author": "Spokane Tech Team",
            "series": "Building SpokaneTech",
            "tags": ["Celery", "Asynchronous", "Scheduling", "Redis"],
        },
        # part 8: adding docker
        {
            "platform": "Medium",
            "title": "Part 8: Adding Docker",
            "description": "Follow the Docker implementation, using Docker and Docker Compose to containerize and isolate services. Explore commands like docker-compose up -d and migration execution streamline development and multi-container orchestration.",
            "url": "https://dbslusser.medium.com/building-spokane-tech-part-8-b3ef344c75ca",
            "author": "Spokane Tech Team",
            "series": "Building SpokaneTech",
            "tags": ["Docker", "Docker Compose", "Microservices"],
        },
        # part 9: improving docker
    ]
    for post_data in posts_list:
        platform: BlogPlatform = BlogPlatform.objects.get(name=post_data.pop("platform"))
        series_name: str | None = post_data.pop("series", None)
        series: BlogSeries | None = BlogSeries.objects.get(name=series_name) if series_name else None
        tags_names: list[str] = post_data.get("tags", [])
        post_data.pop("tags", None)  # handled separately below
        post, _ = BlogPost.objects.get_or_create(
            title=post_data["title"],
            defaults={**post_data, "platform": platform, "series": series},
        )
        if tags_names:
            # post: BlogPost = BlogPost.objects.get(title=post_data["title"])
            for tag_name in tags_names:
                tag: BlogTag = BlogTag.objects.get(value=tag_name)
                post.tags.add(tag)


def run() -> None:
    create_blog_platforms()
    create_blog_series()
    create_blog_tags()
    create_blog_posts()
