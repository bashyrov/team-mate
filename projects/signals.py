from django.db.models.signals import post_save
from django.dispatch import receiver

from projects.models import ProjectRating


@receiver(post_save, sender=ProjectRating)
def update_avg_score_signal(sender, instance, created, **kwargs):
    if created:
        project = instance.project
        project.update_avg_score()

