from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Profile
from .forms import ProfileForm

@login_required
def profile_view(request):
    profile = request.user.profile

    form = ProfileForm(instance=profile)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            if request.htmx:  # Check if the request is an HTMX request
                return render(request, 'partials/profile-info.html', {'profile': profile})
            return redirect('profile')

    context = {'profile': profile, 'form': form}
    return render(request, 'users/profile.html', context)
