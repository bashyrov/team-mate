from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, FormView, DeleteView

from .decorators import validate_permissions_application_review, validate_application_status, validate_is_member
from .models import Project, Task, ProjectMembership, ProjectRating, ProjectApplication, \
    ProjectOpenRole
from .forms import ProjectForm, TaskForm, ProjectMembershipFormSet, ProjectMembershipFormUpdate, ProjectMembershipForm, \
    ProjectStageForm, ProjectRatingForm, ProjectApplicationForm, ProjectSearchForm, ProjectOpenRoleForm, \
    ProjectOpenRoleSearchForm, TaskSearchForm, MyTaskSearchForm
from projects.mixins import TaskPermissionRequiredMixin, ProjectPermissionRequiredMixin, ProjectRatingPermissionMixin, \
    ApplicationPermissionRequiredMixin, MembershipPermissionRequiredMixin, BasePermissionMixin
from django.shortcuts import redirect, get_object_or_404, render

UserModel = get_user_model()


class ProjectListView(ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 10
    view_type = 'all_projects'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(ProjectListView, self).get_context_data(**kwargs)

        project_name = self.request.GET.get('project_name', '')
        development_stage = self.request.GET.get('development_stage', '')
        domain = self.request.GET.get('domain', '')
        open_to_candidates = self.request.GET.get('open_to_candidates', '')

        context["search_form"] = ProjectSearchForm(
            initial={'project_name': project_name,
                     'development_stage': development_stage,
                     'domain': domain,
                     'open_to_candidates': open_to_candidates
                     }
        )
        return context

    def get_queryset(self):

        qs = Project.objects.all()

        form = ProjectSearchForm(self.request.GET)

        if form.is_valid():
            project_name = form.cleaned_data.get('project_name')
            development_stage = form.cleaned_data.get('development_stage')
            domain = form.cleaned_data.get('domain')
            open_to_candidates = form.cleaned_data.get('open_to_candidates')

            if project_name:
                qs = qs.filter(name__icontains=project_name)
            if development_stage:
                qs = qs.filter(development_stage=development_stage)
            if domain:
                qs = qs.filter(domain=domain)
            if open_to_candidates:
                qs = qs.filter(open_to_candidates=True)

        return qs

@method_decorator(login_required, name='dispatch')
class MyProjectListView(ListView):
    model = Project
    template_name = 'projects/my_projects.html'
    context_object_name = 'projects'
    paginate_by = 10

    def get_queryset(self):
        qs = (self.request.user.projects.all() | self.request.user.owned_projects.all()).distinct()
        return qs


@method_decorator(login_required, name='dispatch')
class MyTasksListView(ListView):
    model = Task
    template_name = 'projects/my_task_list.html'
    context_object_name = 'tasks'
    paginate_by = 10
    view_type = 'my_tasks'

    def get_queryset(self):
        user = self.request.user
        qs = Task.objects.filter(assignee=user)

        form = MyTaskSearchForm(self.request.GET, user=user)
        if form.is_valid():
            title = form.cleaned_data.get('title')
            status = form.cleaned_data.get('status')

            if title:
                qs = qs.filter(title__icontains=title)
            if status:
                qs = qs.filter(status=status)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['search_form'] = MyTaskSearchForm(
            self.request.GET or None,
            user=self.request.user
        )

        context['view_type'] = self.view_type
        return context


class ProjectDetailView(DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'
    pk_url_kwarg = "project_pk"

    def get_queryset(self):
        return (
            Project.objects
            .select_related('owner')
            .prefetch_related(
                'tasks__tags',
                'projectmembership_set__user',
                'ratings__rated_by',
                'open_roles',
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        user = self.request.user

        memberships = list(project.projectmembership_set.all())
        tasks = Task.objects.filter(project=project)[:8]
        open_roles = project.open_roles.all()[:3]
        is_deployed = project.development_stage == "deployed"

        is_owner = False
        is_member = False
        can_rate = False
        user_permissions = {}

        if user.is_authenticated:
            membership = user.get_member_of(project)
            is_owner = project.owner == user
            is_member = membership is not None

            if membership:
                permissions = [
                    'edit_project_info_perm',
                    'add_task_perm',
                    'update_project_stage_perm',
                    'manage_open_roles_perm'
                ]
                user_permissions = {perm: getattr(membership, perm, False) for perm in permissions}

            is_rated = ProjectRating.objects.filter(project=project, rated_by=user).exists()
            can_rate = not (is_member and is_owner and is_rated)

        context.update({
            **user_permissions,
            'memberships': memberships,
            'tasks': tasks,
            'open_roles': open_roles,
            'is_owner': is_owner,
            'is_member': is_member,
            'can_rate': can_rate,
            'is_deployed': is_deployed,
            'ratings': project.ratings.all().order_by('-created_at'),
        })

        return context


@method_decorator(login_required, name='dispatch')
class ProjectOpenRoleCreateView(ProjectPermissionRequiredMixin,CreateView):
    model = ProjectOpenRole
    form_class = ProjectOpenRoleForm
    template_name = "projects/open_roles_form.html"
    pk_url_kwarg = "open_role_pk"
    required_permission = 'manage_open_roles_perm'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        return context

    def form_valid(self, form):
        form.instance.project = self.project
        form.instance.user = self.request.user
        form.save()
        self.project.update_open_to_candidates()

        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string(self.template_name, {'form': form}, self.request)
            return JsonResponse({'success': False, 'html': html})
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('projects:project_open_roles_list', kwargs={'project_pk': self.project.pk,})


class ProjectOpenRoleListView(BasePermissionMixin, ListView):
    model = ProjectOpenRole
    paginate_by = 10
    template_name = "projects/project_open_roles_list.html"
    context_object_name = 'open_roles'
    success_url = reverse_lazy('projects:open_roles_list')

    def get_queryset(self):

        qs = ProjectOpenRole.objects.all().filter(project=self.project)

        form = ProjectOpenRoleSearchForm(self.request.GET)

        if form.is_valid():
            role_name = form.cleaned_data.get('role_name')
            if role_name:
                qs = qs.filter(role_name=role_name)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        role_name = self.request.GET.get('role_name', '')

        user_permissions = {}
        is_owner = False
        is_member = False

        if self.user.is_authenticated:
            membership = self.user.get_member_of(self.project)
            is_owner = self.project.owner == self.user
            is_member = membership is not None

            if membership:
                permissions = [
                    'manage_open_roles_perm'
                ]

                user_permissions = {perm: getattr(membership, perm, False) for perm in permissions}

        context['search_form'] = ProjectOpenRoleSearchForm(
            initial={'role_name': role_name}
        )
        context['project'] = self.project
        context.update({
            **user_permissions,
            'is_owner': is_owner,
            'is_member': is_member,
        })

        return context


@method_decorator(login_required, name='dispatch')
class ProjectOpenRoleDeleteView(ProjectPermissionRequiredMixin, DeleteView):
    model = ProjectOpenRole
    required_permission = 'manage_open_roles_perm'

    def get_object(self, queryset=None):
        return get_object_or_404(ProjectOpenRole, pk=self.kwargs['role_pk'], project=self.project)

    def delete(self, request, *args, **kwargs):
        role = self.get_object()
        role.delete()
        self.project.update_open_to_candidates()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({"status": "deleted"})
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('projects:project_open_roles_list', kwargs={'project_pk': self.project.pk})


class TaskListView(ListView):
    model = Task
    template_name = "projects/task_list.html"
    context_object_name = "tasks"
    paginate_by = 10

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=kwargs['project_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        form = TaskSearchForm(self.request.GET, project=self.project)
        qs = Task.objects.filter(project_id=self.project.id)

        if form.is_valid():
            title = form.cleaned_data.get('title')
            assignee = form.cleaned_data.get('assignee')
            status = form.cleaned_data.get('status')

            if title:
                qs = qs.filter(title__icontains=title)
            if assignee:
                qs = qs.filter(assignee=assignee)
            if status:
                qs = qs.filter(status=status)

        return qs

    def get_context_data(self, **kwargs):
        context = super(TaskListView, self).get_context_data(**kwargs)

        self.user = self.request.user

        title = self.request.GET.get('title', '')
        assignee = self.request.GET.get('assignee', '')
        status = self.request.GET.get('status', '')

        user_permissions = {}
        is_owner = False
        is_member = False

        if self.user.is_authenticated:
            membership = self.user.get_member_of(self.project)
            is_owner = self.project.owner == self.user
            is_member = membership is not None

            if membership:
                permissions = [
                    'add_task_perm'
                ]

                user_permissions = {perm: getattr(membership, perm, False) for perm in permissions}

        context["project"] = self.project
        context.update({**user_permissions,
                        'is_owner': is_owner,
                        'is_member': is_member,
                        })

        context["search_form"] = TaskSearchForm(
            initial={'title': title,
                     'assignee': assignee,
                     'status': status,
                     },
            project=self.project
        )
        return context

@method_decorator(login_required, name='dispatch')
class TaskDetailView(TaskPermissionRequiredMixin, DetailView):
    model = Task
    template_name = 'projects/task_detail.html'
    context_object_name = 'task'
    pk_url_kwarg = 'task_pk'
    required_permission = 'view_task'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        update_task_perm = (self.object.assignee == self.request.user or
                            self.object.created_by == self.request.user or
                            self.user.is_owner(self.project))

        if not hasattr(self, 'project'):
            self.project = get_object_or_404(Project, pk=self.object.project.pk)
            context['view_type'] = 'my_tasks'

        context['project'] = self.project
        context['update_task_perm'] = update_task_perm

        return context

@method_decorator(login_required, name='dispatch')
class ProjectCreateView(CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'

    def form_valid(self, form):
        form.instance.owner = self.request.user

        response = super().form_valid(form)

        ProjectMembership.objects.create(
            project=self.object,
            user=self.request.user,
            role='No Role',
        )

        return response

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'project_pk': self.object.pk})

@method_decorator(login_required, name='dispatch')
class ProjectUpdateView(ProjectPermissionRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_update.html'
    pk_url_kwarg = 'project_pk'
    required_permission = 'edit_project_info_perm'

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'project_pk': self.object.pk})

@method_decorator(login_required, name='dispatch')
class ProjectMembershipUpdateView(ProjectPermissionRequiredMixin, UpdateView):
    model = ProjectMembership
    template_name = 'projects/project_roles_form.html'
    form_class = ProjectMembershipFormUpdate
    required_permission = 'update_membership_roles_perm'

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.object.pk})

@method_decorator(login_required, name='dispatch')
class ProjectStageUpdateView(ProjectPermissionRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectStageForm
    template_name = 'projects/project_stage_form.html'
    pk_url_kwarg = 'project_pk'
    required_permission = 'update_project_stage_perm'

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'project_pk': self.object.pk})

@method_decorator(login_required, name='dispatch')
class ProjectRatingCreateView(ProjectRatingPermissionMixin, CreateView):
    model = ProjectRating
    form_class = ProjectRatingForm
    template_name = 'projects/project_rating_form.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context['project'] = self.project

        return context

    def form_valid(self, form):
        form.instance.project = self.project
        form.instance.rated_by = self.user
        form.save()

        if self.request.headers.get("HX-Request"):
            return render(self.request, "projects/project_rating_form.html",
                          {"form": ProjectRatingForm(), "project": self.project})

        self.project.update_avg_score()

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'project_pk': self.project.pk})

@method_decorator(login_required, name='dispatch')
class ProjectRolesUpdateView(ProjectPermissionRequiredMixin, UpdateView):
    model = Project
    template_name = 'projects/project_roles_form.html'
    form_class = ProjectMembershipFormSet
    pk_url_kwarg = 'project_pk'
    required_permission = 'update_project_roles_perm'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            formset = ProjectMembershipFormSet(
                self.request.POST,
                instance=self.object,
                form_kwargs={'project': self.object}
            )
        else:
            formset = ProjectMembershipFormSet(
                instance=self.object,
                form_kwargs={'project': self.object}
            )
        context['formset'] = formset
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        formset = ProjectMembershipFormSet(
            self.request.POST,
            instance=self.object,
            form_kwargs={'project': self.object}
        )
        if formset.is_valid():
            formset.save()
            return redirect(self.get_success_url())

        return self.render_to_response(self.get_context_data(formset=formset))

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'project_pk': self.object.pk})

@method_decorator(login_required, name='dispatch')
class TaskCreateView(ProjectPermissionRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'projects/task_form.html'
    required_permission = 'add_task_perm'

    def form_valid(self, form):
        assignee = form.cleaned_data.get("assignee")

        form.instance.project = self.project
        form.instance.created_by = self.user

        if assignee:
            if not assignee.get_member_of(self.project):
                raise PermissionDenied("Assignee must be a member of this project.")

        return super().form_valid(form)

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields['assignee'].queryset = get_user_model().objects.filter(
        memberships__project=self.project
    )
        return form

    def get_success_url(self):
        return reverse_lazy('projects:task_detail', kwargs={'project_pk': self.project.pk, 'task_pk': self.object.pk})

@method_decorator(login_required, name='dispatch')
class TaskUpdateView(TaskPermissionRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'projects/task_form.html'
    pk_url_kwarg = "task_pk"
    required_permission = 'update_task'

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields['assignee'].queryset = get_user_model().objects.filter(
            memberships__project=self.project
        )
        return form

    def form_valid(self, form):
        form.instance.project = self.project

        assignee = form.cleaned_data.get("assignee")
        if assignee:
            if not ProjectMembership.objects.filter(project=self.project, user=assignee).exists():
                raise PermissionDenied("Assignee must be a member of this project.")

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project

        return context

    def get_success_url(self):
        return reverse_lazy('projects:task_detail', kwargs={'task_pk': self.kwargs['task_pk'], 'project_pk': self.kwargs['project_pk']})


@method_decorator(login_required, name='dispatch')
class ProjectApplicationCreateView(ApplicationPermissionRequiredMixin, CreateView):
    model = ProjectApplication
    form_class = ProjectApplicationForm
    template_name = "projects/project_application_form.html"
    required_permission = 'add_project_application'

    def dispatch(self, request, *args, **kwargs):
        self.role = get_object_or_404(ProjectOpenRole, pk=self.kwargs["role_pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.project = self.project
        form.instance.user = self.request.user
        form.save()

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("projects:project_detail", kwargs={"project_pk": self.project.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        context['role'] = self.role
        return context


@method_decorator(login_required, name='dispatch')
class ProjectApplicationListView(MembershipPermissionRequiredMixin, ListView):  #TODO: Realize
    model = ProjectApplication
    template_name = "projects/project_application_list.html"
    context_object_name = "applications"
    paginate_by = 10
    view_type = 'active'
    required_permission = 'view_project_applications'

    def get_queryset(self):

        qs = ProjectApplication.objects.filter(project=self.project)
        self.view_type = getattr(self, 'view_type', 'active')

        if self.view_type == 'active':
            qs = qs.filter(status='pending')
        elif self.view_type == 'archive':
            qs = qs.filter(status__in=['accepted', 'rejected'])

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['view_type'] = self.view_type
        context['project'] = self.project
        return context

@login_required
@validate_permissions_application_review
@validate_application_status
@validate_is_member
def application_approve(request, **kwargs):  #TODO: Change Roles
    application = kwargs.get('application')
    project = application.project

    try:
        with transaction.atomic():
            ProjectMembership.objects.create(
                project=project,
                user=application.user,
                role=application.role,
            )

            application.status = 'accepted'
            application.save(update_fields=['status'])

            messages.success(request, f"{application.user.username} has been added to the project!")

    except Exception as ex:
        messages.error(request, "An error occurred while approving the application.")

    return redirect('projects:applications_list', project.pk)

@validate_permissions_application_review
@validate_application_status
@login_required
def application_reject(request, **kwargs):  #TODO: Change Roles
    application = kwargs.get('application')
    project = application.project

    try:
        with transaction.atomic():
            application.status = 'rejected'
            application.save(update_fields=['status'])

            messages.success(request, f"{application.user.username} application has rejected!")

    except Exception as ex:
        messages.error(request, "An error occurred while rejecting the application.")

    return redirect('projects:applications_list', project.pk)