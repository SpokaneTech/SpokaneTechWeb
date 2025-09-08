def create_new_event_prompt(event_description: str, platform_name: str, group_name: str) -> str:
    """
    Generates a prompt string for announcing a new event on Discord.
    Args:
        event_description (str): The description of the event.
        platform_name (str): The name of the platform where the event is added.
        group_name (str): The name of the group hosting the event.
    Returns:
        str: A formatted prompt for a friendly and inviting event announcement, excluding links, dates, and location.
    """

    prompt: str = f"create a single friendly and inviting announcement for a new event that was just added to {platform_name} from the {group_name}. This will be posted to Discord via webhook, and we only need the content section, do not include links or dates or location. Here is the event description: {event_description}"
    return prompt


def create_event_reminder_prompt(event_description: str) -> str:
    """
    Generates a prompt for creating a friendly and inviting event reminder for an event happening tomorrow.
    The prompt is intended for posting to Discord via webhook and requests only the content section,
    excluding links, dates, and location information.
    Args:
        event_description (str): A description of the event to be included in the reminder.
    Returns:
        str: A formatted prompt string for generating the event reminder.
    """

    prompt: str = f"create a single friendly and inviting event reminder for the following event that is happening tomorrow. This will be posted to Discord via webhook, and we only need the content section, do not include links or dates or location. Here is the event description: {event_description}"
    return prompt


def create_weekly_events_list_prompt(event_count: int) -> str:
    """
    Generates a prompt for creating a friendly and inviting weekly events list.
    The prompt is intended for posting to Discord via webhook and requests only the content section,
    excluding links, dates, and location information.
    Args:
        event_count (int): The number of events to be included in the weekly events list.
    Returns:
        str: A formatted prompt string for generating the weekly events list.
    """

    prompt: str = f"create a single friendly and exciting sounding header for a post sharing {event_count} events occurring in Spokane this week as available from SpokaneTech.org. This will be posted to Discord via webhook, and we only need the content section; do not include any dates. The actual events will be added separately. The post should sound exciting and fun and encourage people to check out the events and attend them! Just provide one, I don't need multiple options."
    return prompt
