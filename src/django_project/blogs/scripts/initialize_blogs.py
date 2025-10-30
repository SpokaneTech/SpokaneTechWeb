from blogs.models import BlogPlatform, BlogPost, BlogSeries


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
            "description": "An introduction to the project and its goals.",
            "url": "https://dbslusser.medium.com/spokane-tech-introduction-0ccf3762112d",
            "author": "Spokane Tech Team",
            "series": "Building SpokaneTech",
        },
        # part 1: tech stack
        {
            "platform": "Medium",
            "title": "Tech Stack",
            "description": "An overview of the tech stack used in the project.",
            "url": "https://dbslusser.medium.com/part-1-tech-stack-spokane-tech-blog-9ecd015c21d9",
            "author": "Spokane Tech Team",
            "series": "Building SpokaneTech",
        },
        # part 2: project structure
        {
            "platform": "Medium",
            "title": "Project Structure",
            "description": "A walkthrough of the project and repository structure.",
            "url": "https://dbslusser.medium.com/part-2-project-structure-spokane-tech-blog-8da22251f604",
            "author": "Spokane Tech Team",
            "series": "Building SpokaneTech",
        },
        # part 3: running locally
        {
            "platform": "Medium",
            "title": "Running Locally",
            "description": "Instructions on how to set up and run the project locally.",
            "url": "https://dbslusser.medium.com/building-spokane-tech-part-3-4b1a8c0ccdfb",
            "author": "Spokane Tech Team",
            "series": "Building SpokaneTech",
        },
        # part 4: data modeling
        {
            "platform": "Medium",
            "title": "Data Modeling",
            "description": "Designing the data models for the project.",
            "url": "https://dbslusser.medium.com/building-spokane-tech-part-4-306889b0aa2c",
            "author": "Spokane Tech Team",
            "series": "Building SpokaneTech",
        },
        # part 5: gui
        {
            "platform": "Medium",
            "title": "GUI Development",
            "description": "Creating the user interface for the project.",
            "url": "https://dbslusser.medium.com/part-5-gui-spokane-tech-blog-d5a8b9bc78f4",
            "author": "Spokane Tech Team",
            "series": "Building SpokaneTech",
        },
        # part 6: data collection
        {
            "platform": "Medium",
            "title": "Data Collection",
            "description": "Methods and strategies for collecting data for the project.",
            "url": "https://dbslusser.medium.com/building-spokane-tech-part-6-6a80e0d65f6e",
            "author": "Spokane Tech Team",
            "series": "Building SpokaneTech",
        },
        # part 7: scheduling tasks
        {
            "platform": "Medium",
            "title": "Scheduling Tasks",
            "description": "Integrating Celery for scheduling tasks, executing work asynchronously, and monitoring task statuses.",
            "url": "https://dbslusser.medium.com/building-spokane-tech-part-7-f729be78157c",
            "author": "Spokane Tech Team",
            "series": "Building SpokaneTech",
        },
        # part 8: adding docker
        {
            "platform": "Medium",
            "title": "Adding Docker",
            "description": "Containerizing the application using Docker for easier deployment and development.",
            "url": "https://dbslusser.medium.com/building-spokane-tech-part-8-1-2-3-adding-docker-7c6f6f2fbb3e",
            "author": "Spokane Tech Team",
            "series": "Building SpokaneTech",
        },
        # part 9: improving docker
    ]
    for post_data in posts_list:
        platform: BlogPlatform = BlogPlatform.objects.get(name=post_data.pop("platform"))
        series_name: str | None = post_data.pop("series", None)
        series: BlogSeries | None = BlogSeries.objects.get(name=series_name) if series_name else None
        BlogPost.objects.get_or_create(
            title=post_data["title"],
            defaults={**post_data, "platform": platform, "series": series},
        )


def run() -> None:
    create_blog_platforms()
    create_blog_series()
    create_blog_posts()
