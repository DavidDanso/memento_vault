import google.generativeai as genai
from PIL import Image
import asyncio
from functools import lru_cache
import concurrent.futures
from typing import Tuple, List, Optional
import io
import hashlib

class MediaProcessor:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
        self._cache = {}

    @lru_cache(maxsize=100)
    def _get_file_hash(self, file_content: bytes) -> str:
        return hashlib.md5(file_content).hexdigest()

    def get_caption_and_tags(self, file) -> Tuple[str, List[str]]:
        if file.content_type.startswith('image/'):
            return asyncio.run(self._process_image(file))
        elif file.content_type.startswith('video/'):
            return "Video file uploaded", []
        return None, []

    async def _process_image(self, file) -> Tuple[Optional[str], List[str]]:
        try:
            file_content = file.read()
            file_hash = self._get_file_hash(file_content)

            if file_hash in self._cache:
                return self._cache[file_hash]

            img = Image.open(io.BytesIO(file_content))
            if img.mode != 'RGB':
                img = img.convert('RGB')

            caption = self._get_caption(img)
            tags = self._get_tags(img)

            result = (caption, tags)
            self._cache[file_hash] = result
            return result

        except Exception as e:
            print(f"Processing error: {str(e)}")
            return None, []

    def _get_caption(self, img) -> str:
        response = self.model.generate_content([
            "Describe this image in detail, including colors, objects, attributes, setting. 50 words max.",
            img
        ])
        return response.text

    def _get_tags(self, img) -> List[str]:
        response = self.model.generate_content([
            "List 5 comma-separated tags: dominant colors, emotions, key objects, scene type.",
            img
        ])
        return [tag.strip().lower() for tag in response.text.split(',')][:5]

    def clear_cache(self):
        self._cache.clear()
        self._get_file_hash.cache_clear()