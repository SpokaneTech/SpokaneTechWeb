import json
from datetime import datetime
from typing import Any

import requests


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
        event_name: str,
        event_start_datetime: datetime,
        event_end_datetime: datetime,
        event_location_name: str | None = None,
        event_url: str | None = None,
        group_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Builds a Discord message payload for a newly created event.

        Args:
            event_name (str): The name of the event.
            event_start_datetime (datetime): The start date and time of the event.
            event_end_datetime (datetime): The end date and time of the event.
            event_location_name (str | None, optional): The location of the event. Defaults to None.
            event_url (str | None, optional): The URL to RSVP or view the event. Defaults to None.
            group_name (str | None, optional): The name of the group hosting the event. Defaults to None.

        Returns:
            str: A dictionary representing the Discord message payload for the event.
        """
        fields: list[dict[str, Any]] = []
        if event_location_name is not None:
            fields.append({"name": "📍 Location", "value": event_location_name, "inline": False})
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
            "content": f"📢 A new event from {group_name} has just been created!\n\n👉 RSVP here: {event_url}",
            "embeds": [
                {
                    "title": event_name,
                    "url": event_url,
                    "fields": fields,
                    "footer": {"text": f"Hosted by {group_name}"},
                }
            ],
        }
        return data

    def build_event_reminder_message(
        self,
        event_name: str,
        event_start_datetime: datetime,
        event_end_datetime: datetime,
        event_location_name: str | None = None,
        event_url: str | None = None,
        group_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Builds a Discord event reminder message payload.

        Args:
            event_name (str): The name of the event.
            event_start_datetime (datetime): The start datetime of the event.
            event_end_datetime (datetime): The end datetime of the event.
            event_location_name (str | None, optional): The location name of the event. Defaults to None.
            event_url (str | None, optional): The URL for the event. Defaults to None.
            group_name (str | None, optional): The name of the hosting group. Defaults to None.

        Returns:
            str: A dictionary representing the Discord message payload, including content and embeds.
        """
        fields: list[dict[str, Any]] = []
        if event_location_name is not None:
            fields.append({"name": "📍 Location", "value": event_location_name, "inline": False})
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
            "content": f"🚀 Don't miss out! RSVP now for the next {group_name} event! 🎉 👉 {event_url}",
            "embeds": [
                {
                    "title": event_name,
                    "url": event_url,
                    "fields": fields,
                    "footer": {"text": f"Hosted by {group_name}"},
                }
            ],
        }
        return data

    def post_event(
        self,
        event_name: str,
        event_start_datetime: datetime,
        event_end_datetime: datetime,
        group_name: str,
        event_location_name: str | None = None,
        event_url: str | None = None,
        group_discord_webhook_url: str | None = None,
        reminder=False,
    ) -> None:
        """
        Posts an event notification to Discord channels.
        Depending on the `reminder` flag, constructs either an event reminder or event creation message,
        and sends it to the general Discord channel. If a group-specific Discord webhook URL is provided,
        also sends the message to the group's Discord channel.
        Args:
            event_name (str): The name of the event.
            event_start_datetime (datetime): The start date and time of the event.
            event_end_datetime (datetime): The end date and time of the event.
            group_name (str): The name of the group hosting the event.
            event_location_name (str, optional): The name of the event location. Defaults to None.
            event_url (str, optional): The URL for the event. Defaults to None.
            group_discord_webhook_url (str, optional): The Discord webhook URL for the group channel. Defaults to None.
            reminder (bool, optional): If True, sends a reminder message; otherwise, sends an event creation message. Defaults to False.
        Returns:
            None
        """
        if reminder:
            message: dict = self.build_event_reminder_message(
                event_name, event_start_datetime, event_end_datetime, event_location_name, event_url, group_name
            )
        else:
            message = self.build_event_created_message(
                event_name, event_start_datetime, event_end_datetime, event_location_name, event_url, group_name
            )

        # send to the general Discord channel
        self.send_message(message)

        # send to the group's Discord channel if a webhook URL is provided
        if group_discord_webhook_url:
            self.send_message(message, url=group_discord_webhook_url)
