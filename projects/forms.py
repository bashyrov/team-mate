from django import forms
from django.contrib.auth import get_user_model
from django.forms import inlineformset_factory
from .models import Project, ProjectMembership, Task


user_model = get_user_model()


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description']


class ProjectMembershipFormUpdate(forms.ModelForm):
    class Meta:
        model = Project
        fields = '__all__'


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'assignee', 'tags']


class ProjectMembershipForm(forms.ModelForm):
    class Meta:
        model = ProjectMembership
        fields = ["user", "role"]
        widgets = {
            "role": forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        self.fields["user"].disabled = True
        self.fields["user"].required = False
        if self.project:
            self.fields["user"].queryset = Project.objects.get(id=self.project.id).members.all()

    def clean(self):
        cleaned_data = super().clean()
        if self.instance.pk and self.instance.user:
            cleaned_data["user"] = self.instance.user
        return cleaned_data


ProjectMembershipFormSet = inlineformset_factory(
    Project,
    ProjectMembership,
    form=ProjectMembershipForm,
    extra=0,
    can_delete=True
)

