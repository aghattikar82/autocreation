from django import forms
from .models import Company, EmailFormat

from django import forms

class UploadNotepadForm(forms.Form):
    file = forms.FileField()


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'domainname','country']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'domainname': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
        }

class EmailFormatForm(forms.ModelForm):
    class Meta:
        model = EmailFormat
        fields = ['company', 'format_string']
        widgets = {
            'company': forms.Select(attrs={'class': 'form-control'}),
            'format_string': forms.TextInput(attrs={'class': 'form-control'}),
        }

class UploadFileForm(forms.Form):
    file = forms.FileField()
