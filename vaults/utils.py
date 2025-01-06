# utils.py
import google.generativeai as genai
from PIL import Image

class MediaProcessor:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def get_caption_and_tags(self, file):
        if file.content_type.startswith('image/'):
            return self._process_image(file)
        elif file.content_type.startswith('video/'):
            return "Video file uploaded", []
        return None, []

    def _process_image(self, file):
        try:
            img = Image.open(file)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Get caption
            caption_response = self.model.generate_content([
                'Describe this image in a single sentence, focusing on key visual elements and details, no longer than 30 words', 
                img
            ])
            
            # Get emotion tags
            tags_response = self.model.generate_content([
                'Analyze facial expressions and emotions in this image. Return exactly 4 emotion-related tags as a comma-separated list. If no faces, return general image tags.', 
                img
            ])
            
            tags = [tag.strip() for tag in tags_response.text.split(',')][:4]
            return caption_response.text, tags
            
        except Exception as e:
            print(f"Processing error: {str(e)}")
            return None, []
    