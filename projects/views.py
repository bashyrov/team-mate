from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, FormView
from .models import Project, Task, Developer, ProjectMembership
from .forms import ProjectForm, TaskForm, ProjectMembershipFormSet, ProjectMembershipFormUpdate, ProjectMembershipForm, \
    ProjectStageForm
from django.shortcuts import redirect, get_object_or_404, render


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
            'projectmembership_set__user'
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

        context.update({
            'memberships': memberships,
            'tasks_by_assignee': tasks_by_assignee,
            'current_membership': current_membership
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

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.object.pk})


class ProjectRolesUpdateView(UpdateView):
    model = Project
    template_name = 'projects/project_roles_form.html'
    form_class = ProjectMembershipFormSet

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            formset = ProjectMembershipFormSet(
                self.request.POST,
                instance=self.object,
                form_kwargs={'project': self.object}
            )
            print("POST data:", dict(self.request.POST))
            print("Formset bound:", formset.is_bound)
        else:
            formset = ProjectMembershipFormSet(
                instance=self.object,
                form_kwargs={'project': self.object}
            )
            print("GET request: Formset forms count:", len(formset.forms))
            for idx, form in enumerate(formset):
                user = form.instance.user.username if form.instance.pk else "New"
                print(f"Form {idx}: instance={form.instance}, user={user}")
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
            print("Formset is valid! Saving...")
            formset.save()
            return redirect(self.get_success_url())
        else:
            print("Formset is INVALID!")
            print("Non-form errors:", formset.non_form_errors())
            for idx, form in enumerate(formset):
                user = form.instance.user.username if form.instance.pk else "New"
                print(f"Form {idx} errors: {form.errors}, user={user}")
            print("Deleted forms:", [form.instance for form in formset.deleted_forms])
        return self.render_to_response(self.get_context_data(formset=formset))

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.object.pk})


class DeveloperDetailView(DetailView):
    model = Developer
    template_name = 'projects/profile.html'
    context_object_name = 'developer'


class TaskCreateView(CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'projects/task_form.html'

    def form_valid(self, form):
        project_id = self.kwargs['project_pk']
        form.instance.project_id = project_id
        return super().form_valid(form)


class TaskUpdateView(UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'projects/task_form.html'


def index(request):
    return None