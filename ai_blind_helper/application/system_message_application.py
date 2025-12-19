from datetime import datetime
import os

class SystemMessageApplication:
    def __init__(self, language, base_dir="audio"):
        print(f"[SystemMessageApplication __init__] Inicializando serviço de mensagens do sistema (Idioma: {language})")
        self.language = language
        self.base_dir = base_dir

    def get_current_welcome_message_path(self):
        print("[SystemMessageApplication get_current_welcome_message_path] Determinando saudação baseada no horário atual")
        now = datetime.now()
        hour = now.hour

        if hour in range(2, 12):
            filename = "power-on-good-morning.wav"
        elif hour in range(13, 18):
            filename = "power-on-good-afternoon.wav"
        else:
            filename = "power-on-good-night.wav"

        full_path = os.path.join(
            self.base_dir,
            self.language,
            "system",
            filename
        )

        if os.path.exists(full_path):
            print(f"[SystemMessageApplication get_current_welcome_message_path] Arquivo de saudação encontrado: {full_path}")
            return full_path
        else:
            print(f"[SystemMessageApplication get_current_welcome_message_path] Erro: Arquivo não encontrado em {full_path}")
            return None

    def set_language(self, language):
        print(f"[SystemMessageApplication set_language] Alterando idioma das mensagens do sistema para: {language}")
        self.language = language