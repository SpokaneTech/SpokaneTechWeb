from typing import Any

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Event
from .tasks import (
    post_event_to_discord,
    post_event_to_linkedin,
    post_event_to_spug_task,
)


@receiver(post_save, sender=Event)
def event_post_to_linkedin_signal(sender, instance, created, **kwargs) -> None:
    """
    Signal receiver that triggers a Celery task to post the new event to LinkedIn.
    """
    if created:

        def on_commit_callback() -> None:
            # post to Discord
            discord_job: Any = post_event_to_discord.s(instance.pk, is_new=True)
            discord_job.apply_async()

            # post to LinkedIn
            linkedin_job: Any = post_event_to_linkedin.s(instance.pk, is_new=True)
            linkedin_job.apply_async()

            # if TechGroup is SPUG, also post to SPUG website via api
            if instance.group.name == "Spokane Python User Group":
                spug_job: Any = post_event_to_spug_task.s(instance.pk)
                spug_job.apply_async()

        transaction.on_commit(on_commit_callback)
