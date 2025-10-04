from django import forms
from django.contrib.auth import get_user_model
from django.forms import inlineformset_factory
from .models import Project, ProjectMembership, Task, ProjectRating, ProjectApplication


user_model = get_user_model()


class ProjectSearchForm(forms.Form):
    project_name = forms.CharField(max_length=255,
                                   required=False,
                                   label='',
                                   widget=forms.TextInput(attrs=
                                                          {
                                      'class': 'form-control',
                                      'placeholder': 'Project Name',
                                  }))
    development_stage = forms.ChoiceField(
        choices=[('', 'Select stage')] + list(Project.DEVELOPMENT_STAGE_CHOICES),
        required=False,
        label='',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'style': 'margin-top: 15px;'
        })
    )

    domain = forms.ChoiceField(
        choices=[('', 'Select domain')] + list(Project.DOMEN_CHOICES),
        required=False,
        label='',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'style': 'margin-top: 15px;'
        })
    )

    open_to_candidates = forms.BooleanField(
        required=False,
        label='Open to candidates',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-control',
            'style': 'margin-top: 15px; height:30px; width:30px;',
        })
    )


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'domain', 'deploy_url', 'project_url']


class ProjectStageForm(forms.ModelForm):
    development_stage = forms.ChoiceField(
        choices=Project.DEVELOPMENT_STAGE_CHOICES,
        label="Development Stage"
    )

    class Meta:
        model = Project
        fields = ['development_stage', 'deploy_url']

    def clean(self):
        cleaned_data = super().clean()
        stage = cleaned_data.get('development_stage')
        deploy_url = cleaned_data.get('deploy_url')

        if stage == 'deployed' and not deploy_url:
            self.add_error(
                'development_stage',
                'Cannot set stage to "Deployed" without a deploy URL.'
            )

        return cleaned_data


class ProjectMembershipFormUpdate(forms.ModelForm):
    class Meta:
        model = Project
        fields = '__all__'


class ProjectRatingForm(forms.ModelForm):
    class Meta:
        model = ProjectRating
        fields = ['score', 'comment']
        widgets = {
            'score': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'comment': forms.Textarea(attrs={'rows': 3}),
        }


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'assignee', 'tags']


class ProjectApplicationForm(forms.ModelForm):
    class Meta:
        model = ProjectApplication
        fields = ["role", "message"]


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

