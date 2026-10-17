"""Shared public community links, using the site's existing destinations."""

from django.conf import settings


def community_links(request) -> dict:
    """Allow deployments to override public links without exposing integration credentials."""
    return {
        "community_discord_url": getattr(settings, "COMMUNITY_DISCORD_URL", "https://discord.gg/wHrSJNgpnP"),
        "community_social_links": getattr(
            settings,
            "COMMUNITY_SOCIAL_LINKS",
            (
                {"name": "GitHub", "url": "https://github.com/SpokaneTech", "icon": "fab fa-github"},
                {
                    "name": "LinkedIn",
                    "url": "https://www.linkedin.com/company/spokanetech/",
                    "icon": "fab fa-linkedin-in",
                },
                {
                    "name": "Facebook",
                    "url": "https://www.facebook.com/spokanetech.org/",
                    "icon": "fab fa-facebook-f",
                },
            ),
        ),
    }
