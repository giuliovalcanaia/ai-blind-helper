import asyncio
from typing import Optional

# Importando sua classe de câmera existente
from manager import CameraSource 

class TranscriptionApplication:
    def __init__(self):
        
        # Prompt focado especificamente em transcrever texto (OCR)
        self.prompt = (
            "Analise a imagem e transcreva todo o texto visível nela. "
        )

    def get_prompt(self):
        return self.prompt