"""Announce new events and meaningful changes after their transaction commits."""

from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Event
from .tasks import post_event_to_discord, post_event_to_linkedin, post_event_to_spug_task
from .utilities.dt_utils import convert_to_pacific

CHANGE_FIELDS = {
    "name": "title",
    "start_datetime": "start time",
    "end_datetime": "end time",
    "location_name": "venue",
    "location_address": "address",
    "map_link": "map",
    "status": "status",
    "url": "event website",
}


@receiver(pre_save, sender=Event)
def capture_event_changes(sender, instance, raw=False, update_fields=None, **kwargs):
    instance._event_changes = []
    instance._event_was_upcoming = False
    if raw or not instance.pk:
        return
    old = Event.objects.filter(pk=instance.pk).values(*CHANGE_FIELDS, "change_version").first()
    if old is None:
        return
    changes = [
        key
        for key in CHANGE_FIELDS
        if (update_fields is None or key in update_fields) and old[key] != getattr(instance, key)
    ]
    instance._event_changes = changes
    instance._event_was_upcoming = old["start_datetime"] >= timezone.now()
    if changes:
        instance.change_version = old["change_version"] + 1


@receiver(post_save, sender=Event)
def event_post_to_linkedin_signal(sender, instance, created, raw=False, **kwargs) -> None:
    if raw or (instance.group and not instance.group.enabled):
        return
    changes = getattr(instance, "_event_changes", [])
    if not created and not changes:
        return
    if created and instance.is_cancelled:
        return
    # Changes to historic events should not announce an upcoming meetup.
    if not created and instance.start_datetime < timezone.now() and not getattr(instance, "_event_was_upcoming", False):
        return
    change_kwargs = {}
    if not created:
        label = "Event cancelled" if instance.is_cancelled else "Event updated"
        if "status" in changes and not instance.is_cancelled:
            label = "Event reinstated"
        start = convert_to_pacific(instance.start_datetime).strftime("%a, %b %d, %Y at %I:%M %p %Z")
        location = ", ".join(value for value in (instance.location_name, instance.location_address) if value)
        message = (
            f"{label}: {instance.name}\nChanged: {', '.join(CHANGE_FIELDS[key] for key in changes)}\nWhen: {start}"
        )
        if instance.end_datetime:
            message += f" – {convert_to_pacific(instance.end_datetime).strftime('%b %d, %I:%M %p %Z')}"
        if location:
            message += f"\nWhere: {location}"
        if instance.url:
            message += f"\nEvent website: {instance.url}"
        change_kwargs = {"change_message": message, "change_version": instance.change_version}
    # Capture immutable values rather than retaining a mutable model instance.
    pk = instance.pk
    group_name = instance.group.name if instance.group else None

    def on_commit_callback() -> None:
        if settings.POST_TO_DISCORD:
            post_event_to_discord.s(pk, is_new=created, **change_kwargs).apply_async()
        if created or settings.POST_TO_LINKEDIN:
            post_event_to_linkedin.s(pk, is_new=created, **change_kwargs).apply_async()
        if created and group_name == "Spokane Python User Group":
            post_event_to_spug_task.s(pk).apply_async()

    transaction.on_commit(on_commit_callback)
