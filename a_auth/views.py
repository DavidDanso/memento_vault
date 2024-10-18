from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout


########################################## login page views
def login_view(request):
    # 
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request,  'User not found❌')

        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)

            # user login success message
            messages.success(request,  'User login Successful')
            return redirect('dashboard')
        else:
            messages.error(request,  'Username or Password is incorrect❌')

    context = {}
    return render(request, 'a_auth/login.html', context)


########################################## signup page views
def signup_view(request):
    context = {}
    return render(request, 'a_auth/sign_up.html', context)



################################ logout views
def logout_view(request):
    logout(request)
    return redirect('login')


