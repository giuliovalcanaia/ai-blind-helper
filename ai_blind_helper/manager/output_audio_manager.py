import pyaudio
from config import Config

class OutputAudioManager:
    def __init__(self):
        print("[OutputAudioManager __init__] Initializing output audio manager (Hardware)")
        self.pya = pyaudio.PyAudio()
        self.output_stream = None

    def start_output_stream(self):
        print("[OutputAudioManager start_output_stream] Opening output stream for speakers")
        try:
            self.output_stream = self.pya.open(
                format=Config.AUDIO_FORMAT,
                channels=Config.CHANNELS,
                rate=Config.RECEIVE_SAMPLE_RATE,
                output=True,
            )
            print(f"[OutputAudioManager start_output_stream] Audio output enabled ({Config.RECEIVE_SAMPLE_RATE} Hz)")
        except Exception as e:
            print(f"[OutputAudioManager start_output_stream] Error opening output stream: {e}")

    def write_chunk(self, data):
        if self.output_stream:
            try:
                self.output_stream.write(data)
            except Exception as e:
                print(f"[OutputAudioManager write_chunk] Error writing to audio hardware: {e}")

    def close(self):
        print("[OutputAudioManager close] Closing output audio hardware")
        if self.output_stream:
            try:
                self.output_stream.stop_stream()
                self.output_stream.close()
                print("[OutputAudioManager close] Output stream closed")
            except Exception as e:
                print(f"[OutputAudioManager close] Error closing stream: {e}")
        self.pya.terminate()
        print("[OutputAudioManager close] PyAudio terminated")