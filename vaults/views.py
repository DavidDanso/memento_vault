from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from users.models import Profile
from .forms import *

# Dashboard view requires user login and renders the main dashboard page.
@login_required(login_url='login')
def dashboard_view(request):
    # Context dictionary can hold user-specific data to pass to the template.
    context = {}
    return render(request, 'dashboard.html', context)


# Retrieves the user's profile for potential customization or data display.✅
@login_required(login_url='login')
def vault_view(request):
    # Ensure Profile exists for the logged-in user
    profile = get_object_or_404(Profile, user=request.user)

    # Retrieve all vaults associated with the logged-in user's profile
    vaults = profile.vaults.all()

    # Get the current date
    current_date = timezone.now()

    # Prepare a dictionary to hold vaults and their media count
    vaults_with_media_count = []
    for vault in vaults:
        media_count = vault.media_files.count()  # Count media files for each vault
        vaults_with_media_count.append({'vault': vault, 'media_count': media_count})

    form = VaultCreationForm()
    if request.method == 'POST':
        form = VaultCreationForm(request.POST)
        if form.is_valid():
            vault = form.save(commit=False)
            vault.owner = profile
            vault.save()
            messages.success(request, 'Vault created successfully.')
            return redirect('vaults')

    context = {'form': form, 'vaults_with_media_count': vaults_with_media_count, 'now': current_date,}
    return render(request, 'vaults/vaults.html', context)


# Vault details view renders a page that likely displays specific details of a selected vault.
# Could be extended to retrieve and pass specific vault data into the context.
def vault_details_view(request):
    context = {}
    return render(request, 'vaults/vault_details.html', context)


# Everything view renders a page that might showcase all vault-related items or records.
# Could be expanded to include context data from various vaults.
def everything_view(request):
    context = {}
    return render(request, 'vaults/everything.html', context)


# Gallery view loads a gallery page to display media or files related to vaults.
# Context can include images, videos, or other content.
def gallery_view(request):
    context = {}
    return render(request, 'vaults/gallery.html', context)


# Thank you view renders a post-action thank you page, possibly shown after a successful action.
# A context dictionary could contain success messages or action summaries.
def thankY_view(request):
    context = {}
    return render(request, 'thankY_page.html', context)


# Uploads view displays a dedicated page for uploading files or media into a vault.
# Context can be used to pass forms or upload configurations to the template.
def uploads_view(request):
    context = {}
    return render(request, 'vaults/uploads_page.html', context)