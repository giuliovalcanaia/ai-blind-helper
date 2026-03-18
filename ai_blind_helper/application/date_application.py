import os
from datetime import datetime

class DateApplication:
    def __init__(self, language, base_dir="audio"):
        print(f"[DateApplication __init__] Initializing date service (Language: {language})")
        self.language = language
        self.base_dir = base_dir

    def get_current_date_audio_paths(self):
        print("[DateApplication get_current_date_audio_paths] Calculating current date for audio lookup")
        now = datetime.now()
        paths_to_play = []

        wd_index = now.weekday()

        weekday_map = {
            0: "week-1",
            1: "week-2",
            2: "week-3",
            3: "week-4",
            4: "week-5",
            5: "week-6",
            6: "week-7",
        }

        filename_week = f"{weekday_map.get(wd_index, 'week-0')}.wav"
        path_week = os.path.join(self.base_dir, self.language, "date", filename_week)

        if os.path.exists(path_week):
            print(f"[DateApplication get_current_date_audio_paths] Week audio found: {path_week}")
            paths_to_play.append(path_week)
        else:
            print(f"[DateApplication get_current_date_audio_paths] Error: Week file not found at {path_week}")

        day = now.strftime("%d")
        month = now.strftime("%m")
        filename_date = f"{day}-{month}.wav"

        path_date = os.path.join(self.base_dir, self.language, "date", filename_date)

        if os.path.exists(path_date):
            print(f"[DateApplication get_current_date_audio_paths] Date audio found: {path_date}")
            paths_to_play.append(path_date)
        else:
            print(f"[DateApplication get_current_date_audio_paths] Error: Date file not found at {path_date}")

        return paths_to_play

    def set_language(self, language):
        print(f"[DateApplication set_language] Changing date language to: {language}")
        self.language = language