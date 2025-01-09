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
            
            # Enhanced prompts for better search capabilities
            caption_prompt = """
            Describe this image in detail, including:
            - Colors present (explicitly mention colors)
            - Objects and their attributes
            - Setting or environment
            - Any notable visual characteristics
            Limit to 50 words.
            """
            
            tags_prompt = """
            Analyze this image and provide tags as a comma-separated list covering:
            - Dominant colors
            - Emotions or mood
            - Key objects
            - Scene type or setting
            Return exactly 5 descriptive tags.
            """
            
            caption_response = self.model.generate_content([caption_prompt, img])
            tags_response = self.model.generate_content([tags_prompt, img])
            
            tags = [tag.strip().lower() for tag in tags_response.text.split(',')][:5]
            return caption_response.text, tags
            
        except Exception as e:
            print(f"Processing error: {str(e)}")
            return None, []

