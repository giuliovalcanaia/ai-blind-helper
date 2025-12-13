import os
from datetime import datetime


class ClockApplication:
    def __init__(self, language="pt", base_dir="audio"):
        """
        Inicializa o serviço de relógio.
        :param language: 'pt' ou 'en'
        :param base_dir: Diretório raiz onde os áudios estão (padrão: 'audio')
        """
        self.language = language
        self.base_dir = base_dir

    def get_current_time_audio_path(self):
        """
        Retorna o caminho absoluto do arquivo de áudio correspondente à hora atual.
        Retorna None se o arquivo não for encontrado.
        """
        now = datetime.now()

        # Formata a hora e minuto (ex: 22 e 04)
        # %H = Hora 00-23
        # %M = Minuto 00-59
        hour = now.strftime("%H")
        minute = now.strftime("%M")

        # Monta o nome do arquivo: "22h-04.wav"
        filename = f"{hour}h-{minute}.wav"

        # Monta o caminho completo independente do sistema operacional
        # Ex: audio/pt/clock/22h-04.wav
        full_path = os.path.join(
            self.base_dir,
            self.language,
            "clock",
            filename
        )

        # Verifica se o arquivo realmente existe antes de retornar
        if os.path.exists(full_path):
            return full_path
        else:
            print(f"[ClockService] Arquivo não encontrado: {full_path}")
            return None

    def set_language(self, language):
        """Permite trocar o idioma dinamicamente"""
        self.language = language
