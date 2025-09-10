from django import forms
from .models import GymMember, GymVisitor


class GymMemberForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False)
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=False)

    class Meta:
        model = GymMember
        fields ='__all__'

    def clean(self):
        cleaned_data = super().clean()
        pwd = cleaned_data.get("password")
        cpwd = cleaned_data.get("confirm_password")
        if pwd and cpwd and pwd != cpwd:
            raise forms.ValidationError("Passwords do not match!")
        return cleaned_data


class GymVisitorForm(forms.ModelForm):
    class Meta:
        model = GymVisitor
        fields ='__all__'
