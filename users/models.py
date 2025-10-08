from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Avg
from team_mate import settings
from projects.models import Project, ProjectMembership

user_model = settings.AUTH_USER_MODEL


class Developer(AbstractUser):

    POSITION_CHOICES = [
        ('backend', 'Backend'),
        ('frontend', 'Frontend'),
        ('qa', 'QA'),
        ('designer', 'Designer'),
        ('pm', 'PM'),
        ('mentor', 'Mentor'),
    ]

    position = models.CharField(max_length=50, choices=POSITION_CHOICES, default='backend')
    score = models.FloatField(default=0)
    tech_stack = models.CharField(max_length=255, blank=True)
    linkedin_url = models.CharField(max_length=255, blank=True)
    portfolio_url = models.CharField(max_length=255, blank=True)
    telegram_contact = models.CharField(max_length=255, blank=True)
    discord_contact = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.username

    def avg_project_score(self):
        project_ids = ProjectMembership.objects.filter(user=self).values_list('project_id', flat=True)
        avg_score = Project.objects.filter(id__in=project_ids).aggregate(avg=Avg('score'))['avg']
        return avg_score or 0

    def get_member_of(self, project):
        return ProjectMembership.objects.filter(user=self, project=project).first()

    def is_owner(self, project):
        return project.owner_id == self.id

    def get_tasks(self, project=None):
        qs = self.assigned_tasks.all()

        if project:
            qs = qs.filter(project=project)

        return qs

    def has_permission(self, project, permission):

        if self.is_owner(project):
            return True

        user_membership = self.get_member_of(project)

        if not user_membership:
            return False

        return getattr(user_membership, permission, False)



class DeveloperRatings(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(
        user_model,
        on_delete=models.CASCADE,
        related_name='received_user_ratings'
    )
    user_added = models.ForeignKey(
        user_model,
        on_delete=models.CASCADE,
        related_name='given_user_ratings'
    )
    rating = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def get_avg_rating(user):
        return DeveloperRatings.objects.filter(user=user).aggregate(avg=Avg("rating"))["avg"] or 0
