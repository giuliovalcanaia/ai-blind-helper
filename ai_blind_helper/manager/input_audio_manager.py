import pyaudio
import numpy as np
from config import Config

class InputAudioManager:
    def __init__(self):
        print("[InputAudioManager __init__] Initializing input audio manager (Hardware)")
        self.pya = pyaudio.PyAudio()
        self.input_stream = None
        
        self.threshold = Config.NOISE_GATE_THRESHOLD
        self.release_time = Config.NOISE_GATE_RELEASE_TIME
        
        self.gate_open = False
        self.release_counter = 0
        
        if hasattr(Config, 'SEND_SAMPLE_RATE') and hasattr(Config, 'CHUNK_SIZE'):
            self.chunks_release = int(Config.SEND_SAMPLE_RATE / Config.CHUNK_SIZE * self.release_time)
        else:
            self.chunks_release = int(44100 / 1024 * self.release_time)
        
        print(f"[InputAudioManager __init__] Noise Gate configured (Threshold: {self.threshold}, Release: {self.release_time}s)")

    def start_input_stream(self):
        print("[InputAudioManager start_input_stream] Locating default device and opening input stream")
        try:
            mic_info = self.pya.get_default_input_device_info()
            self.input_stream = self.pya.open(
                format=Config.AUDIO_FORMAT,
                channels=Config.CHANNELS,
                rate=Config.SEND_SAMPLE_RATE,
                input=True,
                input_device_index=mic_info["index"],
                frames_per_buffer=Config.CHUNK_SIZE,
            )
            print(f"[InputAudioManager start_input_stream] Microphone activated: {mic_info['name']}")
        except Exception as e:
            print(f"[InputAudioManager start_input_stream] Error opening input stream: {e}")

    def read_chunk(self):
        if not self.input_stream:
            return b''

        try:
            raw_data = self.input_stream.read(Config.CHUNK_SIZE, exception_on_overflow=False)
        except OSError as e:
            print(f"[InputAudioManager read_chunk] Read error (Hardware): {e}")

        audio_data = np.frombuffer(raw_data, dtype=np.int16)

        if len(audio_data) == 0:
            return raw_data

        rms = int(np.sqrt(np.mean(audio_data.astype(np.int64)**2)))

        if rms > self.threshold:
            if not self.gate_open:
                print(f"[InputAudioManager read_chunk] Gate OPEN (RMS: {rms})")
            self.gate_open = True
            self.release_counter = 0
            return raw_data
        
        elif self.gate_open:
            self.release_counter += 1
            if self.release_counter > self.chunks_release:
                self.gate_open = False
                print("[InputAudioManager read_chunk] Gate CLOSED due to inactivity")
            return raw_data
        
        else:
            return b'\x00' * len(raw_data)

    def close(self):
        print("[InputAudioManager close] Closing audio resources")
        if self.input_stream:
            try:
                self.input_stream.stop_stream()
                self.input_stream.close()
                print("[InputAudioManager close] Input stream closed")
            except Exception as e:
                print(f"[InputAudioManager close] Error closing stream: {e}")
        self.pya.terminate()
        print("[InputAudioManager close] PyAudio terminated")