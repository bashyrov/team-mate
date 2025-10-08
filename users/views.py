from django.contrib.auth import get_user_model
from django.views.generic import ListView, DetailView
from django.db.models import Avg

from projects.models import ProjectMembership, Project
from users.forms import DeveloperSearchForm
from team_mate import settings

user_model = settings.AUTH_USER_MODEL


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        developer = self.object

        project_ids = ProjectMembership.objects.filter(user=developer).values_list('project_id', flat=True)
        context['avg_project_score'] = Project.objects.filter(id__in=project_ids).aggregate(avg=Avg('score'))['avg'] or 0

        context['projects'] = Project.objects.filter(id__in=project_ids).order_by('-score')[:5]

        return context