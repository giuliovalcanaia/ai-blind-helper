from google import genai
from google.genai import types
from config import Config

class TextClientApplication:
    
    def generate_text_by_imagem_text(self, prompt: str, image_part_data: dict):
        print("[TextClientApplication generate_text_by_imagem_text] Initializing client for multimodal text generation")
        
        client = genai.Client(
            api_key = Config.API_KEY,
            http_options={'api_version': Config.API_VERSION_TEXT_API_GEMINI_3})

        print(f"[TextClientApplication generate_text_by_imagem_text] Sending prompt and image to model: {Config.MODEL_TEXT_GENERATOR}")
        
        try:
            response = client.models.generate_content(
                model=Config.MODEL_TEXT_GENERATOR,
                contents=[
                    types.Content(
                        parts=[
                            types.Part(text=str(prompt)), 
                            types.Part(
                                inline_data=image_part_data
                            )
                        ]
                    )
                ]
            )
            
            print("[TextClientApplication generate_text_by_imagem_text] Successfully received response from Text API")
            return response.text

        except Exception as e:
            print(f"[TextClientApplication generate_text_by_imagem_text] Error generating content: {e}")
            raise e