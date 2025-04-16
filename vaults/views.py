from urllib import request
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Prefetch
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from functools import reduce
from operator import or_
from users.models import Profile
from .forms import *
from django.http import HttpResponse
from .utils import MediaProcessor
from django.db.models import F
from django.core.cache import cache
from django.utils import timezone 
from datetime import timedelta   


GEMINI_API_KEY = settings.GEMINI_API_KEY
media_processor = MediaProcessor(GEMINI_API_KEY)
VAULT_EXPIRATION_DURATION = timedelta(minutes=10)
VAULT_LIMIT = 10
USER_VAULT_CAP = 3


# Cache settings
CACHE_TTL = 60 * 15


# Home view renders the main page of the application.
def home_view(request):
    context = {}
    return render(request, 'index.html', context)


# Dashboard view renders the dashboard page for the logged-in user.
# It displays the user's vaults, media files, and allows for vault creation.
# The view is protected by login_required decorator to ensure only authenticated users can access it.
@login_required(login_url='login')
def dashboard_view(request):
    # Get current user profile
    profile = request.user.profile if hasattr(request.user, 'profile') else get_object_or_404(Profile, user=request.user)
    
    # Fetch all vaults with prefetched media in one query to avoid N+1 problem
    vaults = Vault.objects.filter(owner=profile).prefetch_related('media_files')
    
    
    # Get vault count
    vault_count = len(vaults)
    vaults_to_create = max(0, USER_VAULT_CAP - vault_count)

    
    # Get first vault title if available
    new_vault = vaults[0].title if vault_count > 0 else "📂 No Vaults Available - Create your first vault"
    new_vault_id = vaults[0].id if vault_count > 0 else None
    
    # Get vaults with recent media
    recent_media = [v for v in vaults if v.media_files.all()][:3]
    
    # File extensions for filtering
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', 'avif']
    video_extensions = ['.mp4', '.webm', '.ogg', '.mov', '.avi', '.mkv']
    
    # Collect all media files
    media_files = []
    for vault in vaults:
        media_files.extend(vault.media_files.all())
    
    # Count images and videos using list comprehension for better performance
    image_count = sum(1 for m in media_files if any(m.file.name.lower().endswith(ext) for ext in image_extensions))
    video_count = sum(1 for m in media_files if any(m.file.name.lower().endswith(ext) for ext in video_extensions))
    
    # Process form submission
    form = VaultCreationForm()
    if request.method == 'POST':
        form = VaultCreationForm(request.POST)
        if form.is_valid():
            vault = form.save(commit=False)
            vault.owner = profile
            vault.save()
            return redirect('vault-details', pk=vault.pk, title=vault.title)
    # Prepare context
    context = {
        'vault_count': vault_count,
        'new_vault': new_vault,
        'image_count': image_count,
        'video_count': video_count,
        'new_vault_id': new_vault_id,
        'recent_media': recent_media,
        'form': form,
        'vaults_to_create': vaults_to_create,
        'user_vault_cap': USER_VAULT_CAP,
    }
    return render(request, 'dashboard.html', context)


# Vault view renders the vaults page for the logged-in user.
# It displays the user's vaults, media files, and allows for vault creation.
# The view is protected by login_required decorator to ensure only authenticated users can access it.
@login_required(login_url='login')
def vault_view(request):
    profile = get_object_or_404(Profile, user=request.user)

    vaults_qs = Vault.objects.filter(
        owner=profile
    ).select_related('owner').annotate(
        media_count=Count('media_files')
    ).order_by('-updated_at') 

    vaults_data = []
    for vault in vaults_qs:
        uploads_left = VAULT_LIMIT - vault.media_count
        vaults_data.append({
            'vault': vault,
            'media_count': vault.media_count,
            'uploads_left': uploads_left,
            'vault_limit': VAULT_LIMIT,
        })

    vault_count = vaults_qs.count()
    vaults_to_create = max(0, USER_VAULT_CAP - vault_count)

    # Form handling
    form = VaultCreationForm()
    if request.method == 'POST':
        form = VaultCreationForm(request.POST)
        if form.is_valid():
            vault = form.save(commit=False)
            vault.owner = profile
            vault.save()
            # Redirect might use vault.title, ensure title is fetched (default)
            return redirect('vault-details', pk=vault.pk, title=vault.title)

    # Prepare context
    context = {
        'vaults_with_media_count': vaults_data, # List contains vault objects and counts
        'vault_count': vault_count,
        'vaults_to_create': vaults_to_create,
        'form': form,
        'now': timezone.now(),
        'user_vault_cap': USER_VAULT_CAP,
    }
    return render(request, 'vaults/vaults.html', context)


# Vault details view renders the details of a specific vault.
# It displays the media files associated with the vault and allows for file uploads.
# The view is protected by login_required decorator to ensure only authenticated users can access it.
@login_required(login_url='login')
def vault_details_view(request, pk, title):
    # Get vault with prefetched media to avoid N+1 problem
    vault = get_object_or_404(
        Vault.objects.prefetch_related(
            Prefetch('media_files', queryset=VaultMedia.objects.order_by('-updated_at'))
        ),
        pk=pk
    )
    
    # Get media files from the prefetched queryset
    media_files = vault.media_files.all()
    media_count = len(media_files)
    remaining_uploads = VAULT_LIMIT - media_count
    
    # Clear the file_count session value by default
    file_count = request.session.pop('file_count', 0)
    
    # Categorize media files by type
    categorized_media = []
    for media in media_files:
        file_url = media.file.url.lower()
        media_type = 'unsupported'
        if file_url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', 'avif')):
            media_type = 'image'
        elif file_url.endswith(('.mp4', '.webm', '.ogg', '.mov', '.avi', '.mkv')):
            media_type = 'video'
        categorized_media.append({'media': media, 'type': media_type})
    
    if request.method == 'POST':
        if 'delete_media' in request.POST:
            media_id = request.POST.get('media_id')
            media_to_delete = get_object_or_404(VaultMedia, id=media_id)
            media_to_delete.delete()
            messages.success(request, 'The selected file has been permanently deleted. 🗑️')
            # Clear caches related to this vault
            cache.delete_many([
                f"dashboard_data_{vault.owner_id}",
                f"user_vaults_{vault.owner_id}",
            ])
            return redirect('vault-details', pk=pk, title=title)
        
        media_form = VaultMediaForm(request.POST, request.FILES)
        if media_form.is_valid():
            files = request.FILES.getlist('file')
            current_file_count = len(files)
            
            if media_count + current_file_count > VAULT_LIMIT:
                messages.error(request, f"Only {remaining_uploads} upload(s) left. Please cut back on your uploads.")
            else:
                request.session['file_count'] = current_file_count
                
                # Process files in bulk to reduce DB hits
                media_objects = []
                for f in files:
                    media_vault = VaultMedia(file=f, vault=vault)
                    try:
                        caption, tags = media_processor.get_caption_and_tags(f)
                        if caption:
                            media_vault.caption = caption
                        media_vault.save()
                        if tags:
                            media_vault.tags.add(*tags)
                    except Exception as e:
                        messages.error(request, f"Processing error: {str(e)}")
                    media_objects.append(media_vault)
                
                # Clear the file count after successful upload
                request.session['file_count'] = 0
                messages.success(request, f"{current_file_count} file(s) successfully uploaded to this vault! 🎉")
                # Clear caches related to this vault
                cache.delete_many([
                    f"dashboard_data_{vault.owner_id}",
                    f"user_vaults_{vault.owner_id}",
                ])
                return redirect('vault-details', pk=pk, title=title)
    
    context = {
        'media_count': media_count,
        'vault': vault,
        'media_files': categorized_media,
        'remaining_uploads': remaining_uploads,
        'file_count': file_count,
        'VAULT_LIMIT': VAULT_LIMIT,
    }
    return render(request, 'vaults/vault_details.html', context)



# Everything view loads a page to display all media or files related to vaults.
# It allows users to create new vaults and delete media files.
@login_required(login_url='login')
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



# Gallery view loads a page to display all media or files related to vaults.
# The view is protected by login_required decorator to ensure only authenticated users can access it.
@login_required(login_url='login')
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



def thankY_view(request):
    context = {}
    return render(request, 'thankY_page.html', context)



# Download QR code view generates and serves a QR code for the vault.
# The view is protected by login_required decorator to ensure only authenticated users can access it.
@login_required(login_url='login')
def download_qr_code(request, vault_id):
    # Use select_related to avoid extra query
    vault = get_object_or_404(Vault, id=vault_id)
    
    # Check if QR code exists
    if not vault.qr_code:
        # Generate QR code if not available
        vault.generate_qr_code()
        vault.save(update_fields=['qr_code'])
    
    # Serve the QR code
    if vault.qr_code:
        response = HttpResponse(vault.qr_code, content_type='image/png')
        response['Content-Disposition'] = f'attachment; filename="{vault.title}_qr_code.png"'
        return response
    else:
        return HttpResponse("QR code not found.", status=404)
    



# Helper function to prepare context dictionary (Reduces repetition)
def _prepare_upload_context(vault, vault_limit, is_expired=False, uploads_remaining=0,
                           user_upload_count=0, uploads_allowed=0, media_form=None):
    total_vault_media_count = VaultMedia.objects.filter(vault=vault).count()

    if media_form is None and not is_expired and uploads_remaining > 0:
        media_form = VaultMediaForm()

    return {
        'vault': vault,
        'is_expired': is_expired,
        'vault_limit': vault_limit,
        'uploads_remaining': uploads_remaining,
        'user_upload_count': user_upload_count,
        'uploads_allowed': uploads_allowed,
        'media_form': media_form,
        'total_vault_media_count': total_vault_media_count,
    }


# Uploads view handles file uploads for a specific vault.
# It checks for expiration, user identification, and upload limits.
def uploads_view(request, vault_id):
    """Handles viewing the upload page and processing file uploads for a specific vault."""
    vault = get_object_or_404(Vault, pk=vault_id)
    now = timezone.now()

    # --- 1. Check Vault Expiration (Based on creation time) ---
    expiration_time = vault.created_at + VAULT_EXPIRATION_DURATION
    is_expired = now > expiration_time

    if is_expired:
        messages.error(request, f"The upload period for this vault expired {VAULT_EXPIRATION_DURATION.total_seconds() / 60:.0f} minutes after creation.")
        context = _prepare_upload_context(vault, VAULT_LIMIT, is_expired=True)
        return render(request, 'vaults/uploads_page.html', context)

    # --- 2. Identify Uploader ---
    uploader_profile = None
    session_key = None
    user_identifier_filter = {}

    if request.user.is_authenticated:
        try:
            uploader_profile = request.user.profile
            user_identifier_filter = {'uploader_profile': uploader_profile}
        except Profile.DoesNotExist:
            messages.error(request, "Could not identify your profile. Please complete sign-up or login again.")
            return redirect('sign-up')
    else:
        # Ensure anonymous users have a session key
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        user_identifier_filter = {'uploader_session_key': session_key}

    # --- 3. Calculate User's Upload Quota ---
    user_upload_count = VaultMedia.objects.filter(vault=vault, **user_identifier_filter).count()
    uploads_allowed = vault.uploads_per_person
    uploads_remaining = max(0, uploads_allowed - user_upload_count)

    # --- 4. Handle POST Request (File Upload Attempt) ---
    if request.method == 'POST':
        # Re-check expiration immediately before processing
        if timezone.now() > expiration_time:
             messages.error(request, "The upload period expired while you were submitting.")
             return redirect('uploads', vault_id=vault_id)

        # Check if user has already reached their limit
        if uploads_remaining <= 0:
            messages.error(request, "You have already reached your upload limit for this vault.")
            context = _prepare_upload_context(
                vault=vault, vault_limit=VAULT_LIMIT, is_expired=False,
                uploads_remaining=0, user_upload_count=user_upload_count,
                uploads_allowed=uploads_allowed
            )
            return render(request, 'vaults/uploads_page.html', context)

        # Process the form
        media_form = VaultMediaForm(request.POST, request.FILES)
        if media_form.is_valid():
            files = request.FILES.getlist('file')
            files_to_upload_count = len(files)

            # Check if this submission exceeds the remaining quota
            if files_to_upload_count > uploads_remaining:
                messages.error(request, f"You can only upload {uploads_remaining} more file(s). You tried to upload {files_to_upload_count}.")
                context = _prepare_upload_context(
                    vault=vault, vault_limit=VAULT_LIMIT, is_expired=False,
                    uploads_remaining=uploads_remaining, user_upload_count=user_upload_count,
                    uploads_allowed=uploads_allowed, media_form=media_form
                )
                return render(request, 'vaults/uploads_page.html', context)
            else:
                # Proceed with saving files
                saved_count = 0
                error_occurred = False
                for f in files:
                    media_instance = VaultMedia(
                        file=f,
                        vault=vault,
                        uploader_profile=uploader_profile,
                        uploader_session_key=session_key
                    )
                    try:
                        media_instance.save()
                        saved_count += 1
                    except Exception as e:
                        error_occurred = True
                        print(f"ERROR saving file to vault {vault_id}: {e}")

                # Provide feedback messages
                if error_occurred:
                     messages.warning(request, f"Successfully uploaded {saved_count} file(s), but an error occurred with at least one other file.")
                elif saved_count > 0:
                     messages.success(request, f"{saved_count} file(s) successfully uploaded! 🎉")

                return redirect('uploads', vault_id=vault_id)

    # --- 5. Handle GET Request or Invalid POST Form ---
    media_form = VaultMediaForm() if request.method == 'GET' else media_form

    # --- 6. Prepare Final Context and Render ---
    context = _prepare_upload_context(
        vault=vault, vault_limit=VAULT_LIMIT, is_expired=False,
        uploads_remaining=uploads_remaining, user_upload_count=user_upload_count,
        uploads_allowed=uploads_allowed, media_form=media_form
    )
    return render(request, 'vaults/uploads_page.html', context)