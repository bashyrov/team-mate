from time import timezone

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
    tech_stack = models.CharField(max_length=255, blank=True)
    linkedin_url = models.CharField(max_length=255, blank=True)
    portfolio_url = models.CharField(max_length=255, blank=True)
    telegram_contact = models.CharField(max_length=255, blank=True)
    discord_contact = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.username


class Project(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(Developer, related_name='owned_projects', on_delete=models.CASCADE)
    score = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    members = models.ManyToManyField(Developer, related_name='projects', blank=True)

    def __str__(self):
        return self.name


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
    deadline = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    project = models.ForeignKey(Project, related_name='tasks', on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag, blank=True)

    def __str__(self):
        return self.title
