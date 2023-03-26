from django import forms
from .models import UserModel

class UserForm(forms.Form):
    user_id = forms.IntegerField(label='User ID', default=1)

