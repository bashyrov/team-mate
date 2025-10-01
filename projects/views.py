from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, FormView
from .models import Project, Task, Developer, ProjectMembership, ProjectRating, DeveloperRatings
from .forms import ProjectForm, TaskForm, ProjectMembershipFormSet, ProjectMembershipFormUpdate, ProjectMembershipForm, \
    ProjectStageForm, ProjectRatingForm
from django.shortcuts import redirect, get_object_or_404, render
from django.db.models import Avg


class ProjectListView(ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'


class MyProjectListView(ListView):
    model = Project
    template_name = 'projects/my_projects.html'
    context_object_name = 'projects'

    def get_queryset(self):
        return self.request.user.projects.all()


class ProjectDetailView(DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'

    def get_queryset(self):
        return Project.objects.prefetch_related(
            'tasks__assignee',
            'tasks__tags',
            'projectmembership_set__user',
            'ratings__user'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object

        memberships = list(project.projectmembership_set.all())

        tasks_by_assignee = {}
        for task in project.tasks.all():
            key = task.assignee.username if task.assignee else "Unassigned"
            tasks_by_assignee.setdefault(key, []).append(task)

        current_membership = next(
            (m for m in memberships if m.user == self.request.user),
            None
        )

        user = self.request.user
        can_rate = False

        if user.is_authenticated:
            is_member = project.projectmembership_set.filter(user=user).exists()
            is_owner = project.owner == user
            is_rated = ProjectRating.objects.filter(project=project, user=user).exists()
            can_rate = not is_member and not is_owner and not is_rated

        context.update({
            'memberships': memberships,
            'tasks_by_assignee': tasks_by_assignee,
            'current_membership': current_membership,
            'can_rate': can_rate,
            'ratings': project.ratings.all().order_by('-created_at')
        })
        return context


class TaskDetailView(DetailView):
    model = Task
    template_name = 'projects/task_detail.html'
    context_object_name = 'task'


class ProjectCreateView(CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class ProjectUpdateView(UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_update.html'

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.object.pk})


class ProjectMembershipUpdateView(UpdateView):
    model = ProjectMembership
    template_name = 'projects/project_roles_form.html'
    form_class = ProjectMembershipFormUpdate

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.object.pk})


class ProjectStageUpdateView(UpdateView):
    model = Project
    form_class = ProjectStageForm
    template_name = 'projects/project_stage_form.html'

    def dispatch(self, request, *args, **kwargs):
        project = self.get_object()
        user = request.user

        allowed_roles = ['pm', 'mentor', 'lead']

        if not user.is_authenticated:
            raise PermissionDenied("Необходимо войти в систему.")

        if not hasattr(user, "role") or user.role not in allowed_roles:
            raise PermissionDenied("У вас нет прав для обновления стадии проекта.")

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.object.pk})


class ProjectRatingCreateView(CreateView):
    model = ProjectRating
    form_class = ProjectRatingForm
    template_name = 'projects/project_rating_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=self.kwargs['pk'])

        if self.project.members.filter(user=request.user).exists() or self.project.owner == request.user:
            raise PermissionDenied("You cannot rate your own project.")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.project = self.project
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.project.pk})


class ProjectRolesUpdateView(UpdateView):
    model = Project
    template_name = 'projects/project_roles_form.html'
    form_class = ProjectMembershipFormSet

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("You must be logged in to create tasks.")

        self.object = self.get_object()
        if self.object.owner != request.user:
            raise PermissionDenied("Only the project owner can edit roles.")
        return super().dispatch(request, *args, **kwargs)

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
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.object.pk})


class DeveloperDetailView(DetailView):
    model = Developer
    template_name = 'projects/profile.html'
    context_object_name = 'developer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        developer = self.object

        # Средняя оценка проектов
        project_ids = ProjectMembership.objects.filter(user=developer).values_list('project_id', flat=True)
        context['avg_project_score'] = Project.objects.filter(id__in=project_ids).aggregate(avg=Avg('score'))['avg'] or 0

        # Список проектов пользователя
        context['projects'] = Project.objects.filter(id__in=project_ids)
        return context


class TaskCreateView(CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'projects/task_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("You must be logged in to create tasks.")

        self.project = get_object_or_404(Project, pk=self.kwargs['project_pk'])

        membership = ProjectMembership.objects.filter(
            project=self.project, user=request.user
        ).first()

        if not membership or membership.role not in ['pm', 'mentor', 'lead']:
            raise PermissionDenied("You don’t have permission to create tasks in this project.")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        project = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        form.instance.project = project

        assignee = form.cleaned_data.get("assignee")
        if assignee:
            if not ProjectMembership.objects.filter(project=project, user=assignee).exists():
                raise PermissionDenied("Assignee must be a member of this project.")

        return super().form_valid(form)

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        project = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        form.fields['assignee'].queryset = get_user_model().objects.filter(
        projectmembership__project=project
    )
        return form

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.kwargs['project_pk']})


class TaskUpdateView(UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'projects/task_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("You must be logged in to update tasks.")

        self.project = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        self.task = self.get_object()

        self.membership = ProjectMembership.objects.filter(
            project=self.project, user=request.user
        ).first()

        if not (
            self.membership and self.membership.role in ['pm', 'mentor', 'lead']
        ) and request.user != self.task.assignee:
            raise PermissionDenied("You don’t have permission to update this task.")

        return super().dispatch(request, *args, **kwargs)

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)

        if self.request.user == self.task.assignee and (
            not self.membership or self.membership.role not in ['pm', 'mentor', 'lead']
        ):
            for field in form.fields:
                if field != "status":
                    form.fields[field].disabled = True

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
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.kwargs['project_pk']})


class LeaderboardView(ListView):
    model = Developer
    template_name = "projects/leaderboard.html"
    context_object_name = "developers"

    def get_queryset(self):
        return Developer.objects.annotate(
            avg_score=Avg("received_user_ratings__rating")
        ).order_by("-avg_score")[:10]

def index(request):
    return None