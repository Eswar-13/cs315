
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()  # Gets your CustomUser

class SignUpForm(UserCreationForm):
    class Meta:
        model = User  # Use your CustomUser
        fields = ['email', 'password1', 'password2']  # Replace with your fields
