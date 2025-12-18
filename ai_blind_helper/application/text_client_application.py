from google import genai
from google.genai import types
from config import Config

class TextClientApplication:
    
    def generate_text_by_imagem_text(self, prompt: str, image_part_data: dict):
        # NOTA: O cliente v1alpha usa 'api_key' ou a variável de ambiente. 
        # Certifique-se de que a API Key esteja configurada, se necessário, adicione `api_key=Config.API_KEY`
        client = genai.Client(
            api_key = Config.API_KEY,
            http_options={'api_version': Config.API_VERSION_TEXT_API_GEMINI_3})

        # O `image_part_data` deve ser o dicionário com 'data' (blob base64) e 'mime_type'.
        # Por exemplo: {"data": base64_string, "mime_type": "image/jpeg"}

        response = client.models.generate_content(
            model=Config.MODEL_TEXT_GENERATOR,
            contents=[
                types.Content(
                    parts=[
                        # --- CORREÇÃO: Use o construtor direto, não from_text ---
                        types.Part(text=str(prompt)), 
                        
                        # Parte da imagem
                        types.Part(
                            inline_data=image_part_data
                        )
                    ]
                )
            ]
        )

        return response.text