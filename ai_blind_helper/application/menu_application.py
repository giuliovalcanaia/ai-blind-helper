import os
from config import Config

class MenuApplication:
    def __init__(self, base_dir="audio"):
        
        self.base_dir = base_dir
        
    @property
    def language(self):
        return Config.LANGUAGE

    def _get_menu_audio_path(self, filename):
        full_path = os.path.join(
            self.base_dir,
            self.language,
            "menu",
            filename
        )

        if os.path.exists(full_path):
            return full_path
        else:
            print(f"[MenuApplication] File not found: {full_path}")
            return None

    def get_change_language_audio_path(self):
        return self._get_menu_audio_path("change-language.wav")

    def get_describe_audio_path(self):
        return self._get_menu_audio_path("describe.wav")

    def get_transcribe_audio_path(self):
        return self._get_menu_audio_path("transcribe.wav")

    def get_websocket_audio_path(self):
        return self._get_menu_audio_path("gemini-audio-mode.wav")

    def get_websocket_video_path(self):
        return self._get_menu_audio_path("gemini-video-mode.wav")

    def set_language(self, language):
        self.language = language

    def get_language_changed_path(self):
        return self._get_menu_audio_path("language-changed.wav")