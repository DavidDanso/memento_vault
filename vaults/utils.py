import google.generativeai as genai
from PIL import Image
import asyncio
from typing import Tuple, List, Optional, Any, Dict
from functools import lru_cache, partial
import concurrent.futures
import io
import hashlib
import logging
import json
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

DEFAULT_OPERATION_TIMEOUT = 45  # reduced for better UX feedback

class MediaProcessor:
    def __init__(self, api_key: str, max_workers: int = 8):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self._cache: Dict[str, Tuple[str, List[str]]] = {}
        self._cache_lock = threading.Lock()
        logging.info("MediaProcessor initialized (model=%s, workers=%d)", self.model.model_name, max_workers)

        self._async_loop: Optional[asyncio.AbstractEventLoop] = None
        self._worker_thread: Optional[threading.Thread] = None
        self._loop_ready_event = threading.Event()
        self._start_async_worker()

    def _start_async_worker(self):
        if self._worker_thread and self._worker_thread.is_alive():
            return
        self._worker_thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self._worker_thread.start()
        if not self._loop_ready_event.wait(timeout=5):
            raise RuntimeError("MediaProcessor async worker failed to start.")

    def _run_async_loop(self):
        self._async_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._async_loop)
        self._loop_ready_event.set()
        self._async_loop.run_forever()

    @lru_cache(maxsize=512)
    def _get_file_hash(self, file_content: bytes) -> str:
        return hashlib.md5(file_content).hexdigest()

    def get_caption_and_tags(self, file: Any, timeout: int = DEFAULT_OPERATION_TIMEOUT) -> Tuple[Optional[str], List[str]]:
        if not self._async_loop or not self._async_loop.is_running():
            return "Error: Processing unavailable", []
        if not all(hasattr(file, attr) for attr in ["content_type", "seek", "read"]):
            return "Invalid file object", []

        content_type = getattr(file, "content_type", "unknown/unknown")
        if content_type.startswith("image/"):
            coro = self._process_image_async_task(file)
            future = asyncio.run_coroutine_threadsafe(coro, self._async_loop)
            try:
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                return "Processing timed out", []
        elif content_type.startswith("video/"):
            return "Video processing not implemented", []
        return None, []

    async def _process_image_async_task(self, file: Any) -> Tuple[Optional[str], List[str]]:
        try:
            file.seek(0)
            file_content = await self._async_loop.run_in_executor(self._executor, file.read)
            if not file_content:
                return "Error reading file (empty)", []

            file_hash = self._get_file_hash(file_content)

            with self._cache_lock:
                if file_hash in self._cache:
                    return self._cache[file_hash]

            img_data = await self._async_loop.run_in_executor(self._executor, self._preprocess_image_sync, file_content)
            if not img_data:
                return "Image preprocessing failed", []

            caption, tags = await self._get_caption_and_tags_combined(img_data)
            if caption and not caption.lower().startswith("error"):
                with self._cache_lock:
                    self._cache[file_hash] = (caption, tags)
            return caption, tags

        except Exception as e:
            logging.error("Critical error in _process_image_async_task: %s", e, exc_info=True)
            return "Internal processing error", []

    def _preprocess_image_sync(self, file_content: bytes) -> Optional[bytes]:
        try:
            img = Image.open(io.BytesIO(file_content))
            if img.mode != "RGB":
                img = img.convert("RGB")
            max_dimension = 768  # smaller = faster
            if max(img.size) > max_dimension:
                img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format="JPEG", quality=75, optimize=True)
            return img_byte_arr.getvalue()
        except Exception as e:
            logging.error("Image preprocessing failed: %s", e)
            return None

    async def _get_caption_and_tags_combined(self, img_data: bytes) -> Tuple[Optional[str], List[str]]:
        try:
            prompt = """Analyze the image and return ONLY JSON:
{"caption": "...", "tags": ["...", "...", "...", "...", "..."]}"""

            content_parts = [prompt, {"mime_type": "image/jpeg", "data": img_data}]
            generation_config = {"temperature": 0.2, "max_output_tokens": 180, "response_mime_type": "application/json"}

            func = partial(self.model.generate_content, generation_config=generation_config)
            api_response = await self._async_loop.run_in_executor(self._executor, func, content_parts)

            if not getattr(api_response, "parts", None):
                return "Caption/Tags unavailable", []

            try:
                result_json = json.loads(api_response.text)
                caption = str(result_json.get("caption", "")).strip()
                tags = [str(tag).lower().strip() for tag in result_json.get("tags", [])][:5]
                return caption or "Caption unavailable", tags
            except Exception:
                return "Failed to parse JSON response", []

        except Exception as e:
            logging.error("Caption API call failed: %s", e, exc_info=True)
            return "Caption/Tags unavailable", []

    def clear_cache(self):
        with self._cache_lock:
            self._cache.clear()
        self._get_file_hash.cache_clear()

    def shutdown(self, timeout: int = 5):
        if self._async_loop and self._async_loop.is_running():
            self._async_loop.call_soon_threadsafe(self._async_loop.stop)
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=timeout)
        self._executor.shutdown(wait=False)
