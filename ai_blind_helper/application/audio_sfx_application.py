import os

class AudioSFXApplication:
    def __init__(self, language="pt", base_dir="audio"):
        """
        Inicializa o serviço de relógio.
        :param language: 'pt' ou 'en'
        :param base_dir: Diretório raiz onde os áudios estão (padrão: 'audio')
        """
        self.language = language
        self.base_dir = base_dir
        
    def get_full_path(self, path):
        full_path = os.path.join(
            self.base_dir,
            "sfx",
            path
        )

        # Verifica se o arquivo realmente existe antes de retornar
        if os.path.exists(full_path):
            print(full_path)
            return full_path
        else:
            print(f"[SystemMessageApp] Arquivo não encontrado: {full_path}")
            return None
        
    def get_audio_button_press(self):
        return self.get_full_path("audio-button-press.wav")

    def get_audio_button_release(self):
        return self.get_full_path("audio-button-release.wav")    
   
    def get_close_websocket(self):
        return self.get_full_path("close-websocket.wav")
    
    def get_hold_button(self):
        return self.get_full_path("hold-button.wav")
    
    def get_open_websocket(self):
        return self.get_full_path("open-websocket.wav")
    
    def get_video_button_press(self):
        return self.get_full_path("video-button-press.wav")
    
    def get_video_button_release(self):
        return self.get_full_path("video-button-release.wav")