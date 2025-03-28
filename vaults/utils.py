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
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
        self._cache = {}

    @lru_cache(maxsize=100)
    def _get_file_hash(self, file_content: bytes) -> str:
        return hashlib.md5(file_content).hexdigest()

    def get_caption_and_tags(self, file) -> Tuple[Optional[str], List[str]]:
        if file.content_type.startswith('image/'):
            return asyncio.run(self._process_image(file))
        elif file.content_type.startswith('video/'):
            return "Video file uploaded", []
        return None, []

    async def _process_image(self, file) -> Tuple[Optional[str], List[str]]:
        try:
            file.seek(0)
            file_content = file.read()
            file_hash = self._get_file_hash(file_content)

            if file_hash in self._cache:
                return self._cache[file_hash]

            img = Image.open(io.BytesIO(file_content))
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Resize image to max 1024px on longest side
            max_size = 1024
            width, height = img.size
            if max(width, height) > max_size:
                if width > height:
                    new_width = max_size
                    new_height = int(height * (max_size / width))
                else:
                    new_height = max_size
                    new_width = int(width * (max_size / height))
                img = img.resize((new_width, new_height), Image.LANCZOS)

            # Convert resized image to JPEG bytes
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG')
            img_data = img_byte_arr.getvalue()

            loop = asyncio.get_event_loop()
            caption_future = loop.run_in_executor(self._executor, self._get_caption, img_data)
            tags_future = loop.run_in_executor(self._executor, self._get_tags, img_data)
            caption, tags = await asyncio.gather(caption_future, tags_future)

            result = (caption, tags)
            self._cache[file_hash] = result
            return result

        except Exception as e:
            print(f"Processing error: {str(e)}")
            return None, []

    def _get_caption(self, img_data: bytes) -> str:
        try:
            response = self.model.generate_content(
                [
                    "Describe this image in detail, including colors, objects, attributes, setting. 50 words max.",
                    {"mime_type": "image/jpeg", "data": img_data}
                ],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=200
                )
            )
            return response.text if response.text else "No caption generated"
        except Exception as e:
            print(f"Caption error: {str(e)}")
            return "Caption unavailable"

    def _get_tags(self, img_data: bytes) -> List[str]:
        try:
            response = self.model.generate_content(
                [
                    "List 5 comma-separated tags: dominant colors, emotions, key objects, scene type.",
                    {"mime_type": "image/jpeg", "data": img_data}
                ],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=100
                )
            )
            if not response.text:
                return []
            return [tag.strip().lower() for tag in response.text.split(',')][:5]
        except Exception as e:
            print(f"Tag error: {str(e)}")
            return []

    def clear_cache(self):
        self._cache.clear()
        self._get_file_hash.cache_clear()