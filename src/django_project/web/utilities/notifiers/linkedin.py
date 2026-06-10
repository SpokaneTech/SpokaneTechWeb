import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.utils import timezone
from web.utilities.ai.gemini import generate_post_content
from web.utilities.ai.prompts import (
    create_event_reminder_prompt,
    create_new_event_prompt,
)
from web.utilities.dt_utils import convert_to_pacific

if TYPE_CHECKING:
    from web.models import Event


logger = logging.getLogger(__name__)


class LinkedInOrganizationClient:
    def __init__(
        self,
        access_token: Optional[str],
        organization_urn: str,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
        env_path: Optional[str] = None,
    ) -> None:
        self.access_token = access_token
        self.organization_urn: str = organization_urn
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.env_path = Path(env_path) if env_path else None
        self.post_url = "https://api.linkedin.com/rest/posts"
        self.access_token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        self.authorization_url = "https://www.linkedin.com/oauth/v2/authorization"
        self.set_headers()

    def set_headers(self) -> None:
        self.headers: dict[str, str] = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "LinkedIn-Version": "202506",
            "X-Restli-Protocol-Version": "2.0.0",
        }

    def can_refresh_access_token(self) -> bool:
        return bool(self.refresh_token and self.client_id and self.client_secret)

    def ensure_access_token(self) -> None:
        if self.access_token:
            return
        if not self.can_refresh_access_token():
            raise ValueError("LinkedIn access token is missing and refresh credentials are not fully configured.")
        self.refresh_access_token()

    def refresh_access_token(self) -> None:
        if not self.can_refresh_access_token():
            raise ValueError("LinkedIn refresh token flow is not fully configured.")

        response = requests.post(
            self.access_token_url,
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )
        response.raise_for_status()
        token_data = response.json()

        self.access_token = token_data["access_token"]
        self.refresh_token = token_data.get("refresh_token", self.refresh_token)
        self.set_headers()
        self._persist_tokens()

    def build_authorization_url(self, redirect_uri: str, scope: str, state: Optional[str] = None) -> str:
        if not self.client_id:
            raise ValueError("LinkedIn client ID is required to build the authorization URL.")

        query_params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
        }
        if state:
            query_params["state"] = state

        prepared_request: requests.PreparedRequest = requests.Request(
            "GET", self.authorization_url, params=query_params
        ).prepare()
        if prepared_request.url is None:
            raise ValueError("LinkedIn authorization URL could not be generated.")
        return prepared_request.url

    def exchange_authorization_code(self, code: str, redirect_uri: str) -> dict[str, Any]:
        if not self.client_id or not self.client_secret:
            raise ValueError("LinkedIn client ID and client secret are required to exchange an authorization code.")

        response = requests.post(
            self.access_token_url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )
        response.raise_for_status()
        token_data = response.json()

        self.access_token = token_data["access_token"]
        self.refresh_token = token_data.get("refresh_token", self.refresh_token)
        self.set_headers()
        self._persist_tokens()
        return token_data

    def _persist_tokens(self) -> None:
        setattr(settings, "LINKEDIN_ACCESS_TOKEN", self.access_token)
        setattr(settings, "LINKEDIN_REFRESH_TOKEN", self.refresh_token)

        if not self.env_path:
            logger.info("LinkedIn tokens refreshed in memory only; ENV_PATH is not configured.")
            return
        if not self.env_path.exists():
            logger.warning("LinkedIn tokens refreshed but env file does not exist: %s", self.env_path)
            return

        lines = self.env_path.read_text(encoding="utf-8").splitlines()
        replacements = {
            "LINKEDIN_ACCESS_TOKEN": self.access_token,
            "LINKEDIN_REFRESH_TOKEN": self.refresh_token,
        }

        for key, value in replacements.items():
            serialized_value = json.dumps(value) if value is not None else '""'
            for index, line in enumerate(lines):
                if line.startswith(f"{key}="):
                    lines[index] = f"{key}={serialized_value}"
                    break
            else:
                lines.append(f"{key}={serialized_value}")

        self.env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _is_auth_failure(self, response: Optional[requests.Response]) -> bool:
        if response is None:
            return False
        return response.status_code in {401, 403}

    def post_organization_post(
        self,
        commentary: str,
        article_url: Optional[str] = None,
        article_title: Optional[str] = None,
        article_description: Optional[str] = None,
    ) -> requests.Response:
        self.ensure_access_token()
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
        response = requests.post(self.post_url, headers=self.headers, data=payload_json, timeout=15)

        try:
            response.raise_for_status()
            return response
        except requests.HTTPError:
            if not self._is_auth_failure(response) or not self.can_refresh_access_token():
                raise

        logger.info("LinkedIn post received %s; refreshing access token and retrying once.", response.status_code)
        self.refresh_access_token()
        retry_response = requests.post(self.post_url, headers=self.headers, data=payload_json, timeout=15)
        retry_response.raise_for_status()
        return retry_response

    def build_event_commentary(
        self,
        event: "Event",
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
        event: "Event",
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
