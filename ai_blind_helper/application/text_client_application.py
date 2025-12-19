from google import genai
from google.genai import types
from config import Config

class TextClientApplication:
    
    def generate_text_by_imagem_text(self, prompt: str, image_part_data: dict):
        print("[TextClientApplication generate_text_by_imagem_text] Inicializando cliente para geração de texto multimodal")
        
        client = genai.Client(
            api_key = Config.API_KEY,
            http_options={'api_version': Config.API_VERSION_TEXT_API_GEMINI_3})

        print(f"[TextClientApplication generate_text_by_imagem_text] Enviando prompt e imagem para o modelo: {Config.MODEL_TEXT_GENERATOR}")
        
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
            
            print("[TextClientApplication generate_text_by_imagem_text] Resposta recebida com sucesso da API de Texto")
            return response.text

        except Exception as e:
            print(f"[TextClientApplication generate_text_by_imagem_text] Erro ao gerar conteúdo: {e}")
            raise e