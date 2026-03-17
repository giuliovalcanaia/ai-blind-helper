import asyncio
from event import EventBus

class AudioController:
    
    def __init__(self, audio_app, event_bus: EventBus):
        print(f"[AudioController __init__] Inicializando controlador com audio_app: {audio_app}")
        self.audio_app = audio_app
    
    def handle_audio_pause_toggle(self):
        print("[AudioController handle_audio_pause_toggle] Tentando alternar pausa do áudio")
        if hasattr(self.audio_app, 'toggle_pause'):
            self.audio_app.toggle_pause()
            print("[AudioController handle_audio_pause_toggle] Comando toggle_pause executado")

    def handle_audio_rewind(self):
        print("[AudioController handle_audio_rewind] Solicitando retrocesso de 5 segundos")
        if hasattr(self.audio_app, 'rewind'):
            self.audio_app.rewind(seconds=5)
            print("[AudioController handle_audio_rewind] Retrocesso de 5 segundos concluído")

    def handle_audio_forward(self):
        print("[AudioController handle_audio_forward] Solicitando avanço de 5 segundos")
        if hasattr(self.audio_app, 'forward'):
            self.audio_app.forward(seconds=5)
            print("[AudioController handle_audio_forward] Avanço de 5 segundos concluído")