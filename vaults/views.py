from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from functools import reduce
from operator import or_
from users.models import Profile
from .forms import *
from django.db.models import Exists, OuterRef
from django.http import HttpResponse

@login_required(login_url='login')
def dashboard_view(request):
    # Ensure Profile exists for the logged-in user
    profile = get_object_or_404(Profile, user=request.user)

    # Retrieve all vaults associated with the logged-in user's profile
    vaults = profile.vaults.all()
    
    # Filter vaults with recent uploads (vaults with media files)
    recent_media = vaults.annotate(
        has_media=Exists(VaultMedia.objects.filter(vault=OuterRef('pk')))
    ).filter(has_media=True)[:3]

    # Vault count and first vault title
    vault_count = vaults.count()
    new_vault = vaults[0].title if vault_count > 0 else "📂 No Vaults Available - Create your first vault"

    # Retrieve all media files for user's vaults
    media_files = VaultMedia.objects.filter(vault__in=vaults)

    #
    vaults_to_created = 5 - vault_count


    # File extension groups
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', 'avif']
    video_extensions = ['.mp4', '.webm', '.ogg', '.mov', '.avi', '.mkv']

    # Count images and videos with OR logic for extensions
    image_count = media_files.filter(
        reduce(or_, (Q(file__endswith=ext) for ext in image_extensions))
    ).count()

    video_count = media_files.filter(
        reduce(or_, (Q(file__endswith=ext) for ext in video_extensions))
    ).count()

    form = VaultCreationForm()
    if request.method == 'POST':
        form = VaultCreationForm(request.POST)
        if form.is_valid():
            vault = form.save(commit=False)
            vault.owner = profile
            vault.save()
            # Redirect to the newly created vault's detail view
            return redirect('vault-details', pk=vault.pk, title=vault.title)

    # Context dictionary
    context = {
        'vault_count': vault_count, 'new_vault': new_vault, 
        'image_count': image_count, 'video_count': video_count,
        'form': form,
        'new_vault_id': vaults[0].id if vault_count > 0 else None,
        'recent_media': recent_media,
        'vaults_to_created': vaults_to_created,
    }
    return render(request, 'dashboard.html', context)



# Retrieves the user's profile for potential customization or data display.✅
@login_required(login_url='login')
def vault_view(request):
    # Ensure Profile exists for the logged-in user
    profile = get_object_or_404(Profile, user=request.user)

    # Retrieve all vaults associated with the logged-in user's profile
    vaults = profile.vaults.all().order_by('-updated_at')

    # Get the current date
    current_date = timezone.now()

    #
    vault_count = vaults.count()

    # basic plan
    vaults_to_created = 5 - vault_count

    # Prepare a dictionary to hold vaults and their media count
    vaults_with_media_count = []
    for vault in vaults:
        media_count = vault.media_files.count()  # Count media files for each vault
        allowed_uploads = vault.max_media_items
        vaults_with_media_count.append({'vault': vault, 'media_count': media_count, 
                                        'allowed_uploads': allowed_uploads})

    form = VaultCreationForm()
    if request.method == 'POST':
        form = VaultCreationForm(request.POST)
        if form.is_valid():
            vault = form.save(commit=False)
            vault.owner = profile
            vault.save()
            return redirect('vault-details', pk=vault.pk, title=vault.title)

    context = {
        'form': form, 
        'vaults_with_media_count': vaults_with_media_count, 
        'now': current_date, 
        'vaults_to_created': vaults_to_created, 
        'vault_count': vault_count
    }
    return render(request, 'vaults/vaults.html', context)



# Vault details view renders a page that likely displays specific details of a selected vault.
@login_required(login_url='login')
def vault_details_view(request, pk, title):
    # Get the vault object using the primary key
    vault = get_object_or_404(Vault, pk=pk)

    # Count media files for the retrieved vault
    media_count = vault.media_files.count()

    # Retrieve all media files associated with the vault
    media_files = vault.media_files.all().order_by('-updated_at')  # This gets all the uploaded media content

    remaining_uploads = vault.max_media_items - media_count
    
    # Categorize media files by type
    categorized_media = []
    for media in media_files:
        file_url = media.file.url.lower()  # Convert URL to lowercase for consistent checking
        if file_url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', 'avif')):
            categorized_media.append({'media': media, 'type': 'image'})
        elif file_url.endswith(('.mp4', '.webm', '.ogg', '.mov', '.avi', '.mkv')):
            categorized_media.append({'media': media, 'type': 'video'})
        else:
            categorized_media.append({'media': media, 'type': 'unsupported'})

    media_form = VaultMediaForm()
    if request.method == 'POST':
        media_form = VaultMediaForm(request.POST, request.FILES)
        if media_form.is_valid(): 
            files = request.FILES.getlist('file')  # Get all uploaded files

            # Check if the upload exceeds the max_media_items limit
            if media_count + len(files) > vault.max_media_items:
                messages.error(request, f"Only {remaining_uploads} upload(s) left. Please cut back on your uploads.")
            else:
                # Save each file to the database
                for f in files:
                    media_vault = VaultMedia(file=f, vault=vault)
                    media_vault.save()
                messages.success(request, f"{len(files)} file(s) successfully uploaded to this vault! 🎉")
                return redirect('vault-details', pk=pk, title=title)
        
        elif 'delete_media' in request.POST:
            # Get the media_id from POST data and delete the specific media file
            media_id = request.POST.get('media_id')
            # Ensure media belongs to this vault and delete
            media_to_delete = get_object_or_404(VaultMedia, id=media_id)
            media_to_delete.delete()
            messages.success(request, 'The selected file has been permanently deleted. 🗑️')
            return redirect('vault-details', pk=pk, title=title)

    context = {'media_count': media_count, 'vault': vault, 
        'media_files': categorized_media, 'media_form': media_form, 
        'remaining_uploads': remaining_uploads}
    return render(request, 'vaults/vault_details.html', context)



# Everything view renders a page that might showcase all vault-related items or records.
def everything_view(request):
    # Ensure Profile exists for the logged-in user
    profile = get_object_or_404(Profile, user=request.user)

    # Retrieve all vaults associated with the logged-in user's profile
    vaults = profile.vaults.all()

    # Collect and sort media files from all vaults associated with the user
    media_files = VaultMedia.objects.filter(vault__in=vaults).order_by('-updated_at')

    # Categorize media files by type
    categorized_media = []
    for media in media_files:
        file_url = media.file.url.lower()
        if file_url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', 'avif')):
            categorized_media.append({'media': media, 'type': 'image'})
        elif file_url.endswith(('.mp4', '.webm', '.ogg', '.mov', '.avi', '.mkv')):
            categorized_media.append({'media': media, 'type': 'video'})
        else:
            categorized_media.append({'media': media, 'type': 'unsupported'})


    form = VaultCreationForm()
    if request.method == 'POST':
        form = VaultCreationForm(request.POST)
        if form.is_valid():
            vault = form.save(commit=False)
            vault.owner = profile
            vault.save()
            # Redirect to the newly created vault's detail view
            return redirect('vault-details', pk=vault.pk, title=vault.title)
        
        if 'delete_media' in request.POST:
            # Get the media_id from POST data and delete the specific media file
            media_id = request.POST.get('media_id')
            # Ensure media belongs to this vault and delete
            media_to_delete = get_object_or_404(VaultMedia, id=media_id)
            media_to_delete.delete()
            messages.success(request, 'The selected file has been permanently deleted. 🗑️')
            return redirect('everything')

    # Pass categorized media to the context for easy handling in the template
    context = {
        'media_files': categorized_media,
        'profile': profile,
        'form': form,
    }
    return render(request, 'vaults/everything.html', context)



# Gallery view loads a gallery page to display media or files related to vaults.
def gallery_view(request):
    # Ensure Profile exists for the logged-in user
    profile = get_object_or_404(Profile, user=request.user)

    # Retrieve all vaults associated with the logged-in user's profile
    vaults = profile.vaults.all()

    # Collect and sort media files from all vaults associated with the user
    media_files = VaultMedia.objects.filter(vault__in=vaults).order_by('-updated_at')

    # Categorize media files by type
    categorized_media = []
    for media in media_files:
        file_url = media.file.url.lower()
        if file_url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', 'avif')):
            categorized_media.append({'media': media, 'type': 'image'})
        elif file_url.endswith(('.mp4', '.webm', '.ogg', '.mov', '.avi', '.mkv')):
            categorized_media.append({'media': media, 'type': 'video'})
        else:
            categorized_media.append({'media': media, 'type': 'unsupported'})

    # File extension groups
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', 'avif']
    video_extensions = ['.mp4', '.webm', '.ogg', '.mov', '.avi', '.mkv']

    # Count images and videos with OR logic for extensions
    image_count = media_files.filter(
        reduce(or_, (Q(file__endswith=ext) for ext in image_extensions))
    ).count()

    video_count = media_files.filter(
    reduce(or_, (Q(file__endswith=ext) for ext in video_extensions))
    ).count()

    context = {'image_count': image_count, 
               'video_count': video_count, 'media_files': categorized_media}
    return render(request, 'vaults/gallery.html', context)


# Thank you view renders a post-action thank you page, possibly shown after a successful action.
def thankY_view(request):
    context = {}
    return render(request, 'thankY_page.html', context)


# Uploads view displays a dedicated page for uploading files or media into a vault.
@login_required(login_url='login')
def uploads_view(request, vault_id):
    # Get the vault object using the primary key
    vault = get_object_or_404(Vault, pk=vault_id)

    # Calculate the total media upload limit for the vault

    # Count the currently uploaded media files
    media_count = vault.media_files.count()

    # Determine the remaining uploads for the user
    uploads_remaining = vault.max_media_items - media_count

    media_form = VaultMediaForm()
    if request.method == 'POST':
        media_form = VaultMediaForm(request.POST, request.FILES)
        if media_form.is_valid():
            files = request.FILES.getlist('file')  # Get all uploaded files

            # Check if the user is exceeding their allowed uploads
            if media_count + len(files) > vault.max_media_items:
                messages.error(request, f"Only {uploads_remaining} upload(s) left. Please cut back on your uploads.")
            else:
                # Save each uploaded file to the database
                for f in files:
                    VaultMedia.objects.create(file=f, vault=vault)
                messages.success(request, f"{len(files)} file(s) successfully uploaded to this vault! 🎉")
                # Recalculate uploads remaining after successful upload
                uploads_remaining -= len(files)

    # Pass the remaining uploads count and other data to the context
    context = {
        'vault': vault,
        'uploads_remaining': uploads_remaining,
        'media_form': media_form,
        'media_count': media_count,
    }
    return render(request, 'vaults/uploads_page.html', context)



#
def download_qr_code(request, vault_id):
    # Fetch the vault
    vault = get_object_or_404(Vault, id=vault_id)

    if vault.qr_code:
        # Serve the QR code as a downloadable file
        response = HttpResponse(vault.qr_code, content_type='image/png')
        response['Content-Disposition'] = f'attachment; filename="{vault.title}_qr_code.png"'
        return response
    else:
        return HttpResponse("QR code not found.", status=404)