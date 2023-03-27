from django import forms
from django.core.validators import MinValueValidator
from .models import UserModel

class UserForm(forms.Form):
    user_id = forms.IntegerField(label='User ID', validators=[MinValueValidator(1)])
