# utils.py
import google.generativeai as genai
from PIL import Image
import io
from django.core.files.uploadedfile import InMemoryUploadedFile

class MediaProcessor:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def get_caption(self, file):
        """Process file and generate caption"""
        if isinstance(file, InMemoryUploadedFile):
            if file.content_type.startswith('image/'):
                return self._process_image(file)
            elif file.content_type.startswith('video/'):
                return "Video file uploaded - automatic caption generation not available"
        return None

    def _process_image(self, file):
        """Process image and get caption from Gemini"""
        try:
            img = Image.open(file)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            response = self.model.generate_content(['Describe this image in a single sentence, focusing on key visual elements and details, no longer than 30 words', img])
            return response.text
            
        except Exception as e:
            print(f"Image processing error: {str(e)}")
            return None