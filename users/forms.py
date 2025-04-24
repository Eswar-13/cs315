from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()  # Gets your CustomUser

class SignUpForm(UserCreationForm):
    name = forms.CharField(max_length=150, required=True, label='Full Name')

    class Meta:
        model = User  # Use your CustomUser
        fields = ['email', 'name' ,'password1', 'password2']  # Replace with your fields
