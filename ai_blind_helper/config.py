import pyaudio
import os

FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024
MODEL = "models/gemini-2.5-flash-native-audio-preview-09-2025"

# Fallback para evitar erros se a ENV não estiver setada
API_KEY = os.getenv("GOOGLE_API_KEY")