# Create your views here.
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import *

def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)
        if user is None:
            messages.error(request, "Invalid credentials")
            return redirect('login')
        auth_login(request, user)
        return redirect('core:landing')

    return render(request, 'accounts/login.html')

# Define a view function for the registration page
def register(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')

        # Basic validation
        if not username or not password or not first_name or not last_name:
            messages.error(request, "Please fill in all required fields.")
            return redirect('register')

        if password2 and password != password2:
            messages.error(request, "Passwords do not match.")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.info(request, "Username already taken!")
            return redirect('register')

        User.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            username=username,
            password=password
        )

        messages.success(request, "Account created successfully! Please log in.")
        return redirect('login_view')

    return render(request, 'accounts/register.html')