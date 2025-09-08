from web.models import Event
from web.utilities.ai.gemini import (
    create_event_reminder_tomorrow,
    create_new_event_prompt,
    generate_post_content,
)


def build_event_post_content(event: Event) -> str:
    # prompt: str = create_new_event_prompt(event.description, event.group.platform.name, event.group.name)
    prompt = create_event_reminder_tomorrow(event.description)
    content: str = generate_post_content(prompt)
    return content


def run():
    event = Event.objects.get(pk=52)
    if event:
        post_content = build_event_post_content(event)
        print(post_content)
