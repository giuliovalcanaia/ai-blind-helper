import asyncio

class AudioController:
    
    def __init__(self, audio_app):
        self.audio_app = audio_app
    
    def handle_audio_pause_toggle(self):
        """Tecla (Ex: Espaço ou P): Pausa/Continua a resposta da IA"""
        if hasattr(self.audio_app, 'toggle_pause'):
            self.audio_app.toggle_pause()

    def handle_audio_rewind(self):
        """Tecla (Ex: Seta Esquerda): Volta 5 segundos"""
        if hasattr(self.audio_app, 'rewind'):
            self.audio_app.rewind(seconds=5)

    def handle_audio_forward(self):
        """Tecla (Ex: Seta Direita): Avança 5 segundos"""
        if hasattr(self.audio_app, 'forward'):
            self.audio_app.forward(seconds=5)
            
    