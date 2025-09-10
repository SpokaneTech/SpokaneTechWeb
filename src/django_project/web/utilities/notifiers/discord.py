import json
from multiprocessing.managers import BaseManager
from typing import Any

import requests
from django.utils import timezone
from web.models import Event
from web.utilities.ai.gemini import generate_post_content
from web.utilities.ai.prompts import (
    create_event_reminder_prompt,
    create_new_event_prompt,
    create_weekly_events_list_prompt,
)
from web.utilities.dt_utils import convert_to_pacific


class DiscordNotifier:
    def __init__(self, webhook_url: str) -> None:
        self.webhook_url: str = webhook_url

    def send_message(self, payload: dict, url: str | None = None) -> requests.Response:
        """
        Sends a message to a Discord webhook.
        Args:
            payload (dict): The JSON payload to send in the message.
            url (str, optional): The Discord webhook URL to send the message to.
                If not provided, uses the instance's `webhook_url`.
        Returns:
            requests.Response: The response object from the Discord webhook.
        Raises:
            requests.HTTPError: If the HTTP request returned an unsuccessful status code.
        """

        headers: dict[str, str] = {"Content-Type": "application/json"}
        response: requests.Response = requests.post(
            url or self.webhook_url, data=json.dumps(payload), headers=headers, timeout=15
        )
        response.raise_for_status()
        return response

    def build_event_created_message(
        self,
        event: Event,
    ) -> dict[str, Any]:
        """
        Builds a Discord message payload for a newly created event.

        Args:
            event (Event): The event object containing details about the event.
            group_name (str | None, optional): The name of the group hosting the event. Defaults to None.

        Returns:
            str: A dictionary representing the Discord message payload for the event.
        """
        try:
            prompt: str = create_new_event_prompt(
                event_description=event.name,
                platform_name=event.group.platform.name,
                group_name=event.group.name or "Unknown Group",
            )
            content: str = generate_post_content(prompt)
        except (ValueError, requests.HTTPError):
            content = f"📢 A new event from {event.group.name} has just been created!\n\n👉 RSVP here: {event.url}"

        event_start_datetime: timezone.datetime = convert_to_pacific(event.start_datetime)
        event_end_datetime: timezone.datetime = convert_to_pacific(event.end_datetime)

        fields: list[dict[str, Any]] = []
        if event.location_name is not None:
            fields.append({"name": "📍 Location", "value": event.location_name, "inline": False})
        fields.extend(
            [
                {"name": "📅 Date", "value": str(event_start_datetime.date()), "inline": True},
                {
                    "name": "⏰ Time",
                    "value": f"{event_start_datetime.strftime('%I:%M %p')} - {event_end_datetime.strftime('%I:%M %p')}",
                    "inline": True,
                },
            ]
        )
        data: dict[str, Any] = {
            "content": content,
            "embeds": [
                {
                    "title": event.name,
                    "url": event.url,
                    "fields": fields,
                    "footer": {"text": f"Hosted by {event.group.name}"},
                }
            ],
        }
        return data

    def build_event_reminder_message(
        self,
        event: Event,
    ) -> dict[str, Any]:
        """
        Builds a Discord event reminder message payload.

        Args:
            event (Event): The event object containing details about the event.

        Returns:
            str: A dictionary representing the Discord message payload, including content and embeds.
        """
        try:
            prompt: str = create_event_reminder_prompt(event_description=event.description)
            content: str = generate_post_content(prompt)
        except (ValueError, requests.HTTPError):
            content = f"📢 A new event from {event.group.name} has just been created!\n\n👉 RSVP here: {event.url}"

        event_start_datetime: timezone.datetime = convert_to_pacific(event.start_datetime)
        event_end_datetime: timezone.datetime = convert_to_pacific(event.end_datetime)

        fields: list[dict[str, Any]] = []
        if event.location_name is not None:
            fields.append({"name": "📍 Location", "value": event.location_name, "inline": False})
        fields.extend(
            [
                {"name": "📅 Date", "value": str(event_start_datetime.date()), "inline": True},
                {
                    "name": "⏰ Time",
                    "value": f"{event_start_datetime.strftime('%I:%M %p')} - {event_end_datetime.strftime('%I:%M %p')}",
                    "inline": True,
                },
            ]
        )
        data: dict[str, Any] = {
            "content": content,
            "embeds": [
                {
                    "title": event.name,
                    "url": event.url,
                    "fields": fields,
                    "footer": {"text": f"Hosted by {event.group.name}"},
                }
            ],
        }
        return data

    def build_weekly_event_summary(
        self,
        event_list,
    ) -> dict[str, Any]:
        """
        Builds a Discord message payload summarizing the week's events.

        Args:
            event_list (BaseManager[Event]): A queryset of events to include in the summary.

        Returns:
            dict: A dictionary representing the Discord message payload, including content and embeds.
        """
        if not event_list:
            return {"content": "No events found for the week."}

        try:
            prompt: str = create_weekly_events_list_prompt(event_count=event_list.count())
            content: str = generate_post_content(prompt)
        except (ValueError, requests.HTTPError):
            content = f"📢 Hello Spokane Tech Community! We have {event_list.count()} great events happening this week!\n👉 Check them out!"

        embeded_event_list: list[dict[str, Any]] = []
        for event in event_list:
            embeded_event_list.append(
                {
                    "name": f"{convert_to_pacific(event.start_datetime).strftime('%Y-%m-%d %I:%M %p')} {event.name}",
                    "value": f"{event.description}\n[RSVP here]({event.url})",
                    "inline": False,
                },
            )

        data: dict[str, Any] = {
            "content": content,
            "embeds": [{"fields": embeded_event_list}],
        }
        return data

    def post_event(
        self,
        event: Event,
        reminder=False,
    ) -> None:
        """
        Posts an event notification to Discord channels.
        Depending on the `reminder` flag, constructs either an event reminder or event creation message,
        and sends it to the general Discord channel. If a group-specific Discord webhook URL is provided,
        also sends the message to the group's Discord channel.
        Args:
            event (Event): The event object containing details about the event.
            reminder (bool, optional): If True, sends a reminder message; otherwise, sends an event creation message. Defaults to False.
        Returns:
            None
        """
        if reminder:
            message: dict = self.build_event_reminder_message(event)
        else:
            message = self.build_event_created_message(event)

        # send to the general Discord channel
        self.send_message(message)

        # send to the group's Discord channel if a webhook URL is provided
        if event.group.discord_webhook_url:
            self.send_message(message, url=event.group.discord_webhook_url)

    def post_weekly_summary(self, event_list: BaseManager) -> None:
        """
        Posts a weekly event summary to the general Discord channel.
        Constructs a summary message for the provided list of events and sends it to the general Discord channel.
        Args:
            event_list (BaseManager): A queryset of events to include in the weekly summary.
        Returns:
            None
        """
        payload: dict = self.build_weekly_event_summary(event_list)
        self.send_message(payload=payload)
