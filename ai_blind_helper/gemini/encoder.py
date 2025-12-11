class GeminiProtocolEncoder:
    """Responsável por formatar os dados para o padrão da API"""
    
    @staticmethod
    def encode_audio(pcm_data):
        return {
            "data": pcm_data, 
            "mime_type": "audio/pcm"
        }

    @staticmethod
    def encode_image(jpeg_bytes):
        return {
            "mime_type": "image/jpeg", 
            "data": base64.b64encode(jpeg_bytes).decode()
        }