from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models


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

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    development_stage = models.CharField(max_length=50, choices=DEVELOPMENT_STAGE_CHOICES, default='backend')
    deploy_url = models.CharField(max_length=255, blank=True)
    owner = models.ForeignKey(Developer, related_name='owned_projects', on_delete=models.CASCADE)
    score = models.FloatField(default=0)
    project_url = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    members = models.ManyToManyField(
        get_user_model(),
        through="ProjectMembership",
        related_name="projects"
    )

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
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
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
    assignee = models.ForeignKey(Developer, related_name='tasks', on_delete=models.SET_NULL, null=True, blank=True)
    deadline = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    project = models.ForeignKey(Project, related_name='tasks', on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag, blank=True)

    def __str__(self):
        return self.title
