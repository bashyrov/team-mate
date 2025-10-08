from team_mate import settings
from django.db import models
from django.db.models import Avg
from projects.service.managers import ProjectManager

user_model = settings.AUTH_USER_MODEL


class ProjectRating(models.Model):
    project = models.ForeignKey('Project', related_name='ratings', on_delete=models.CASCADE)
    rated_by = models.ForeignKey(
        user_model,
        on_delete=models.CASCADE,
        related_name='given_project_ratings'
    )
    score = models.IntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Project(models.Model):

    DEVELOPMENT_STAGE_CHOICES = [
        ('initiation', 'Project Initiation'),
        ('planning', 'Planning'),
        ('design', 'Design & Architecture'),
        ('implementation', 'Implementation / Development'),
        ('testing', 'Testing & QA'),
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
    domain = models.CharField(max_length=50, choices=DOMEN_CHOICES, default='backend')
    development_stage = models.CharField(max_length=50, choices=DEVELOPMENT_STAGE_CHOICES, default='initiation')
    deploy_url = models.CharField(max_length=255, blank=True)
    owner = models.ForeignKey(user_model, related_name='owned_projects', on_delete=models.CASCADE)
    open_to_candidates = models.BooleanField(default=False)
    unical_id = models.CharField(max_length=255, default='unical_id')
    score = models.FloatField(default=0)
    project_url = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    members = models.ManyToManyField(
        user_model,
        through="ProjectMembership",
        related_name="projects"
    )

    objects = ProjectManager()

    def update_open_to_candidates(self):
        has_roles = self.open_roles.exists()
        if self.open_to_candidates != has_roles:
            self.open_to_candidates = has_roles

            self.save(update_fields=['open_to_candidates'])

        return self.open_to_candidates


    def get_members(self):
        return self.members.all()

    def update_avg_score(self):
        avg = self.ratings.aggregate(avg=Avg("score"))["avg"] or 0
        self.score = round(avg, 2)
        self.save(update_fields=['score'])

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
    user = models.ForeignKey(user_model, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="DEV")
    edit_project_info_perm = models.BooleanField(default=False)
    add_task_perm = models.BooleanField(default=False)
    update_project_stage_perm = models.BooleanField(default=False)
    manage_open_roles_perm = models.BooleanField(default=False)

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("project", "user")

    def has_permission(self, perm_name) -> bool:
        return getattr(self, perm_name, False)

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


class ProjectOpenRole(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="open_roles")
    role_name = models.CharField(max_length=100)
    message = models.TextField(blank=True, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project.name} - {self.role_name}"


class ProjectApplication(models.Model):

    APPLICATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="applications")
    user = models.ForeignKey(user_model, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True)
    role = models.CharField(max_length=10, choices=ProjectMembership.ROLE_CHOICES, default="DEV")
    created_at = models.DateTimeField(auto_now_add=True)
