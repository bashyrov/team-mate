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
from .models import Project, Task, ProjectMembership, ProjectRating, ProjectApplication, \
    ProjectOpenRole
from .forms import ProjectForm, TaskForm, ProjectMembershipFormSet, ProjectMembershipFormUpdate, ProjectMembershipForm, \
    ProjectStageForm, ProjectRatingForm, ProjectApplicationForm, ProjectSearchForm, ProjectOpenRoleForm, \
    ProjectOpenRoleSearchForm, TaskSearchForm
from projects.mixins import TaskPermissionRequiredMixin, ProjectPermissionRequiredMixin, ProjectRatingMixin, \
    ApplicationPermissionRequiredMixin
from django.shortcuts import redirect, get_object_or_404, render

UserModel = get_user_model()


class ProjectListView(ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 10

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


class MyProjectListView(ListView):
    model = Project
    template_name = 'projects/my_projects.html'
    context_object_name = 'projects'

    def get_queryset(self):
        return self.request.user.projects.all()


class ProjectDetailView(DetailView): #TODO: Change Roles
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'
    pk_url_kwarg = "project_pk"

    def get_queryset(self):
        return Project.objects.prefetch_related(
            'tasks__assignee',
            'tasks__tags',
            'projectmembership_set__user',
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object

        memberships = list(project.projectmembership_set.all())

        tasks = Task.objects.filter(project=project)[:8]

        tasks_by_assignee = {}
        for task in project.tasks.all():
            key = task.assignee.username if task.assignee else "Unassigned"
            tasks_by_assignee.setdefault(key, []).append(task)

        current_membership = next(
            (m for m in memberships if m.user == self.request.user),
            None
        )

        user = self.request.user
        can_rate = True
        can_applicate = True
        is_deployed = True if project.development_stage == "deployed" else False
        open_roles = project.open_roles.all()

        if user.is_authenticated:
            is_member = project.projectmembership_set.filter(user=user).exists()
            is_owner = project.owner == user
            is_rated = ProjectRating.objects.filter(project=project, rated_by=user).exists() #TODO: change for real validate
            can_rate = not is_member and not is_owner and not is_rated
            can_applicate = not is_member and not is_owner

        context.update({
            'memberships': memberships,
            'tasks': tasks,
            'open_roles': open_roles,
            'tasks_by_assignee': tasks_by_assignee,
            'current_membership': current_membership,
            'can_rate': can_rate,
            'is_deployed': is_deployed,
            'can_applicate': can_applicate,
            'ratings': project.ratings.all().order_by('-created_at')
        })
        return context

@method_decorator(login_required, name='dispatch')
class ProjectOpenRoleCreateView(ProjectPermissionRequiredMixin,CreateView):  #TODO: Change Roles
    model = ProjectOpenRole
    form_class = ProjectOpenRoleForm
    template_name = "projects/open_roles_form.html"
    pk_url_kwarg = "open_role_pk"
    required_permission = 'manage_open_roles_perm'

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        return super().dispatch(request, *args, **kwargs)

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


class ProjectOpenRoleListView(ListView):
    model = ProjectOpenRole
    paginate_by = 10
    template_name = "projects/project_open_roles_list.html"
    context_object_name = 'open_roles'
    success_url = reverse_lazy('projects:open_roles_list')

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        return super().dispatch(request, *args, **kwargs)

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

        project = get_object_or_404(Project, pk=self.kwargs['project_pk'])

        role_name = self.request.GET.get('role_name', '')

        context['search_form'] = ProjectOpenRoleSearchForm(
            initial={'role_name': role_name}
        )
        context['project'] = project

        return context


@method_decorator(login_required, name='dispatch')
class ProjectOpenRoleDeleteView(ProjectPermissionRequiredMixin, DeleteView):
    model = ProjectOpenRole
    required_permission = 'manage_open_roles_perm'

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=kwargs['project_pk'])
        self.user = request.user

        if not self.has_required_permission():
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({"error": "You do not have permission to delete this role."}, status=403)
            else:
                return render(request, "projects/no_permission.html", {
                    "message": "You do not have permission to delete this role.",
                    "project": self.project,
                })

        return super().dispatch(request, *args, **kwargs)

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

        context["project"] = self.project

        title = self.request.GET.get('title', '')
        assignee = self.request.GET.get('assignee', '')
        status = self.request.GET.get('status', '')

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
        can_edit = False #TODO: use1
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        return context

@method_decorator(login_required, name='dispatch')
class ProjectCreateView(CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'project_pk': self.object.pk})

@method_decorator(login_required, name='dispatch')
class ProjectUpdateView(ProjectPermissionRequiredMixin, UpdateView): #TODO: Change Roles
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_update.html'
    pk_url_kwarg = 'project_pk'
    required_permission = 'edit_project_info_perm'

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'project_pk': self.object.pk})


class ProjectMembershipUpdateView(UpdateView): #TODO:Realize, Validate
    model = ProjectMembership
    template_name = 'projects/project_roles_form.html'
    form_class = ProjectMembershipFormUpdate
    required_permission = 'update_membership_roles_perm'

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.object.pk})

@method_decorator(login_required, name='dispatch')
class ProjectStageUpdateView(ProjectPermissionRequiredMixin, UpdateView): #TODO: Change Roles
    model = Project
    form_class = ProjectStageForm
    template_name = 'projects/project_stage_form.html'
    pk_url_kwarg = 'project_pk'
    required_permission = 'update_project_stage_perm'

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'project_pk': self.object.pk})

@method_decorator(login_required, name='dispatch')
class ProjectRatingCreateView(ProjectRatingMixin, CreateView): #TODO: Change can_rate
    model = ProjectRating
    form_class = ProjectRatingForm
    template_name = 'projects/project_rating_form.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context['project'] = self.project

        return context

    def form_valid(self, form):
        form.instance.project = self.project
        form.instance.rated_by = self.user  #TODO: change for real user
        form.save()

        if self.request.headers.get("HX-Request"):
            return render(self.request, "projects/project_rating_form.html",
                          {"form": ProjectRatingForm(), "project": self.project})

        self.project.update_avg_score()

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'project_pk': self.project.pk})

@method_decorator(login_required, name='dispatch')
class ProjectRolesUpdateView(ProjectPermissionRequiredMixin, UpdateView): #TODO: Change Roles
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
class TaskCreateView(ProjectPermissionRequiredMixin, CreateView): #TODO: Change Roles
    model = Task
    form_class = TaskForm
    template_name = 'projects/task_form.html'
    required_permission = 'add_task_perm'

    def form_valid(self, form):
        assignee = form.cleaned_data.get("assignee")

        form.instance.project = self.project
        form.instance.created_by = self.user

        if assignee: #TODO:chech assignee in project members
            if not ProjectMembership.objects.filter(project=self.project, user=assignee).exists():
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
class TaskUpdateView(TaskPermissionRequiredMixin, UpdateView): #TODO: Change Roles
    model = Task
    form_class = TaskForm
    template_name = 'projects/task_form.html'
    pk_url_kwarg = "task_pk"
    required_permission = 'change_task'

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

    def get_success_url(self):
        return reverse_lazy('projects:task_detail', kwargs={'task_pk': self.kwargs['task_pk'], 'project_pk': self.kwargs['project_pk']})


class ProjectApplicationCreateView(ApplicationPermissionRequiredMixin, CreateView):  #TODO: Change can_applicate
    model = ProjectApplication
    form_class = ProjectApplicationForm
    template_name = "projects/project_application_form.html"
    required_permission = 'add_project_application'

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=self.kwargs["project_pk"])
        self.role = get_object_or_404(ProjectOpenRole, pk=self.kwargs["role_pk"])

        if not request.user.is_authenticated:
            return HttpResponse("""
                <div class='alert alert-warning'>
                    You need to be logged in to perform this action.
                    <a href="{% url 'login' %}?next={request.path}" class="btn btn-primary">Войти</a>
                </div>
            """)

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


class ProjectApplicationListView(ListView):  #TODO: Realize
    model = ProjectApplication
    template_name = "projects/project_application_list.html"
    context_object_name = "applications"
    paginate_by = 10

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=kwargs['project_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return ProjectApplication.objects.filter(project=self.project, status='pending').select_related('user')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        return context


def application_approve(args, **kwargs):  #TODO: Change Roles
    request = args
    pk = kwargs.get('pk')
    application = get_object_or_404(ProjectApplication, pk=pk)
    project = application.project

    if application.status in ['accepted', 'rejected']:
        messages.warning(request, "This application has already been processed.")
        return redirect('projects:applications_list', project.pk)

    try:
        with transaction.atomic():
            if ProjectMembership.objects.filter(project=project, user=application.user).exists() or project.owner == application.user:
                messages.warning(request, f"{application.user.username} is already a member of the project.")
                return redirect('projects:applications_list', project.pk)


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