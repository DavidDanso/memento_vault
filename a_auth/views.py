from django.shortcuts import render


# 
def login_view(request):
    context = {}
    return render(request, 'a_auth/login.html', context)


# 
def signup_view(request):
    context = {}
    return render(request, 'a_auth/sign_up.html', context)


