import json
from datetime import datetime
from typing import Any, Optional

import requests
from bs4 import BeautifulSoup


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

    def build_event_created_commentary(
        self,
        event_name: str,
        event_date: datetime,
        location_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> str:
        """
        Constructs a LinkedIn-style commentary string for a new event announcement.
        Args:
            event_name (str): The name of the event.
            event_date (datetime): The date and time of the event.
            location_name (Optional[str], optional): The location of the event. Defaults to None.
            description (Optional[str], optional): A description of the event. If provided, only the first 500 characters are included. Defaults to None.
        Returns:
            str: A formatted commentary string suitable for posting on LinkedIn.
        """
        if isinstance(event_date, datetime):
            formatted_date: str = event_date.strftime("%A, %B %d, %Y at %I:%M %p")
        else:
            formatted_date = str(event_date)

        commentary: str = f"🚀 New Event Alert! Join us for: {event_name}\n\n"
        commentary += f"🗓️ When: {formatted_date}\n\n"
        if location_name:
            commentary += f"📍 Where: {location_name}\n\n"
        if description:
            description = BeautifulSoup(description, "html.parser").get_text()
            commentary += f"Details: {description[:500]}..."
        return commentary

    def build_event_reminder_commentary(
        self, event_name: str, event_date: datetime, location_name: Optional[str] = None
    ) -> str:
        """
        Generates a reminder commentary string for an event, including its name, date, and optional location.

        Args:
            event_name (str): The name of the event.
            event_date (datetime.datetime): The date and time of the event.
            location_name (Optional[str], optional): The name of the event location. Defaults to None.

        Returns:
            str: A formatted reminder string containing event details.
        """
        if isinstance(event_date, datetime):
            formatted_date: str = event_date.strftime("%A, %B %d, %Y at %I:%M %p")
        else:
            formatted_date = str(event_date)

        reminder: str = f"🔔 Reminder: {event_name} is happening on {formatted_date}."
        if location_name:
            reminder += f"📍 Location: {location_name}."
        return reminder

    def post_event_created(
        self,
        name: str,
        date_time: datetime,
        url: Optional[str] = None,
        location_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> requests.Response:
        """
        Posts a new event announcement to LinkedIn.
        Args:
            event_name (str): The name of the event.
            event_date (datetime): The date and time of the event.
            location_name (Optional[str], optional): The location of the event. Defaults to None.
            description (Optional[str], optional): A description of the event. Defaults to None.
        Returns:
            dict: The response from the LinkedIn API after posting the event.
        """
        commentary: str = self.build_event_created_commentary(
            event_name=name, event_date=date_time, location_name=location_name, description=description
        )
        return self.post_organization_post(
            commentary,
            article_url=url,
            article_title=name,
            article_description=description or "Learn more about this event.",
        )

    def post_event_reminder(
        self,
        event_name: str,
        event_date: datetime,
        event_url: Optional[str] = None,
        location_name: Optional[str] = None,
    ) -> requests.Response:
        """
        Posts a reminder for an upcoming event to LinkedIn.
        Args:
            event_name (str): The name of the event.
            event_date (datetime): The date and time of the event.
            location_name (Optional[str], optional): The location of the event. Defaults to None.
        Returns:
            dict: The response from the LinkedIn API after posting the reminder.
        """
        commentary: str = self.build_event_reminder_commentary(event_name, event_date, location_name)
        return self.post_organization_post(commentary, article_url=event_url, article_title=event_name)
