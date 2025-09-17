from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from .models import Project, Task, Developer
from .forms import ProjectForm, TaskForm


# Список всех проектов
class ProjectListView(ListView):
    model = Project
    template_name = 'projects/project-list.html'
    context_object_name = 'projects'


# Мои проекты (пользовательские)
class MyProjectListView(ListView):
    model = Project
    template_name = 'projects/my_projects.html'
    context_object_name = 'projects'

    def get_queryset(self):
        return self.request.user.projects.all()


# Детальный вид проекта с задачами
class ProjectDetailView(DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'


# Создание проекта
class ProjectCreateView(CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


# Редактирован
# ие проекта
class ProjectUpdateView(UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'


# Детальный вид разработчика (профиль)
class DeveloperDetailView(DetailView):
    model = Developer
    template_name = 'projects/profile.html'
    context_object_name = 'developer'


# Создание задачи
class TaskCreateView(CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'projects/task_form.html'

    def form_valid(self, form):
        project_id = self.kwargs['project_pk']
        form.instance.project_id = project_id
        return super().form_valid(form)


# Редактирование задачи
class TaskUpdateView(UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'projects/task_form.html'


def index(request):
    return None