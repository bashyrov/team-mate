from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, UpdateView
from django.db.models import Avg
from django.views.generic import FormView

from projects.models import ProjectMembership, Project, Task
from users.forms import DeveloperSearchForm, DeveloperForm, MyTaskSearchForm, DeveloperCreationForm
from team_mate.settings import base

user_model = base.AUTH_USER_MODEL


class RegisterView(FormView):
    template_name = 'registration/register.html'
    form_class = DeveloperCreationForm

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('users:profile', kwargs={'user_pk': self.request.user.pk})


class LeaderboardView(ListView):
    model = user_model
    template_name = "users/leaderboard.html"
    context_object_name = "developers"
    paginate_by = 10

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(LeaderboardView, self).get_context_data(**kwargs)
        username = self.request.GET.get('project_name', '')
        context['search_form'] = DeveloperSearchForm(
            initial={'username': username}
        )
        page_obj = context.get('page_obj')

        if page_obj:
            context['start_rank'] = (page_obj.number - 1) * self.paginate_by
        else:
            context['start_rank'] = 0

        return context

    def get_queryset(self):
        qs = get_user_model().objects.all()
        form = DeveloperSearchForm(self.request.GET)

        if form.is_valid():
            username = self.request.GET.get('username', '')

            if username:
                qs = qs.filter(username__icontains=username)

        qs = qs.annotate(avg_score=Avg('projects__score')).order_by('-avg_score', 'username')

        return qs


class DeveloperDetailView(DetailView):
    model = get_user_model()
    template_name = 'users/profile.html'
    context_object_name = 'developer'
    pk_url_kwarg = 'user_pk'

    def get_queryset(self):
        return get_user_model().objects.filter(pk=self.kwargs['user_pk']).prefetch_related("projects")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        developer = self.object
        is_developer = developer == self.request.user

        project_ids = ProjectMembership.objects.filter(user=developer).values_list('project_id', flat=True)

        context['is_developer'] = is_developer
        context['avg_project_score'] = Project.objects.filter(id__in=project_ids).aggregate(avg=Avg('score'))['avg'] or 0

        context['projects'] = Project.objects.filter(id__in=project_ids).order_by('-score')[:5]

        return context

@method_decorator(login_required, name='dispatch')
class DeveloperUpdateView(UpdateView):
    model = get_user_model()
    form_class = DeveloperForm
    template_name = 'users/profile_update.html'
    context_object_name = 'developer'
    pk_url_kwarg = 'user_pk'

    def dispatch(self, request, *args, **kwargs):
        if request.user and request.user.pk != self.get_object().pk:
            return redirect('users:profile', user_pk=request.user.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        developer = self.object

        project_ids = ProjectMembership.objects.filter(user=developer).values_list('project_id', flat=True)
        context['avg_project_score'] = Project.objects.filter(id__in=project_ids).aggregate(avg=Avg('score'))['avg'] or 0

        context['projects'] = Project.objects.filter(id__in=project_ids).order_by('-score')[:5]

        return context

    def get_success_url(self):
        return reverse_lazy('users:profile', kwargs={'user_pk': self.object.pk})


@method_decorator(login_required, name='dispatch')
class MyProjectListView(ListView):
    model = Project
    template_name = 'users/my_projects.html'
    context_object_name = 'projects'
    paginate_by = 10

    def get_queryset(self):
        qs = (self.request.user.projects.all() | self.request.user.owned_projects.all()).distinct()
        return qs


@method_decorator(login_required, name='dispatch')
class MyTasksListView(ListView):
    model = Task
    template_name = 'users/my_task_list.html'
    context_object_name = 'tasks'
    paginate_by = 10
    view_type = 'my_tasks'

    def get_queryset(self):
        user = self.request.user
        qs = Task.objects.filter(assignee=user).select_related('assignee', 'created_by',
                                                               'project__owner').prefetch_related(
            'tags')

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