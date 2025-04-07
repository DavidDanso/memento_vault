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

    cache_key = f"user_vaults_{profile.id}"
    cached_data = cache.get(cache_key)

    if cached_data is None:
        vaults_qs = Vault.objects.filter(
            owner=profile
        ).annotate(
            media_count=Count('media_files')
        ).order_by('-updated_at')

        # Prepare data for template directly from the annotated queryset
        vaults_data = []
        for vault in vaults_qs:
            allowed_uploads = vault.max_media_items
            uploads_left = allowed_uploads - vault.media_count
            vaults_data.append({
                'vault': vault,
                'media_count': vault.media_count,
                'allowed_uploads': allowed_uploads,
                'uploads_left': uploads_left,
            })

        vault_count = len(vaults_data) # Get count after processing
        vaults_to_create = max(0, 3 - vault_count) # Ensure non-negative

        # Data to cache
        cached_data = {
            'vaults_with_media_count': vaults_data,
            'vault_count': vault_count,
            'vaults_to_created': vaults_to_create,
        }
        cache.set(cache_key, cached_data, CACHE_TTL)

    # Form handling remains the same
    form = VaultCreationForm()
    if request.method == 'POST':
        form = VaultCreationForm(request.POST)
        if form.is_valid():
            vault = form.save(commit=False)
            vault.owner = profile
            vault.save()
            cache.delete(cache_key) # Invalidate cache on change
            # Consider passing slug instead of title if title can change or has special chars
            return redirect('vault-details', pk=vault.pk, title=vault.title) # Ensure 'vault-details' URL is defined

    # Prepare context for rendering
    context = cached_data.copy() # Use the cached or freshly generated data
    context['form'] = form
    context['now'] = timezone.now()

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
    remaining_uploads = vault.max_media_items - media_count
    
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
            
            if media_count + current_file_count > vault.max_media_items:
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
        'file_count': file_count
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


@login_required(login_url='login')
def uploads_view(request, vault_id):
    # Get the vault with its media files in a single query
    vault = get_object_or_404(
        Vault.objects.annotate(media_count=Count('media_files')),
        pk=vault_id
    )
    
    # Clear the file_count session value by default
    file_count = request.session.pop('file_count', 0)
    
    # Calculate remaining uploads
    uploads_remaining = vault.max_media_items - vault.media_count
    
    if request.method == 'POST':
        media_form = VaultMediaForm(request.POST, request.FILES)
        if media_form.is_valid():
            files = request.FILES.getlist('file')
            current_file_count = len(files)
            
            if vault.media_count + current_file_count > vault.max_media_items:
                messages.error(request, f"Only {uploads_remaining} upload(s) left. Please cut back on your uploads.")
            else:
                request.session['file_count'] = current_file_count
                
                # Process files in bulk
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
                
                # Clear the file count after successful upload
                request.session['file_count'] = 0
                messages.success(request, f"{current_file_count} file(s) successfully uploaded to this vault! 🎉")
                # Clear caches related to this vault
                cache.delete_many([
                    f"dashboard_data_{vault.owner_id}",
                    f"user_vaults_{vault.owner_id}",
                    f"gallery_view_{vault.owner_id}",
                    f"everything_view_{vault.owner_id}",
                ])
                # Recalculate uploads remaining
                uploads_remaining -= current_file_count
                return redirect('uploads', vault_id=vault_id)
    else:
        media_form = VaultMediaForm()
    
    context = {
        'vault': vault,
        'uploads_remaining': uploads_remaining,
        'media_form': media_form,
        'media_count': vault.media_count,
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