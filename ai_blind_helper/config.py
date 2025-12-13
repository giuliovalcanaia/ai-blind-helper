import os
import pyaudio
from google.genai import types


class Config:
    """Configurações globais."""
    # Defina sua API KEY aqui ou garanta que está nas variáveis de ambiente
    API_KEY = os.getenv(
        "GOOGLE_API_KEY", "AIzaSyCgcpCz46tJvT0RneuhTZvlOAXGGqAGDiI")

    MODEL = "models/gemini-2.5-flash-native-audio-preview-09-2025"

    # Audio Settings
    AUDIO_FORMAT = pyaudio.paInt16
    CHANNELS = 1
    SEND_SAMPLE_RATE = 16000
    RECEIVE_SAMPLE_RATE = 24000
    CHUNK_SIZE = 1024
    LOCK_THRESHOLD_MS_AUDIO = 500
    LOCK_THRESHOLD_MS_VIDEO = 500

    # Keyboard Settings
    KEYBOARD_PATH = '/dev/input/event6'
    
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
