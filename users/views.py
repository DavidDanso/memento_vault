from django.shortcuts import render

# Create your views here.
def profile_view(request):
    context = {}
    return render(request, 'users/profile.html', context)