from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Avg
from team_mate.settings import base
from projects.models import Project, ProjectMembership

user_model = base.AUTH_USER_MODEL


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
    avg_projects_score = models.DecimalField(default=0, decimal_places=2, max_digits=3)
    linkedin_url = models.URLField(max_length=255, blank=True)
    portfolio_url = models.URLField(max_length=255, blank=True)
    github_url = models.URLField(max_length=255, blank=True)
    behance_url = models.URLField(max_length=255, blank=True)
    telegram_contact = models.CharField(max_length=255, blank=True)
    discord_contact = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.username

    def set_avg_project_score(self):
        project_ids = ProjectMembership.objects.filter(user=self).values_list('project_id', flat=True)
        avg_score = Project.objects.filter(id__in=project_ids).aggregate(avg=Avg('score'))['avg'] or 0
        self.avg_projects_score = round(avg_score, 2)

    def get_member_of(self, project):
        return ProjectMembership.objects.filter(user=self, project=project).first()

    def is_owner(self, project):
        return project.owner_id == self.id

    def get_tasks(self, project=None):
        qs = self.assigned_tasks.all()

        if project:
            qs = qs.filter(project=project)

        return qs


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
