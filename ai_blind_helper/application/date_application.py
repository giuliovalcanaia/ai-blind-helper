import os
from datetime import datetime


class DateApplication:
    def __init__(self, language="pt", base_dir="audio"):
        self.language = language
        self.base_dir = base_dir

    def get_current_date_audio_paths(self):
        """
        Retorna uma LISTA de caminhos: [caminho_semana, caminho_data].
        Exemplo: ['.../week-1.wav', '.../29-12.wav']
        """
        now = datetime.now()
        paths_to_play = []

        # --- 1. Lógica do Dia da Semana ---
        wd_index = now.weekday()

        # Mapeamento para o nome do SEU arquivo.
        weekday_map = {
            0: "week-1",  # Domingo
            1: "week-2",  # Segunda
            2: "week-3",  # Terça
            3: "week-4",  # Quarta
            4: "week-5",  # Quinta
            5: "week-6",  # Sexta
            6: "week-7",  # Sábado
        }

        filename_week = f"{weekday_map.get(wd_index, 'week-0')}.wav"

        path_week = os.path.join(
            self.base_dir, self.language, "date", filename_week)

        if os.path.exists(path_week):
            paths_to_play.append(path_week)
        else:
            print(f"[DateService] Arquivo de semana não encontrado: {
                  path_week}")

        # --- 2. Lógica do Dia/Mês ---
        day = now.strftime("%d")
        month = now.strftime("%m")
        filename_date = f"{day}-{month}.wav"

        path_date = os.path.join(
            self.base_dir, self.language, "date", filename_date)

        if os.path.exists(path_date):
            paths_to_play.append(path_date)
        else:
            print(f"[DateService] Arquivo de data não encontrado: {path_date}")

        return paths_to_play  # Retorna lista, mesmo que vazia ou parcial

    def set_language(self, language):
        self.language = language
