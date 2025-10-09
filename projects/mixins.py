from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect

from projects.models import ProjectMembership, Project, Task, ProjectApplication, ProjectOpenRole


class BasePermissionMixin:
    required_permission = None

    def is_owner(self):
        return self.user == self.project.owner

    def is_member(self):
        return self.user == self.project.owner or self.project.members.filter(id=self.user.id).exists()

    def applied_to_project(self):
        return self.project.applications.filter(user=self.user, status='pending', role=self.role).exists()

    def is_rated(self):
        return self.user.given_project_ratings.filter(project=self.project).exists()

    def is_project_deployed(self):
        return self.project.development_stage == 'deployed'

    def can_edit_task(self):
        return self.user == self.task.created_by or self.user == self.task.assignee

    def dispatch(self, request, *args, **kwargs):

        self.user = request.user

        if 'project_pk' in kwargs:
            self.project = get_object_or_404(Project, pk=kwargs['project_pk'])
        if 'task_pk' in kwargs:
            self.task = get_object_or_404(Task, pk=kwargs['task_pk'])
        if 'role_pk' in kwargs:
            self.role = get_object_or_404(ProjectOpenRole, pk=kwargs['role_pk'])

        return super().dispatch(request, *args, **kwargs)

class ProjectPermissionRequiredMixin(BasePermissionMixin):

    def has_required_permission(self):

        if not self.required_permission:
            return True

        if self.is_owner():
            return True

        has_permission = False

        try:
            user_obj = self.user.get_member_of(self.project)
            has_permission = getattr(user_obj, self.required_permission)
        except Exception as e:
            return has_permission

        return has_permission

    def dispatch(self, request, *args, **kwargs):

        response = super().dispatch(request, *args, **kwargs)

        if not self.has_required_permission():
            return render(request, "projects/no_permission.html", {
                "message": "You do not have permission to access this page.",
                "project": self.project,
            })

        return response


class ProjectRatingPermissionMixin(BasePermissionMixin):

    def dispatch(self, request, *args, **kwargs):

        response = super().dispatch(request, *args, **kwargs)

        if self.is_member():
            return render(request, "projects/no_permission.html", {
                "message": "You cannot rate your own project.",
                "project": self.project,
            })

        if self.is_rated():
            return render(request, "projects/no_permission.html", {
                "message": "You already rate this project.",
                "project": self.project,
            })

        if not self.is_project_deployed():
            return render(request, "projects/no_permission.html", {
                "message": "You can only rate deployed projects.",
                "project": self.project,
            })

        return response


class TaskPermissionRequiredMixin(BasePermissionMixin):

    def has_required_permission(self):

        if not self.required_permission:
            return True

        if self.is_owner():
            return True

        if self.required_permission == 'view_task' and (self.is_owner() or self.is_member() or self.task.assignee == self.user):
            return True

        if self.required_permission == 'update_task' and self.can_edit_task():
            return True
        return False

    def dispatch(self, request, *args, **kwargs):

        response = super().dispatch(request, *args, **kwargs)

        if not self.has_required_permission():
            return render(request, "projects/no_permission.html", {
                "message": "You do not have permission to access this page.",
                "task": self.task,
            })

        return response


class ApplicationPermissionRequiredMixin(BasePermissionMixin):

    def dispatch(self, request, *args, **kwargs):

        response = super().dispatch(request, *args, **kwargs)

        if self.is_member() or self.is_owner():
            messages.warning(request, "You cannot apply your own project.")
            return redirect('projects:project_open_roles_list', self.project.pk)

        if self.applied_to_project():
            messages.warning(request, "Your application to join this project is currently under review.")
            return redirect('projects:project_open_roles_list', self.project.pk)

        return response


class MembershipPermissionRequiredMixin(BasePermissionMixin):

    def dispatch(self, request, *args, **kwargs):

        response = super().dispatch(request, *args, **kwargs)

        if not self.is_member():
            return render(request, "projects/no_permission.html", {
                "message": "You must be a project member to access this page.",
                "project": self.project,
            })
        return response
