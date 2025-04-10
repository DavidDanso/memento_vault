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

GEMINI_API_KEY = settings.GEMINI_API_KEY
media_processor = MediaProcessor(GEMINI_API_KEY)

# Cache settings
CACHE_TTL = 60 * 15  # 15 minutes
VAULT_LIMIT = 10

def home_view(request):
    context = {}
    return render(request, 'index.html', context)


@login_required(login_url='login')
def dashboard_view(request):
    # Get current user profile - this avoids multiple DB hits
    profile = request.user.profile if hasattr(request.user, 'profile') else get_object_or_404(Profile, user=request.user)
    
    # Cache key for user dashboard data
    cache_key = f"dashboard_data_{profile.id}"
    dashboard_data = cache.get(cache_key)
    
    if not dashboard_data:
        # Fetch all vaults with prefetched media in one query to avoid N+1 problem
        vaults = Vault.objects.filter(owner=profile).prefetch_related('media_files')
        
        # Get vault count
        vault_count = len(vaults)
        
        # Get first vault title if available
        new_vault = vaults[0].title if vault_count > 0 else "📂 No Vaults Available - Create your first vault"
        new_vault_id = vaults[0].id if vault_count > 0 else None
        
        # Prepare vaults with recent media
        # Using Python to filter instead of another DB query
        vaults_with_media = [v for v in vaults if v.media_files.all()]
        recent_media = vaults_with_media[:3]
        
        # File extensions for filtering
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', 'avif']
        video_extensions = ['.mp4', '.webm', '.ogg', '.mov', '.avi', '.mkv']
        
        # Count media by type
        media_files = []
        for vault in vaults:
            media_files.extend(vault.media_files.all())
        
        # Count images and videos
        image_count = sum(1 for m in media_files if any(m.file.name.lower().endswith(ext) for ext in image_extensions))
        video_count = sum(1 for m in media_files if any(m.file.name.lower().endswith(ext) for ext in video_extensions))
        
        vaults_to_created = 5 - vault_count
        
        # Cache the data
        dashboard_data = {
            'vault_count': vault_count,
            'new_vault': new_vault,
            'image_count': image_count,
            'video_count': video_count,
            'new_vault_id': new_vault_id,
            'recent_media': recent_media,
            'vaults_to_created': vaults_to_created,
        }
        
        cache.set(cache_key, dashboard_data, CACHE_TTL)
    
    form = VaultCreationForm()
    if request.method == 'POST':
        form = VaultCreationForm(request.POST)
        if form.is_valid():
            vault = form.save(commit=False)
            vault.owner = profile
            vault.save()
            # Clear cache when data changes
            cache.delete(cache_key)
            # Redirect to the newly created vault's detail view
            return redirect('vault-details', pk=vault.pk, title=vault.title)
    
    context = dashboard_data.copy()
    context['form'] = form
    
    return render(request, 'dashboard.html', context)


@login_required(login_url='login')
def vault_view(request):
    profile = get_object_or_404(Profile, user=request.user)

    # Always fetch and process data from the database
    vaults_qs = Vault.objects.filter(
        owner=profile
    ).annotate(
        media_count=Count('media_files')
    ).order_by('-updated_at')

    # Prepare data for template directly from the annotated queryset
    vaults_data = []
    for vault in vaults_qs:
        uploads_left = VAULT_LIMIT - vault.media_count
        vaults_data.append({
            'vault': vault,
            'media_count': vault.media_count,
            'uploads_left': uploads_left,
            'vault_limit': VAULT_LIMIT,
        })

    vault_count = len(vaults_data)
    vaults_to_create = max(0, 5 - vault_count)

    # Form handling
    form = VaultCreationForm()
    if request.method == 'POST':
        form = VaultCreationForm(request.POST)
        if form.is_valid():
            vault = form.save(commit=False)
            vault.owner = profile
            vault.save()
            return redirect('vault-details', pk=vault.pk, title=vault.title) # Ensure 'vault-details' URL is defined

    # Prepare context for rendering directly from calculated variables
    context = {
        'vaults_with_media_count': vaults_data,
        'vault_count': vault_count,
        'vaults_to_create': vaults_to_create,
        'form': form,
        'now': timezone.now(),
    }
    return render(request, 'vaults/vaults.html', context)








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


def thankY_view(request):
    context = {}
    return render(request, 'thankY_page.html', context)


def uploads_view(request, vault_id):
    # Get the vault object
    vault = get_object_or_404(Vault, pk=vault_id)

    vaut_limit = VAULT_LIMIT

    # --- User Identification ---
    uploader_profile = None
    session_key = None
    user_identifier_filter = {} # Filter criteria for counting user's uploads

    if request.user.is_authenticated:
        try:
            # Assumes a logged-in user has a related Profile object
            uploader_profile = request.user.profile
            user_identifier_filter = {'uploader_profile': uploader_profile}
        except Profile.DoesNotExist:
            # Handle case where logged-in user doesn't have a Profile (shouldn't happen ideally)
            messages.error(request, "Could not identify your profile.")
            # Redirect or return an error response appropriate for your app
            return redirect('some_error_page_or_home')
    else:
        # For anonymous users, use the session key
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        user_identifier_filter = {'uploader_session_key': session_key}

    # --- Calculate User's Upload Count & Remaining ---
    # Count how many files *this specific user/session* has already uploaded to *this* vault
    user_upload_count = VaultMedia.objects.filter(vault=vault, **user_identifier_filter).count()

    # Calculate how many more uploads this user is allowed
    uploads_allowed = vault.uploads_per_person
    uploads_remaining = max(0, uploads_allowed - user_upload_count) # Ensure non-negative

    if request.method == 'POST':
        # Check if the user has any uploads remaining *before* processing the form
        if uploads_remaining <= 0:
            messages.error(request, "You have reached your upload limit for this vault.")
            # Re-render the page showing the limit message
            media_form = VaultMediaForm() # Show an empty form again
            context = {
                'vault': vault,
                'uploads_remaining': 0,
                'media_form': media_form,
                'user_upload_count': user_upload_count,
                'uploads_allowed': uploads_allowed,
            }
            return render(request, 'vaults/uploads_page.html', context)

        media_form = VaultMediaForm(request.POST, request.FILES)
        if media_form.is_valid():
            files = request.FILES.getlist('file') # Get all uploaded files
            files_to_upload_count = len(files)

            # Check if uploading these files exceeds the user's limit
            if user_upload_count + files_to_upload_count > uploads_allowed:
                messages.error(request, f"You can only upload {uploads_remaining} more file(s). You tried to upload {files_to_upload_count}.")
            else:
                # Proceed with saving files
                saved_count = 0
                for f in files:
                    media_instance = VaultMedia(
                        file=f,
                        vault=vault,
                        # Assign the uploader based on whether user is logged in or anonymous
                        uploader_profile=uploader_profile, # Will be None if anonymous
                        uploader_session_key=session_key # Will be None if logged in
                    )
                    try:
                        # --- Optional: Your media processing ---
                        # caption, tags = media_processor.get_caption_and_tags(f)
                        # if caption:
                        #     media_instance.caption = caption
                        # --- End Optional ---

                        media_instance.save() # Save the media instance

                        # --- Optional: Add tags after saving if using TaggableManager ---
                        # if tags:
                        #    media_instance.tags.add(*tags)
                        # --- End Optional ---

                        saved_count += 1
                    except Exception as e:
                        # Log the error e
                        print(f"Error saving file: {e}") # Basic logging
                        messages.error(request, f"An error occurred while saving one of your files: {e}")
                        # Decide if you want to stop or continue processing other files

                if saved_count > 0:
                    messages.success(request, f"{saved_count} file(s) successfully uploaded to this vault! 🎉")

                    # --- Optional: Cache Clearing ---
                    # cache.delete_many([
                    #     f"dashboard_data_{vault.owner_id}",
                    #     f"user_vaults_{vault.owner_id}",
                    #     f"gallery_view_{vault.owner_id}",
                    #     f"everything_view_{vault.owner_id}",
                    # ])
                    # --- End Optional ---

                # Redirect back to the same page after POST to prevent re-submission
                return redirect('uploads', vault_id=vault_id) # Use the name of your upload URL pattern

    # --- Handle GET Request or Invalid POST ---
    else:
        media_form = VaultMediaForm() # Create an empty form for GET requests

    # --- Prepare Context for Template ---
    context = {
        'vault': vault,
        'uploads_remaining': uploads_remaining, # User-specific remaining uploads
        'media_form': media_form,
        'user_upload_count': user_upload_count, # How many this user uploaded
        'uploads_allowed': uploads_allowed, # The limit per person
        'total_vault_media_count': VaultMedia.objects.filter(vault=vault).count(),
        'vaut_limit': vaut_limit, # Total vault limit
    }
    return render(request, 'vaults/uploads_page.html', context)


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