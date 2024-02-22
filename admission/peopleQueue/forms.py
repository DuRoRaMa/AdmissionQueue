from django import forms

class RegisterForm(forms.Form):
    name = forms.CharField(max_length=5)