from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from .forms import *


########################################## signup page views
def signup_view(request):
    form = UserRegistrationForm()
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            messages.success(request, 'Please complete your profile details.')
            return redirect('profile')
        else:
            messages.error(request,  'Error: Please check your information and try again')

    context = {'form': form}
    return render(request, 'a_auth/sign_up.html', context)



########################################## login page views
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        try:
            user = User.objects.get(username=username)
            # Authenticate the user only if they exist
            authenticated_user = authenticate(username=username, password=password)
            if authenticated_user is not None:
                login(request, authenticated_user)
                messages.success(request, 'User login successful ✅')
                return redirect('dashboard')
            else:
                # Incorrect password
                messages.error(request, 'Incorrect password ❌')
        except User.DoesNotExist:
            # User does not exist
            messages.error(request, 'User not found ❌')

    return render(request, 'a_auth/login.html', {})



################################ logout views
def logout_view(request):
    logout(request)
    return redirect('login')


