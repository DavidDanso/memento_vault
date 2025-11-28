from celery import shared_task
from django.conf import settings
from .models import VaultMedia
from .utils import MediaProcessor
import logging

logger = logging.getLogger(__name__)

# Initialize MediaProcessor globally for the worker
GEMINI_API_KEY = settings.GEMINI_API_KEY
media_processor = MediaProcessor(GEMINI_API_KEY)

@shared_task
def process_media_ai(media_id):
    """
    Background task to generate caption and tags for a media file using AI.
    """
    try:
        media = VaultMedia.objects.get(id=media_id)
    except VaultMedia.DoesNotExist:
        logger.error(f"VaultMedia with id {media_id} not found.")
        return

    logger.info(f"Starting AI processing for media {media_id}")

    try:
        # Open the file from storage
        with media.file.open('rb') as f:
            # The MediaProcessor expects an object with content_type, seek, read.
            # Django's File object usually has these, but let's ensure content_type is set if possible.
            # If not, MediaProcessor defaults to unknown/unknown and checks magic bytes or extension?
            # Looking at utils.py: content_type = getattr(file, "content_type", "unknown/unknown")
            # We might need to guess it or rely on the file extension check in utils.py
            
            # Let's mock content_type if it's missing, based on name
            if not hasattr(f, 'content_type'):
                import mimetypes
                content_type, _ = mimetypes.guess_type(media.file.name)
                f.content_type = content_type or 'application/octet-stream'

            caption, tags = media_processor.get_caption_and_tags_sync(f)

        if caption:
            media.caption = caption
        
        if tags:
            media.tags.add(*tags)
            
        media.save()
        logger.info(f"AI processing completed for media {media_id}")

    except Exception as e:
        logger.error(f"Error processing media {media_id}: {str(e)}", exc_info=True)
