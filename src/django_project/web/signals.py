from typing import Any

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Event
from .tasks import post_event_to_linkedin


@receiver(post_save, sender=Event)
def event_post_to_linkedin_signal(sender, instance, created, **kwargs) -> None:
    """
    Signal receiver that triggers a Celery task to post the new event to LinkedIn.
    """
    if created:
        job: Any = post_event_to_linkedin.s(instance.pk, is_new=True)
        job.apply_async()
