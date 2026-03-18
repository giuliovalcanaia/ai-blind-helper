import os
from datetime import datetime

class ClockApplication:
    def __init__(self, language, base_dir="audio"):
        print(f"[ClockApplication __init__] Initializing clock service (Language: {language})")
        self.language = language
        self.base_dir = base_dir

    def get_current_time_audio_path(self):
        print("[ClockApplication get_current_time_audio_path] Calculating current time for audio lookup")
        now = datetime.now()

        hour = now.strftime("%H")
        minute = now.strftime("%M")

        filename = f"{hour}h-{minute}.wav"

        full_path = os.path.join(
            self.base_dir,
            self.language,
            "clock",
            filename
        )

        if os.path.exists(full_path):
            print(f"[ClockApplication get_current_time_audio_path] File found: {full_path}")
            return full_path
        else:
            print(f"[ClockApplication get_current_time_audio_path] Error: File not found at {full_path}")
            return None

    def set_language(self, language):
        print(f"[ClockApplication set_language] Changing clock language to: {language}")
        self.language = language