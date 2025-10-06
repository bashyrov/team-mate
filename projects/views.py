from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, FormView, DeleteView
from .models import Project, Task, ProjectMembership, ProjectRating, ProjectApplication, \
    ProjectOpenRole
from .forms import ProjectForm, TaskForm, ProjectMembershipFormSet, ProjectMembershipFormUpdate, ProjectMembershipForm, \
    ProjectStageForm, ProjectRatingForm, ProjectApplicationForm, ProjectSearchForm, ProjectOpenRoleForm, \
    ProjectOpenRoleSearchForm, TaskSearchForm
from projects.mixins import TaskUpdatePermissionRequiredMixin
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
            'ratings__user_added'
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
            is_rated = ProjectRating.objects.filter(project=project, user_added=user).exists()
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


class ProjectOpenRoleCreateView(CreateView):  #TODO: Change Roles
    model = ProjectOpenRole
    form_class = ProjectOpenRoleForm
    template_name = "projects/open_roles_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        return super().dispatch(request, *args, **kwargs)

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
        return reverse_lazy('projects:project_open_roles_list', kwargs={'project_pk': self.project.pk})


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


class ProjectOpenRoleDeleteView(View): #TODO: Change Roles

    def post(self, request, project_pk, role_pk):
        project = get_object_or_404(Project, pk=project_pk)
        role = get_object_or_404(ProjectOpenRole, pk=role_pk, project=project)

        role.delete()

        project.update_open_to_candidates()

        return JsonResponse({"status": "deleted"})

    def get_success_url(self):
        return reverse_lazy('projects:project_open_roles_list', kwargs={'pk': self.project.pk})


class TaskListView(ListView):
    model = Task
    template_name = "projects/task_list.html"
    context_object_name = "tasks"
    paginate_by = 10

    def get_queryset(self):

        project = get_object_or_404(Project, pk=self.kwargs['project_pk'])

        form = TaskSearchForm(self.request.GET, project=project)
        qs = Task.objects.filter(project_id=project.id)

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

        project = get_object_or_404(Project, pk=self.kwargs["project_pk"])
        context["project"] = project

        title = self.request.GET.get('title', '')
        assignee = self.request.GET.get('assignee', '')
        status = self.request.GET.get('status', '')

        context["search_form"] = TaskSearchForm(
            initial={'title': title,
                     'assignee': assignee,
                     'status': status,
                     },
            project=project
        )
        return context


class TaskDetailView(DetailView):
    model = Task
    template_name = 'projects/task_detail.html'
    context_object_name = 'task'
    pk_url_kwarg = 'task_pk'


class ProjectCreateView(CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class ProjectUpdateView(UpdateView): #TODO: Change Roles
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_update.html'
    pk_url_kwarg = 'project_pk'

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'project_pk': self.object.pk})


class ProjectMembershipUpdateView(UpdateView):
    model = ProjectMembership
    template_name = 'projects/project_roles_form.html'
    form_class = ProjectMembershipFormUpdate

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.object.pk})


class ProjectStageUpdateView(UpdateView): #TODO: Change Roles
    model = Project
    form_class = ProjectStageForm
    template_name = 'projects/project_stage_form.html'
    pk_url_kwarg = 'project_pk'

    def dispatch(self, request, *args, **kwargs):
        user = request.user

        allowed_roles = ['pm', 'mentor', 'lead']

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'project_pk': self.object.pk})


class ProjectRatingCreateView(CreateView): #TODO: Change can_rate
    model = ProjectRating
    form_class = ProjectRatingForm
    template_name = 'projects/project_rating_form.html'

    def dispatch(self, request, *args, **kwargs):

        self.project = get_object_or_404(Project, pk=self.kwargs['project_pk'])

        if self.project.development_stage != 'deployed':
            return HttpResponse(
                "<div class='alert alert-warning'>You can only rate deployed projects.</div>"
            )

        if self.project.members.filter(id=request.user.id).exists() or self.project.owner == request.user:
            return HttpResponse(
                "<div class='alert alert-warning'>You can only rate deployed projects.</div>"
            )

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['project'] = self.project

        return context

    def form_valid(self, form):

        user = get_user_model().objects.first()

        form.instance.project = self.project
        form.instance.user_added = user  #TODO: change for real user
        form.save()

        if self.request.headers.get("HX-Request"):
            return render(self.request, "projects/project_rating_form.html",
                          {"form": ProjectRatingForm(), "project": self.project})

        self.project.update_avg_score()

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'project_pk': self.project.pk})


class ProjectRolesUpdateView(UpdateView): #TODO: Change Roles
    model = Project
    template_name = 'projects/project_roles_form.html'
    form_class = ProjectMembershipFormSet
    pk_url_kwarg = 'project_pk'

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


class TaskCreateView(CreateView): #TODO: Change Roles
    model = Task
    form_class = TaskForm
    template_name = 'projects/task_form.html'

    def dispatch(self, request, *args, **kwargs):

        self.project = get_object_or_404(Project, pk=self.kwargs['project_pk'])

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        project = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        form.instance.project = project

        assignee = form.cleaned_data.get("assignee")
        user = self.request.user

        form.instance.created_by = user  #TODO:change for real

        if assignee:
            if not ProjectMembership.objects.filter(project=project, user=assignee).exists():
                raise PermissionDenied("Assignee must be a member of this project.")

        return super().form_valid(form)

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        project = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        form.fields['assignee'].queryset = get_user_model().objects.filter(
        memberships__project=project
    )
        return form

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'project_pk': self.kwargs['project_pk']})


class TaskUpdateView(TaskUpdatePermissionRequiredMixin, UpdateView): #TODO: Change Roles
    model = Task
    form_class = TaskForm
    template_name = 'projects/task_form.html'
    pk_url_kwarg = "task_pk"

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        project = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        form.fields['assignee'].queryset = get_user_model().objects.filter(
            memberships__project=project
        )
        return form

    def form_valid(self, form):
        project = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        form.instance.project = project

        assignee = form.cleaned_data.get("assignee")
        if assignee:
            if not ProjectMembership.objects.filter(project=project, user=assignee).exists():
                raise PermissionDenied("Assignee must be a member of this project.")

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'project_pk': self.kwargs['project_pk']})


class ProjectApplicationCreateView(CreateView):  #TODO: Change can_applicate
    model = ProjectApplication
    form_class = ProjectApplicationForm
    template_name = "projects/project_application_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=self.kwargs["pk"])

        if not request.user.is_authenticated:
            return HttpResponse("""
                <div class='alert alert-warning'>
                    You need to be logged in to perform this action.
                    <a href="{% url 'login' %}?next={request.path}" class="btn btn-primary">Войти</a>
                </div>
            """)

        if self.project.members.filter(id=request.user.id).exists() or self.project.owner == request.user:
            raise PermissionDenied("You cannot apply to your own project.")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.project_id = self.kwargs["pk"]
        form.instance.user = self.request.user
        form.save()
        return HttpResponse(status=204)

    def get_success_url(self):
        return reverse_lazy("projects:project_detail", kwargs={"pk": self.project.pk})


def index(request):
    return None