from django import forms
from .models import Campaign, EmailTemplate, Plugin, SubscriberList
from django_quill.forms import QuillFormField, QuillWidget

class CampaignForm(forms.ModelForm):
    list = forms.ModelChoiceField(queryset=SubscriberList.objects.all(), required=True)
    preview_text = QuillFormField()
    content = QuillFormField()

    class Meta:
        model = Campaign
        fields = ['name', 'subject', 'preview_text', 'content', 'is_active', 'list' ,'template']

class EmailTemplateForm(forms.ModelForm):
    content = QuillFormField()

    class Meta:
        model = EmailTemplate
        fields = ['name', 'subject', 'content', 'is_active']

class PluginForm(forms.ModelForm):

    class Meta:
        model = Plugin
        fields = ['name', 'description', 'code','description', 'is_active']
        widgets = {
            'code': forms.Textarea(attrs={'rows': 10}),
        }
