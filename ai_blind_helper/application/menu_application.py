import os

class MenuApplication:
    def __init__(self, language="pt", base_dir="audio"):
        """
        Inicializa o serviço de áudios do menu.
        :param language: 'pt' ou 'en'
        :param base_dir: Diretório raiz onde os áudios estão (padrão: 'audio')
        """
        self.language = language
        self.base_dir = base_dir

    def _get_menu_audio_path(self, filename):
        """
        Método auxiliar privado para construir o caminho e validar a existência.
        Caminho esperado: audio/{lang}/menu/{filename}
        """
        full_path = os.path.join(
            self.base_dir,
            self.language,
            "menu",
            filename
        )

        # Verifica se o arquivo realmente existe antes de retornar
        if os.path.exists(full_path):
            return full_path
        else:
            print(f"[MenuApplication] Arquivo não encontrado: {full_path}")
            return None

    def get_change_language_audio_path(self):
        """Retorna o caminho para o áudio de troca de idioma."""
        return self._get_menu_audio_path("change-language.wav")

    def get_describe_audio_path(self):
        """Retorna o caminho para o áudio da funcionalidade de descrição."""
        return self._get_menu_audio_path("describe.wav")

    def get_exit_audio_path(self):
        """Retorna o caminho para o áudio de saída/encerramento."""
        return self._get_menu_audio_path("exit.wav")

    def get_transcribe_audio_path(self):
        """Retorna o caminho para o áudio da funcionalidade de transcrição."""
        return self._get_menu_audio_path("transcribe.wav")

    def get_websocket_audio_path(self):
        """Retorna o caminho para o áudio relacionado ao status do websocket."""
        return self._get_menu_audio_path("websocket-audio.wav")

    def get_websocket_video_path(self):
        """Retorna o caminho para o vídeo relacionado ao status do websocket."""
        return self._get_menu_audio_path("websocket-video.wav")

    def set_language(self, language):
        """Permite trocar o idioma dinamicamente"""
        self.language = language