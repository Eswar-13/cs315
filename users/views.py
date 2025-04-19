from django.contrib.auth import authenticate, login ,logout
from django.shortcuts import render, redirect
from .forms import SignUpForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

User = get_user_model()  # Uncomment this

def user_login(request):
    if request.method == 'POST':
        # Use 'username' key for email if using email as username
        email = request.POST.get('username')  # Changed from 'email' to 'username'
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)  # Key fix
        
        if user is not None:
            login(request, user)
            return redirect('home')  # Ensure 'home' URL exists
        else:
            return render(request, 'registration/login.html', {'error': 'Invalid credentials'})
    return render(request, 'registration/login.html')

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Auto-login after signup
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def home(request):
    return render(request, 'home.html')


def user_logout(request):
    logout(request)
    return redirect('login')