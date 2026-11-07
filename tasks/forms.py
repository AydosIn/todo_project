from django import forms
from .models import Task


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'priority', 'due_date', 'completed']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'What needs to be done?', 'autofocus': True}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Optional details'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }
        labels = {
            'completed': 'Mark as done',
        }
