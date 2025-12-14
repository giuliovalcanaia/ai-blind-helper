import asyncio
from typing import Optional

# Importando sua classe de câmera existente
# (Assumindo que ela está em um arquivo chamado video_source.py ou similar)
from manager import CameraSource 

class DescriptionApplication:
    def __init__(self, camera_index=0):
        # Instancia o manager da câmera
        self.camera_manager = CameraSource(camera_index=camera_index)
        
        # Prompt que instrui a IA sobre o que fazer com a imagem
        self.prompt = "Analise a imagem capturada agora e descreva detalhadamente o ambiente, objetos e contexto."

    def get_prompt(self):
        return self.prompt