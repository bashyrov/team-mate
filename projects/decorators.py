from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404

from projects.models import ProjectMembership, ProjectApplication, Project


def validate_permissions_application_review(func):
    def wrapper(request, *args, **kwargs):
        user = request.user
        project = get_object_or_404(Project, pk=kwargs["project_pk"])

        if user.is_anonymous:
            messages.warning(
                request, "You must be logged in to review applications."
            )
            return redirect("projects:applications_list", project.pk)

        membership_opj = ProjectMembership.objects.filter(
            user=user, project=project
        ).first()

        has_permission = membership_opj.has_permission(
            "manage_open_roles_perm"
        )
        if not has_permission:
            messages.warning(
                request,
                "You do not have permission to review this application.",
            )
            return redirect("projects:applications_list", project.pk)

        kwargs["project"] = project
        return func(request, *args, **kwargs)

    return wrapper


def validate_application_status(func):
    def wrapper(request, *args, **kwargs):
        application_pk = kwargs.get("application_pk")
        application = get_object_or_404(ProjectApplication, pk=application_pk)
        project = application.project

        if application.status in ["approved", "rejected"]:
            messages.warning(
                request, "This application has already been processed."
            )
            return redirect("projects:applications_list", project.pk)

        kwargs["application"] = application
        return func(request, *args, **kwargs)

    return wrapper


def validate_is_member(func):
    def wrapper(request, *args, **kwargs):
        print("Validating is member...")
        application = kwargs["application"]
        project = application.project

        if (
            ProjectMembership.objects.filter(
                project=project, user=application.user
            ).exists()
            or project.owner == application.user
        ):
            messages.warning(
                request,
                f"{application.user.username} "
                f"is already a member of the project.",
            )
            return redirect("projects:applications_list", project.pk)

        return func(request, *args, **kwargs)

    return wrapper
