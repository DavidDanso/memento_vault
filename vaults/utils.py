import google.generativeai as genai
from PIL import Image
import asyncio
from typing import Tuple, List, Optional, Any
from functools import lru_cache
import concurrent.futures
import io
import hashlib
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MediaProcessor:
    """
    Processes uploaded media (images) to generate captions and tags using Gemini,
    """

    def __init__(self, api_key: str, max_workers: int = 10):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        # Simple in-memory cache for results based on content hash
        self._cache = {}
        logging.info("MediaProcessor initialized with model: %s", self.model.model_name)

    # LRU Cache for hashing function based on content bytes
    @lru_cache(maxsize=256)
    def _get_file_hash(self, file_content: bytes) -> str:
        return hashlib.md5(file_content).hexdigest()

    def get_caption_and_tags(self, file: Any) -> Tuple[Optional[str], List[str]]:
        # Check if the input object has the required attributes
        if not all(hasattr(file, attr) for attr in ['content_type', 'seek', 'read']):
            logging.error("Invalid file object provided. Must have 'content_type', 'seek', and 'read' methods.")
            return "Invalid file object", []

        content_type = getattr(file, 'content_type', 'unknown/unknown')

        if content_type.startswith('image/'):
            try:
                # Run the async image processing function synchronously
                # Use asyncio.run() to manage the event loop for this call
                return asyncio.run(self._process_image(file))
            except RuntimeError as e:
                # Handle cases where asyncio.run might conflict if called from an existing loop
                logging.warning("RuntimeError calling asyncio.run (maybe nested loops?): %s. Trying another approach.", e)
                # Fallback or alternative loop management might be needed depending on the environment
                # For simplicity here, we log the error and return failure.
                # In complex async apps, ensure loop management is handled correctly.
                return "Error running async processing", []
            except Exception as e:
                logging.error("Unexpected error in get_caption_and_tags: %s", e, exc_info=True)
                return "Processing error", []

        elif content_type.startswith('video/'):
            logging.info("Video file type (%s) received, processing not implemented.", content_type)
            return "Video processing not implemented", []
        else:
            logging.warning("Unsupported content type: %s", content_type)
            return None, [] # Return None for unsupported types consistent with original logic

    async def _process_image(self, file: Any) -> Tuple[Optional[str], List[str]]:
        try:
            try:
                file.seek(0)
                file_content = file.read()
            except Exception as read_err:
                 logging.error("Failed to read file object: %s", read_err, exc_info=True)
                 return "Error reading file", []

            file_hash = self._get_file_hash(file_content)

            if file_hash in self._cache:
                logging.info("Cache hit for hash: %s", file_hash)
                return self._cache[file_hash]

            content_type = getattr(file, 'content_type', 'image/unknown')
            logging.info("Processing image (hash: %s, type: %s, size: %d bytes)",
                         file_hash, content_type, len(file_content))

            # --- Image Preprocessing ---
            try:
                img = Image.open(io.BytesIO(file_content))
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                max_dimension = 1024
                if max(img.size) > max_dimension:
                    img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG', quality=85)
                img_data = img_byte_arr.getvalue()
                logging.info("Image preprocessed (new size: %s, %d bytes JPEG)", img.size, len(img_data))

            except Exception as img_err:
                logging.error("Image processing/conversion error: %s", img_err, exc_info=True)
                return "Error processing image", []

            # --- Concurrent API Calls ---
            loop = asyncio.get_running_loop()
            caption_future = loop.run_in_executor(self._executor, self._get_caption, img_data)
            tags_future = loop.run_in_executor(self._executor, self._get_tags, img_data)

            caption, tags = await asyncio.gather(caption_future, tags_future)

            result = (caption, tags)
            self._cache[file_hash] = result
            logging.info("Successfully generated caption and tags for hash: %s", file_hash)
            return result

        except Exception as e:
            logging.error("Error in _process_image: %s", e, exc_info=True)
            return None, []

    def _get_caption(self, img_data: bytes) -> str:
        """Calls the Gemini API to generate an image caption."""
        try:
            prompt = "Describe this image in detail, focusing on main subjects, setting, and mood. Max 50 words."
            content_parts = [
                prompt,
                {"mime_type": "image/jpeg", "data": img_data}
            ]
            response = self.model.generate_content(
                content_parts,
                generation_config={
                    "temperature": 0.4,
                    "max_output_tokens": 150
                }
            )
            if response.parts:
                return response.text.strip()
            else:
                feedback = getattr(response, 'prompt_feedback', 'Unknown reason')
                logging.warning("Caption generation returned no content. Reason: %s", feedback)
                # Match original behavior: return "No caption generated"
                return "No caption generated"
        except Exception as e:
            logging.error("Caption generation API error: %s", e, exc_info=True)
            # Match original behavior: return "Caption unavailable"
            return "Caption unavailable" # Indicate error consistent with original

    def _get_tags(self, img_data: bytes) -> List[str]:
        """Calls the Gemini API to generate image tags."""
        try:
            prompt = "List exactly 5 relevant comma-separated tags for this image: key objects, dominant colors, style/genre, overall mood."
            content_parts = [
                 prompt,
                {"mime_type": "image/jpeg", "data": img_data}
            ]
            response = self.model.generate_content(
                content_parts,
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 100
                }
            )
            if response.parts and response.text:
                tags_raw = response.text.strip()
                tags = [tag.strip().lower() for tag in tags_raw.split(',') if tag.strip()]
                return tags[:5]
            else:
                feedback = getattr(response, 'prompt_feedback', 'Unknown reason')
                logging.warning("Tag generation returned no content. Reason: %s", feedback)
                return []
        except Exception as e:
            logging.error("Tag generation API error: %s", e, exc_info=True)
            return []

    def clear_cache(self):
        """Clears the internal result cache and the hash function cache."""
        count = len(self._cache)
        self._cache.clear()
        self._get_file_hash.cache_clear()
        logging.info("Cleared %d items from result cache and hash cache.", count)

    def shutdown(self):
        """Shuts down the thread pool executor gracefully."""
        logging.info("Shutting down ThreadPoolExecutor...")
        # Ensure executor exists before shutting down
        if self._executor:
             self._executor.shutdown(wait=True)
        logging.info("ThreadPoolExecutor shut down.")

