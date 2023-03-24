from django import forms

class UserForm(forms.Form):
    user_id = forms.IntegerField(label='User ID')

