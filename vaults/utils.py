# utils.py

import google.generativeai as genai

def generate_caption_with_gemini(file_path, api_key, file_type):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        with open(file_path, 'rb') as file:
            file_data = file.read()

        # Validate file data
        if not file_data:
            raise ValueError("No data found in the file")

        # Define the prompt based on file type
        if file_type == 'image':
            prompt = "Generate a caption for this image."
        elif file_type == 'video':
            prompt = "Generate a caption for this video."
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        # Generate the content
        response = model.generate_content([prompt, file_data])

        if not response or not hasattr(response, 'text'):
            raise ValueError("Invalid response from Gemini API")

        return response.text

    except Exception as e:
        print(f"Error generating caption: {e}")
        raise
