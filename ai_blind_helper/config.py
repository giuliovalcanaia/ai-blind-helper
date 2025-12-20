import os
import pyaudio
import json
from google.genai import types

# Define o nome do ficheiro de persistência
SETTINGS_FILE = "settings.json"


def load_persistent_settings():
    """Carrega as definições do ficheiro JSON."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[Config] Erro ao ler settings: {e}")
    return {}


def save_persistent_setting(key, value):
    """Guarda uma definição específica no JSON."""
    settings = load_persistent_settings()
    settings[key] = value
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"[Config] Erro ao guardar settings: {e}")


# Carrega as definições antes de criar a classe
_initial_settings = load_persistent_settings()


class Config:
    """Configurações globais."""
    # Defina sua API KEY aqui ou garanta que está nas variáveis de ambiente
    API_KEY = os.getenv(
        "GOOGLE_API_KEY", "AIzaSyCgcpCz46tJvT0RneuhTZvlOAXGGqAGDiI")

    API_VERSION_TEXT_API_GEMINI_3 = 'v1alpha'

    MODEL = "models/gemini-2.5-flash-native-audio-preview-12-2025"
    MODEL_TEXT = "models"

    MODEL_TEXT_GENERATOR = "gemini-3-pro-preview"

    # LINGUAGEM

    # Define o nome do ficheiro de persistência
    SETTINGS_FILE = "settings.json"

    LANGUAGES = ['pt', 'en']
    LANGUAGE = _initial_settings.get("language", "pt")

    @staticmethod
    def set_language(new_lang):
        """Atualiza a variável em memória e persiste no ficheiro."""
        Config.LANGUAGE = new_lang
        save_persistent_setting("language", new_lang)

    # Config do Noise Gate
    NOISE_GATE_THRESHOLD = 150
    NOISE_GATE_RELEASE_TIME = 0.5

    VIDEO_MODE = "camera"

    # Audio Settings
    AUDIO_FORMAT = pyaudio.paInt16
    CHANNELS = 1
    SEND_SAMPLE_RATE = 16000
    RECEIVE_SAMPLE_RATE = 24000
    CHUNK_SIZE = 1024
    LOCK_THRESHOLD_MS_AUDIO = 500
    LOCK_THRESHOLD_MS_VIDEO = 500
    LOCK_THRESHOLD_MS_DATE = 500

    # Keyboard Settings (ls -l /dev/input/by-id/)
    # For arch: sudo evtest
    # Adicionar entradas e saidas ao usuário comum: sudo usermod -a -G input,audio,video giulio
    # KEYBOARD_PATH = '/dev/input/event4'
    # Keyboard Settings (ls -l /dev/input/by-path/)
    KEYBOARD_PATH = '/dev/input/by-path/platform-i8042-serio-0-event-kbd'

    # Gemini Config
    LIVE_CONFIG = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        media_resolution="MEDIA_RESOLUTION_MEDIUM",
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name="Zephyr")
            )
        ),
        context_window_compression=types.ContextWindowCompressionConfig(
            trigger_tokens=25600,
            sliding_window=types.SlidingWindow(target_tokens=12800),
        ),
    )
