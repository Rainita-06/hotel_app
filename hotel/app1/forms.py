# from django import forms
# from .models import GymMember, GymVisitor


# class GymMemberForm(forms.ModelForm):
#     pin = forms.CharField(widget=forms.PasswordInput, required=True)
#     confirm_password = forms.CharField(widget=forms.PasswordInput, required=True)

#     class Meta:
#         model = GymMember
#         fields ='__all__'

#     def clean(self):
#         cleaned_data = super().clean()
#         pwd = cleaned_data.get("pin")
#         cpwd = cleaned_data.get("confirm_password")

#         if pwd and cpwd and pwd != cpwd:
#             raise forms.ValidationError("Pin and Confirm Password do not match!")
#         return cleaned_data



# class GymVisitorForm(forms.ModelForm):
#     class Meta:
#         model = GymVisitor
#         fields ='__all__'

from django import forms
from .models import Building, Floor

class FloorForm(forms.ModelForm):
    class Meta:
        model = Floor
        fields = ["building", "name", "description", "rooms", "occupancy", "is_active"]
