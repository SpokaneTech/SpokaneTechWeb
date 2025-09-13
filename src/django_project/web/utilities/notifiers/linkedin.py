import json
from typing import Any, Optional

import requests
from bs4 import BeautifulSoup
from django.utils import timezone
from web.models import Event
from web.utilities.ai.gemini import generate_post_content
from web.utilities.ai.prompts import (
    create_event_reminder_prompt,
    create_new_event_prompt,
)
from web.utilities.dt_utils import convert_to_pacific


class LinkedInOrganizationClient:
    def __init__(
        self,
        access_token: str,
        organization_urn: str,
    ) -> None:
        self.access_token: str = access_token
        self.organization_urn: str = organization_urn
        self.post_url = "https://api.linkedin.com/rest/posts"
        self.set_headers()

    def set_headers(self) -> None:
        self.headers: dict[str, str] = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "LinkedIn-Version": "202506",
            "X-Restli-Protocol-Version": "2.0.0",
        }

    def post_organization_post(
        self,
        commentary: str,
        article_url: Optional[str] = None,
        article_title: Optional[str] = None,
        article_description: Optional[str] = None,
    ) -> requests.Response:
        payload: dict[str, Any] = {
            "author": self.organization_urn,
            "commentary": commentary,
            "visibility": "PUBLIC",
            "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": []},
            "lifecycleState": "PUBLISHED",
        }

        if article_url:
            payload["content"] = {
                "article": {
                    "source": article_url,
                    "title": article_title,
                    "description": article_description or "Learn more about this event.",
                }
            }

        payload_json: str = json.dumps(payload)
        response: requests.Response = requests.post(self.post_url, headers=self.headers, data=payload_json, timeout=15)
        response.raise_for_status()
        return response

    def build_event_commentary(
        self,
        event: Event,
        is_new: bool = True,
    ) -> str:
        """
        Generates a reminder commentary string for an event, including its name, date, and optional location.

        Args:
            event (Event): The event object containing details about the event.
            is_new (bool, optional): If True, sends a creation message; otherwise, sends a reminder message. Defaults to True.

        Returns:
            str: A formatted reminder string containing event details.
        """
        event_start_datetime: timezone.datetime = convert_to_pacific(event.start_datetime)

        try:
            if is_new:
                prompt: str = create_new_event_prompt(
                    event_description=(
                        BeautifulSoup(event.description, "html.parser").get_text() if event.description else event.name
                    ),
                    platform_name=event.group.platform.name,
                    group_name=event.group.name,
                )
            else:
                prompt = create_event_reminder_prompt(
                    event_description=(
                        BeautifulSoup(event.description, "html.parser").get_text() if event.description else event.name
                    ),
                )
            commentary: str = generate_post_content(prompt)
        except (ValueError, requests.HTTPError):
            if is_new:
                commentary = f"🚀 New Event Alert! Join us for: {event.name}\n\n"
            else:
                commentary = f"🔔 Reminder: {event.name} is happening soon!\n\n"

        if event.location_name:
            commentary += f"\n\n📍 Location: {event.location_name}."
        commentary += f"\n\n📅 Date: {event_start_datetime.date()}."
        commentary += f"\n⏰ Time: {event_start_datetime.strftime('%I:%M %p')}."
        if event.url:
            commentary += f"\n\n👉 RSVP here: {event.url}"
        return commentary

    def post_event(
        self,
        event: Event,
        is_new: bool = True,
    ) -> requests.Response:
        """
        Posts an event notification to LinkedIn.
        Args:
            event (Event): The event object containing details about the event.
            is_new (bool, optional): If True, sends a creation message; otherwise, sends a reminder message. Defaults to True.
        Returns:
            None
        """
        if is_new:
            commentary: str = self.build_event_commentary(event, is_new)
        else:
            commentary = self.build_event_commentary(event, is_new)
        return self.post_organization_post(commentary, article_url=event.url, article_title=event.name)
