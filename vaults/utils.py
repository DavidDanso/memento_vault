import google.generativeai as genai
from PIL import Image
import asyncio
from typing import Tuple, List, Optional, Any, Dict
from functools import lru_cache, partial # Import partial
import concurrent.futures
import io
import hashlib
import logging
import json
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DEFAULT_OPERATION_TIMEOUT = 60

class MediaProcessor:
    def __init__(self, api_key: str, max_workers: int = 10):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self._cache = {}
        logging.info("MediaProcessor initializing (model: %s, max_workers: %d)...", self.model.model_name, max_workers)
        self._async_loop: Optional[asyncio.AbstractEventLoop] = None
        self._worker_thread: Optional[threading.Thread] = None
        self._loop_ready_event = threading.Event()
        self._start_async_worker()
        logging.info("MediaProcessor initialized and async worker started.")

    def _start_async_worker(self):
        if self._worker_thread is not None and self._worker_thread.is_alive():
            logging.warning("Async worker thread already running.")
            return
        self._worker_thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self._worker_thread.start()
        if not self._loop_ready_event.wait(timeout=10):
            logging.error("Async worker thread event loop failed to start in time.")
            raise RuntimeError("MediaProcessor async worker failed to initialize.")
        logging.info("Async worker thread and event loop started successfully.")

    def _run_async_loop(self):
        try:
            self._async_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._async_loop)
            self._loop_ready_event.set()
            self._async_loop.run_forever()
        except Exception as e:
            logging.critical("Async worker loop crashed: %s", e, exc_info=True)
        finally:
            if self._async_loop and not self._async_loop.is_closed():
                try:
                    tasks = asyncio.all_tasks(self._async_loop)
                    for task in tasks:
                        task.cancel()
                    group = asyncio.gather(*tasks, return_exceptions=True)
                    self._async_loop.run_until_complete(group)
                    self._async_loop.run_until_complete(self._async_loop.shutdown_asyncgens())
                except Exception as e_shutdown:
                    logging.error("Error during async loop shutdown cleanup: %s", e_shutdown)
                finally:
                    self._async_loop.close()
            logging.info("Async worker thread event loop stopped.")

    @lru_cache(maxsize=256)
    def _get_file_hash(self, file_content: bytes) -> str:
        return hashlib.md5(file_content).hexdigest()

    def get_caption_and_tags(self, file: Any, timeout: int = DEFAULT_OPERATION_TIMEOUT) -> Tuple[Optional[str], List[str]]:
        if not self._async_loop or not self._async_loop.is_running():
            logging.error("Async worker is not running. Cannot process request.")
            return "Error: Processing service unavailable", []
        if not all(hasattr(file, attr) for attr in ['content_type', 'seek', 'read']):
            logging.error("Invalid file object provided.")
            return "Invalid file object", []
        content_type = getattr(file, 'content_type', 'unknown/unknown')
        if content_type.startswith('image/'):
            try:
                coro = self._process_image_async_task(file)
                future = asyncio.run_coroutine_threadsafe(coro, self._async_loop)
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                logging.error("Processing timed out after %s seconds for content type %s.", timeout, content_type)
                return "Processing timed out", []
            except Exception as e:
                logging.error("Error submitting task to async worker or getting result: %s", e, exc_info=True)
                return "Processing submission error", []
        elif content_type.startswith('video/'):
            logging.info("Video file type (%s) received, processing not implemented.", content_type)
            return "Video processing not implemented", []
        else:
            logging.warning("Unsupported content type: %s", content_type)
            return None, []

    async def _process_image_async_task(self, file: Any) -> Tuple[Optional[str], List[str]]:
        file_content: Optional[bytes] = None
        img_data: Optional[bytes] = None
        file_hash = "unknown_hash" # Initialize file_hash
        try:
            try:
                file.seek(0)
                file_content = await self._async_loop.run_in_executor(self._executor, file.read)
                if not file_content:
                    logging.error("File content is empty after reading.")
                    return "Error reading file (empty)", []
            except Exception as read_err:
                 logging.error("Failed to read file object: %s", read_err, exc_info=True)
                 return "Error reading file", []

            file_hash = self._get_file_hash(file_content) # Assign actual hash

            if file_hash in self._cache:
                logging.info("Cache hit for hash: %s", file_hash)
                return self._cache[file_hash]

            content_type = getattr(file, 'content_type', 'image/unknown')
            logging.info("Processing image (hash: %s, type: %s, size: %d bytes)",
                         file_hash, content_type, len(file_content))

            try:
                img_data = await self._async_loop.run_in_executor(
                    self._executor, self._preprocess_image_sync, file_content
                )
                if img_data is None:
                    return "Error processing image (preprocessing failed)", []
                logging.info("Image preprocessed (%d bytes JPEG) for hash: %s", len(img_data), file_hash)
            except Exception as img_prep_err:
                 logging.error("Image preprocessing task execution failed for hash %s: %s", file_hash, img_prep_err, exc_info=True)
                 return "Error processing image (task execution)", []

            caption, tags = await self._get_caption_and_tags_combined(img_data)
            result = (caption, tags)

            # Conditional logging and caching
            is_successful_api_call = caption is not None and not \
                                     any(err_str in caption.lower() for err_str in ["unavailable", "error", "failed", "not found in json"])

            if is_successful_api_call:
                self._cache[file_hash] = result
                logging.info("Successfully generated and cached caption and tags for hash: %s", file_hash)
            else:
                logging.warning("API call for hash %s did not yield a usable result. Caption: '%s'. Not caching.", file_hash, caption)
            return result

        except Exception as e:
            logging.error("Critical error in _process_image_async_task for hash %s: %s", file_hash, e, exc_info=True)
            return "Internal processing error", []

    def _preprocess_image_sync(self, file_content: bytes) -> Optional[bytes]:
        try:
            img = Image.open(io.BytesIO(file_content))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            max_dimension = 1024
            if max(img.size) > max_dimension:
                img.thumbnail((max_dimension, max_dimension), Image.Resampling.BICUBIC)
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG', quality=80)
            return img_byte_arr.getvalue()
        except Exception as img_err:
            logging.error("PIL image processing failed: %s", img_err, exc_info=True)
            return None

    async def _get_caption_and_tags_combined(self, img_data: bytes) -> Tuple[Optional[str], List[str]]:
        try:
            prompt = """Analyze the image and provide:
1.  A descriptive caption (max 50 words) focusing on main subjects, setting, and mood.
2.  A list of exactly 5 relevant tags (key objects, dominant colors, style/genre, overall mood).

Return the result ONLY as a valid JSON object with keys "caption" and "tags" (where tags is a list of strings). Example:
{"caption": "A sunset over a calm lake.", "tags": ["sunset", "lake", "orange", "calm", "nature"]}"""
            content_parts = [prompt, {"mime_type": "image/jpeg", "data": img_data}]

            generation_config_dict = {
                "temperature": 0.3,
                "max_output_tokens": 250,
                "response_mime_type": "application/json",
            }

            # Use functools.partial to correctly pass keyword arguments
            # to self.model.generate_content when it's called by the executor.
            func_to_call = partial(
                self.model.generate_content,
                generation_config=generation_config_dict
                # You could add other keyword args here like safety_settings=your_settings_dict
            )

            api_response = await self._async_loop.run_in_executor(
                self._executor,
                func_to_call,    # Call the partial function
                content_parts    # Pass 'contents' as the remaining positional argument
            )

            if api_response.parts:
                try:
                    result_json = json.loads(api_response.text)
                    caption = result_json.get("caption", "Caption not found in JSON")
                    tags_list = result_json.get("tags", [])
                    if isinstance(caption, str) and isinstance(tags_list, list):
                        return caption.strip(), [str(tag).strip().lower() for tag in tags_list][:5]
                    else:
                        logging.warning("Parsed JSON has unexpected types. Caption: %s, Tags: %s", type(caption), type(tags_list))
                        return "Failed to parse JSON (type error)", []
                except json.JSONDecodeError as json_err:
                    logging.error("Failed to decode JSON: %s\nResponse: %s", json_err, api_response.text[:200])
                    return "Failed to parse JSON response", []
                except Exception as parse_err:
                    logging.error("Error processing API response JSON: %s", parse_err, exc_info=True)
                    return "Failed to parse JSON (unknown error)", []
            else:
                feedback = getattr(api_response, 'prompt_feedback', 'Unknown reason')
                logging.warning("Combined API call returned no content. Reason: %s", feedback)
                return "Caption/Tags unavailable (no API content)", []
        except Exception as e: # This will now catch TypeErrors from incorrect calls too, if any remained
            logging.error("Combined generation API call error: %s", e, exc_info=True) # This log was key
            return "Caption/Tags unavailable (API Error)", []


    def clear_cache(self):
        count = len(self._cache)
        self._cache.clear()
        self._get_file_hash.cache_clear()
        logging.info("Cleared %d items from result cache and hash cache.", count)

    def shutdown(self, timeout: int = 10):
        logging.info("MediaProcessor shutting down...")
        if self._async_loop and self._async_loop.is_running():
            logging.info("Stopping async worker loop...")
            self._async_loop.call_soon_threadsafe(self._async_loop.stop)
        if self._worker_thread and self._worker_thread.is_alive():
            logging.info("Joining async worker thread...")
            self._worker_thread.join(timeout=timeout)
            if self._worker_thread.is_alive():
                logging.warning("Async worker thread did not terminate in time.")
        if self._executor:
            logging.info("Shutting down ThreadPoolExecutor...")
            self._executor.shutdown(wait=True)
        logging.info("MediaProcessor shutdown complete.")