# import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from members.models import Member

# import tasks
from members.tasks import get_city_from_zip


@receiver(post_save, sender=Member)
def new_member(sender, instance, created, **kwargs) -> None:
    """ """
    if created:
        job = get_city_from_zip.s(instance.pk)
        job.apply()
