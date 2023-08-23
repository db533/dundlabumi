from django import forms
from django.core.validators import MinValueValidator
from .models import UserModel, Redirect

class UserForm(forms.Form):
    user_id = forms.IntegerField(label='User ID', validators=[MinValueValidator(1)])

class RedirectCodeForm(forms.Form):
    redirect_code = forms.IntegerField(label='Redirect Code')
