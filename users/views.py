from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ProfileForm
from vaults.models import Vault

@login_required
def profile_view(request):
    profile = request.user.profile
    vault_count = Vault.objects.filter(owner=profile).count()
    remaining_vaults = 5 - vault_count

    if request.method == 'POST':
        if 'delete_account' in request.POST:
            profile.delete()
            messages.success(request, 'Account deleted successfully')
            return redirect('sign-up')
            
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            if request.htmx:
                return render(request, 'partials/profile-info.html', {
                    'profile': profile,
                    'form': form,
                    'remaining_vaults': remaining_vaults
                })
            messages.success(request, 'Profile updated successfully')
            return redirect('profile')
        else:
            if request.htmx:
                return render(request, 'partials/profile-info.html', {
                    'profile': profile,
                    'form': form,
                    'remaining_vaults': remaining_vaults
                }, status=400)
    else:
        form = ProfileForm(instance=profile)

    context = {
        'profile': profile,
        'form': form,
        'remaining_vaults': remaining_vaults
    }
    return render(request, 'users/profile.html', context)