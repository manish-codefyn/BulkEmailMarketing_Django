from django import forms
from .models import Subscriber, SubscriberList

class SubscriberImportForm(forms.Form):
    excel_file = forms.FileField(label='Select Excel file')


class SubscriberForm(forms.ModelForm):
    class Meta:
        model = Subscriber
        fields = ['email', 'first_name', 'last_name', 'is_active', 'lists']


class SubscriberListForm(forms.ModelForm):
    class Meta:
        model = SubscriberList
        fields = ['name', 'description', 'is_active']