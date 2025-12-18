from datetime import datetime
import os

class SystemMessageApplication:
    def __init__(self, language, base_dir="audio"):
        """
        Inicializa o serviço de relógio.
        :param language: 'pt' ou 'en'
        :param base_dir: Diretório raiz onde os áudios estão (padrão: 'audio')
        """
        self.language = language
        self.base_dir = base_dir

    def get_current_welcome_message_path(self):
        """
        Retorna o caminho time_audio_absoluto do arquivo de áudio correspondente à hora atual.
        Retorna None se o arquivo não for encontrado.
        """
        now = datetime.now()

        hour = now.hour

        if hour in range(2, 12):
            filename = "power-on-good-morning.wav"
        elif hour in range(13, 18):
            filename = "power-on-good-afternoon.wav"
        else:
            filename = "power-on-good-night.wav"

        # Monta o caminho completo independente do sistema operacional
        # Ex: audio/pt/clock/22h-04.wav
        full_path = os.path.join(
            self.base_dir,
            self.language,
            "system",
            filename
        )

        # Verifica se o arquivo realmente existe antes de retornar
        if os.path.exists(full_path):
            print(full_path)
            return full_path
        else:
            print(f"[SystemMessageApp] Arquivo não encontrado: {full_path}")
            return None

    def set_language(self, language):
        """Permite trocar o idioma dinamicamente"""
        self.language = language