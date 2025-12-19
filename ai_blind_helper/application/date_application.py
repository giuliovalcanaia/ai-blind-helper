import os
from datetime import datetime

class DateApplication:
    def __init__(self, language, base_dir="audio"):
        print(f"[DateApplication __init__] Inicializando serviço de data (Idioma: {language})")
        self.language = language
        self.base_dir = base_dir

    def get_current_date_audio_paths(self):
        print("[DateApplication get_current_date_audio_paths] Calculando data atual para busca de áudios")
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
            print(f"[DateApplication get_current_date_audio_paths] Áudio da semana encontrado: {path_week}")
            paths_to_play.append(path_week)
        else:
            print(f"[DateApplication get_current_date_audio_paths] Erro: Arquivo de semana não encontrado em {path_week}")

        day = now.strftime("%d")
        month = now.strftime("%m")
        filename_date = f"{day}-{month}.wav"

        path_date = os.path.join(self.base_dir, self.language, "date", filename_date)

        if os.path.exists(path_date):
            print(f"[DateApplication get_current_date_audio_paths] Áudio do dia encontrado: {path_date}")
            paths_to_play.append(path_date)
        else:
            print(f"[DateApplication get_current_date_audio_paths] Erro: Arquivo de data não encontrado em {path_date}")

        return paths_to_play

    def set_language(self, language):
        print(f"[DateApplication set_language] Alterando idioma da data para: {language}")
        self.language = language