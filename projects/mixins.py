from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render

from projects.models import ProjectMembership, Project, Task


class ProjectPermissionRequiredMixin:
    required_permission = None

    def has_required_permission(self, user, project):
        if not self.required_permission:
            return True

        has_permission = False

        try:
            membership = ProjectMembership.objects.get(user=user, project=project)
            has_permission = hasattr(membership, "name")
            return has_permission
        except ProjectMembership.DoesNotExist:
            return has_permission


class TaskUpdatePermissionRequiredMixin:

    def has_required_permission(self, user, task):
        if user == task.created_by or user == task.assignee or user == task.project.owner:
            return True
        return False

    def dispatch(self, request, *args, **kwargs):
        task = get_object_or_404(Task, pk=kwargs['task_pk'])

        if not self.has_required_permission(request.user, task):
            return render(request, "projects/no_permission.html", {
                "message": "You do not have permission to access this page.",
                "task": task,
            })

        return super().dispatch(request, *args, **kwargs)
