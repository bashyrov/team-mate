from django.contrib import admin
from .models import (
    Project,
    ProjectMembership,
    ProjectRating,
    Task,
    ProjectOpenRole,
    ProjectApplication,
    Tag
)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'domain', 'development_stage', 'score', 'open_to_candidates', 'created_at')
    list_filter = ('domain', 'development_stage', 'open_to_candidates')
    search_fields = ('name', 'description', 'owner__username')
    readonly_fields = ('score', 'created_at')


@admin.register(ProjectMembership)
class ProjectMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'role', 'joined_at')
    list_filter = ('role',)
    search_fields = ('user__username', 'project__name')


@admin.register(ProjectRating)
class ProjectRatingAdmin(admin.ModelAdmin):
    list_display = ('project', 'rated_by', 'score', 'comment', 'created_at')
    list_filter = ('score',)
    search_fields = ('project__name', 'rated_by__username', 'comment')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'assignee', 'status', 'deadline', 'created_at')
    list_filter = ('status', 'project')
    search_fields = ('title', 'description', 'assignee__username')


@admin.register(ProjectOpenRole)
class ProjectOpenRoleAdmin(admin.ModelAdmin):
    list_display = ('role_name', 'project', 'created_at')
    search_fields = ('role_name', 'project__name')


@admin.register(ProjectApplication)
class ProjectApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'role', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('user__username', 'project__name', 'role__role_name')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
