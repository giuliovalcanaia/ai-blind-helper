import os
from datetime import datetime

class DateApplication:
    def __init__(self, language="pt", base_dir="audio"):
        """
        Inicializa o serviço de data/calendário.
        :param language: 'pt' ou 'en'
        :param base_dir: Diretório raiz onde os áudios estão (padrão: 'audio')
        """
        self.language = language
        self.base_dir = base_dir

    def get_current_date_audio_path(self):
        """
        Retorna o caminho absoluto do arquivo de áudio correspondente à data atual.
        Retorna None se o arquivo não for encontrado.
        Formato esperado do arquivo: dd-mm.wav (ex: 13-12.wav)
        """
        now = datetime.now()

        # Formata dia e mês
        # %d = Dia do mês 01-31
        # %m = Mês 01-12
        day = now.strftime("%d")
        month = now.strftime("%m")

        # Monta o nome do arquivo: "13-12.wav"
        filename = f"{day}-{month}.wav"

        # Monta o caminho completo independente do sistema operacional
        # Ex: audio/pt/date/13-12.wav
        # Note que alterei a pasta de "clock" para "date" para manter organizado
        full_path = os.path.join(
            self.base_dir,
            self.language,
            "date", 
            filename
        )

        # Verifica se o arquivo realmente existe antes de retornar
        if os.path.exists(full_path):
            return full_path
        else:
            print(f"[DateService] Arquivo não encontrado: {full_path}")
            return None

    def set_language(self, language):
        """Permite trocar o idioma dinamicamente"""
        self.language = language