from datetime import datetime
import os

class SystemMessageApplication:
    def __init__(self, language, base_dir="audio"):
        print(f"[SystemMessageApplication __init__] Initializing system message service (Language: {language})")
        self.language = language
        self.base_dir = base_dir

    def get_current_welcome_message_path(self):
        print("[SystemMessageApplication get_current_welcome_message_path] Determining greeting based on current time")
        now = datetime.now()
        hour = now.hour

        if hour in range(2, 12):
            filename = "power-on-good-morning.wav"
        elif hour in range(13, 18):
            filename = "power-on-good-afternoon.wav"
        else:
            filename = "power-on-good-evening.wav"

        full_path = os.path.join(
            self.base_dir,
            self.language,
            "system",
            filename
        )

        if os.path.exists(full_path):
            print(f"[SystemMessageApplication get_current_welcome_message_path] Greeting file found: {full_path}")
            return full_path
        else:
            print(f"[SystemMessageApplication get_current_welcome_message_path] Error: File not found at {full_path}")
            return None

    def set_language(self, language):
        """Allows changing the language dynamically"""
        self.language = language

        
    def get_closing_gemini(self):
        return self.get_full_path("closing-gemini.wav")

    def get_initiating_gemini(self):
        return self.get_full_path("initiating-gemini.wav")

        
    def get_closing_gemini_video(self):
        return self.get_full_path("closing-gemini-video.wav")

    def get_initiating_gemini_video(self):
        return self.get_full_path("initiating-gemini-video.wav")
        
        
    def get_full_path(self, path):
        full_path = os.path.join(
            self.base_dir,
            self.language,
            "system",
            path
        )

        # Check that the file actually exists before returning
        if os.path.exists(full_path):
            print(full_path)
            return full_path
        else:
            print(f"[SystemMessageApp] File not found: {full_path}")
            return None
