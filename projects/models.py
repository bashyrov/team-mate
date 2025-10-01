from django.contrib.auth import get_user_model
from team_mate import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Avg

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


class ProjectManager(models.Manager):
    def validate_stage(self, project):
        if project.development_stage == 'deployed' and not project.deploy_url:
            raise ValidationError({
                'stage': 'Cannot set stage to "Deployed" without a deploy URL.'
            })
        return True


class ProjectRating(models.Model):
    project = models.ForeignKey('Project', related_name='ratings', on_delete=models.CASCADE)
    user = models.ForeignKey(user_model, on_delete=models.CASCADE)
    user_added = models.ForeignKey(
        user_model,
        on_delete=models.CASCADE,
        related_name='given_project_ratings'
    )
    score = models.IntegerField()  # например, 1–5
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def get_avg_rating(project):
        return ProjectRating.objects.filter(project=project).aggregate(
            avg=Avg("score"))["avg"] or 0


class Project(models.Model):

    DEVELOPMENT_STAGE_CHOICES = [
        ('initiation', 'Project Initiation'),
        ('planning', 'Planning'),
        ('design', 'Design & Architecture'),
        ('implementation', 'Implementation / Development'),
        ('testing', 'Testing & QA'),
        ('completed', 'Completed'),
        ('deployed', 'Deployed'),
    ]

    DOMEN_CHOICES = [
        ('marketing', 'Marketing'),
        ('blockchain', 'Blockchain'),
        ('food_tech', 'Food Tech'),
        ('technology', 'Technology'),
        ('e_commerce', 'E-Commerce'),
        ('ed_tech', 'EdTech'),
        ('utilities', 'Utilities'),
        ('design', 'Design'),
        ('saas', 'SaaS'),
        ('fintech', 'FinTech'),
        ('ml', 'Machine Learning'),
        ('big_data', 'Big Data'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    domen = models.CharField(max_length=50, choices=DOMEN_CHOICES, default='backend')
    development_stage = models.CharField(max_length=50, choices=DEVELOPMENT_STAGE_CHOICES, default='backend')
    deploy_url = models.CharField(max_length=255, blank=True)
    owner = models.ForeignKey(Developer, related_name='owned_projects', on_delete=models.CASCADE)
    open_to_candidates = models.BooleanField(default=True)
    unical_id = models.CharField(max_length=255, default='unical_id')
    score = models.FloatField(default=0)
    project_url = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    members = models.ManyToManyField(
        get_user_model(),
        through="ProjectMembership",
        related_name="projects"
    )

    objects = ProjectManager()

    @property
    def avg_score(self):
        return round(ProjectRating.get_avg_rating(self), 2)

    def save(self, *args, **kwargs):
        Project.objects.validate_stage(self)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProjectMembership(models.Model):
    ROLE_CHOICES = [
        ("DEV", "Developer"),
        ("LEAD", "Team Lead"),
        ("PM", "Project Manager"),
        ("Mentor", "Mentor"),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(user_model, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="DEV")

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("project", "user")

    def __str__(self):
        return f"{self.user.username} in {self.project.name} as {self.get_role_display()}"


class Tag(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Task(models.Model):
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ]
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='todo')
    assignee = models.ForeignKey(user_model, related_name='assigned_tasks', on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(user_model, related_name='created_tasks', on_delete=models.SET_NULL, null=True, blank=True)
    deadline = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    project = models.ForeignKey(Project, related_name='tasks', on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag, blank=True)

    def __str__(self):
        return self.title


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


class NewCandidates(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

