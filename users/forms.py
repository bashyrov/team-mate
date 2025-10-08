from django import forms
from django.contrib.auth import get_user_model

from projects.models import Task


class DeveloperSearchForm(forms.Form):
    username = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'id': 'voice-search',
            'placeholder': 'Search Mockups, Logos, Design Templates...',
            'class': (
                'bg-gray-50 border border-gray-300 text-gray-900 text-sm '
                'rounded-l-full focus:ring-blue-500 focus:border-blue-500 '
                'block w-full ps-10 p-2.5 dark:bg-gray-700 dark:border-gray-600 '
                'dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 '
                'dark:focus:border-blue-500'
            )
        })
    )
class DeveloperForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = [
            'position',
            'tech_stack',
            'linkedin_url',
            'portfolio_url',
            'telegram_contact',
            'discord_contact',
        ]
        widgets = {
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'tech_stack': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control'}),
            'portfolio_url': forms.URLInput(attrs={'class': 'form-control'}),
            'telegram_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'discord_contact': forms.TextInput(attrs={'class': 'form-control'}),
        }

class MyTaskSearchForm(forms.Form):
    title = forms.CharField(
        max_length=255,
        required=False,
        label='',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Task Name',
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

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user