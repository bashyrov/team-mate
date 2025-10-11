from django import forms
from django.contrib.auth import get_user_model
from django.forms import inlineformset_factory
from .models import Project, ProjectMembership, Task, ProjectRating, ProjectApplication, ProjectOpenRole

user_model = get_user_model()


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'assignee', 'tags']

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)

        field_attrs = {'class': 'form-control form-control-sm mb-2'}

        self.fields['title'].widget.attrs.update({
            **field_attrs,
            'placeholder': 'Task Title',
        })

        self.fields['description'].widget.attrs.update({
            **field_attrs,
            'placeholder': 'Task Description',
            'rows': 2,
        })

        self.fields['status'].widget.attrs.update({
            **field_attrs,
        })

        if project:
            self.fields['assignee'].queryset = project.members.values_list('user', flat=True)
        else:
            self.fields['assignee'].queryset = Task._meta.get_field('assignee').related_model.objects.none()
        self.fields['assignee'].widget.attrs.update({
            **field_attrs,
        })
        self.fields['assignee'].empty_label = 'Select user'

        self.fields['tags'].widget.attrs.update({
            **field_attrs,
        })




class TaskSearchForm(forms.Form):
    title = forms.CharField(
        max_length=255,
        required=False,
        label='',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Project Name',
        })
    )
    assignee = forms.ModelChoiceField(
        queryset=user_model.objects.none(),
        required=False,
        label='',
        empty_label='Select user',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'style': 'margin-top: 15px;'
        })
    )
    status = forms.ChoiceField(
        choices=[('', 'Select status')] + list(Task.STATUS_CHOICES),
        required=False,
        label='',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'style': 'margin-top: 15px;'
        })
    )

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)

        if project:
            self.fields['assignee'].queryset = project.members.all()


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
            'class': 'form-check-input',
            'style': 'margin-top: 5px;',
        })
    )


class ProjectApplicationSearchForm(forms.Form):
    username = forms.CharField(max_length=255,
                                   required=False,
                                   label='',
                                   widget=forms.TextInput(attrs=
                                                          {
                                      'class': 'form-control',
                                      'placeholder': 'Username',
                                  }))
    role = forms.ChoiceField(
        choices=[('', 'Select role')] + list(ProjectMembership.ROLE_CHOICES),
        required=False,
        label='',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'style': 'margin-top: 15px;'
        })
    )


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'domain', 'development_stage', 'deploy_url', 'project_url']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Project Name',
        })

        self.fields['description'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Project Description',
            'rows': 3,
            'style': 'margin-top: 10px;',
        })

        self.fields['domain'].widget.attrs.update({
            'class': 'form-select',
            'style': 'margin-top: 10px;',
        })

        self.fields['development_stage'].widget.attrs.update({
            'class': 'form-select',
            'style': 'margin-top: 10px;',
        })

        self.fields['deploy_url'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Deploy URL',
            'style': 'margin-top: 10px;',
        })
        self.fields['project_url'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Project URL (Github, etc.)',
            'style': 'margin-top: 10px;',
        })


class ProjectStageForm(forms.ModelForm):
    development_stage = forms.ChoiceField(
        choices=Project.DEVELOPMENT_STAGE_CHOICES,
        label="Development Stage",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'style': 'margin-top: 15px;'
        })
    )

    deploy_url = forms.URLField(
        required=False,
        label="Deploy URL",
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'Deploy URL',
            'style': 'margin-top: 10px;',
        }))

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


class ProjectOpenRoleSearchForm(forms.Form):

    role_name = forms.ChoiceField(
        choices=[('', 'Select role')] + list(ProjectMembership.ROLE_CHOICES),
        required=False,
        label='',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'style': 'margin-top: 15px;'
        })
    )


class ProjectOpenRoleForm(forms.ModelForm):
    role_name = forms.ChoiceField(
        choices=[('', 'Select role')] + list(ProjectMembership.ROLE_CHOICES),
        required=True,
        label='',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'style': 'margin-top: 15px;'
        })
    )

    class Meta:
        model = ProjectOpenRole
        fields = ["role_name", "message"]


class ProjectApplicationForm(forms.ModelForm):


    class Meta:
        model = ProjectApplication
        fields = ["message"]
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Write your message to the project owner...',
                'style': 'width: 50%;'
            }),
        }
        labels = {
            'message': '',
        }


class ProjectMembershipForm(forms.ModelForm):
    class Meta:
        model = ProjectMembership
        fields = ["user", "role", "edit_project_info_perm", "add_task_perm", "update_project_stage_perm", "manage_open_roles_perm"]
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

