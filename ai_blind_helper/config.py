import os
import pyaudio
import json
from google.genai import types

SETTINGS_FILE = "settings.json"


def load_persistent_settings():
    """Loads settings from the JSON file."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[Config] Error reading settings: {e}")
    return {}


def save_persistent_setting(key, value):
    """Saves a specific setting to the JSON file."""
    settings = load_persistent_settings()
    settings[key] = value
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"[Config] Error saving settings: {e}")


_initial_settings = load_persistent_settings()


class Config:
    """Global configuration."""
    # Set your API KEY here or ensure it is available in environment variables
    API_KEY = os.getenv("GOOGLE_API_KEY")

    API_VERSION_TEXT_API_GEMINI_3 = 'v1alpha'

    MODEL = "models/gemini-2.5-flash-native-audio-preview-12-2025"
    MODEL_TEXT = "models"

    MODEL_TEXT_GENERATOR = "gemini-3-pro-preview"

    SETTINGS_FILE = "settings.json"

    LANGUAGES = ['pt', 'en']
    LANGUAGE = _initial_settings.get("language", "pt")

    @staticmethod
    def set_language(new_lang):
        """Updates the in-memory variable and persists it to the file."""
        Config.LANGUAGE = new_lang
        save_persistent_setting("language", new_lang)

    # Noise Gate config
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

    KEYBOARD_PATH = '/dev/input/event8'



    # TTS Config

    TTS_CONFIG =types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name='Zephyr',
                )
            )
        ),
    )

    TTS_MODEL = "gemini-2.5-flash-preview-tts"






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
