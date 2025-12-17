import pyaudio
from config import Config

class OutputAudioManager:
    def __init__(self):
        self.pya = pyaudio.PyAudio()
        self.output_stream = None

    def start_output_stream(self):
        self.output_stream = self.pya.open(
            format=Config.AUDIO_FORMAT,
            channels=Config.CHANNELS,
            rate=Config.RECEIVE_SAMPLE_RATE,
            output=True,
        )

    def write_chunk(self, data):
        """
        Escreve os bytes de áudio no stream de saída (alto-falantes).
        """
        if self.output_stream:
            self.output_stream.write(data)

    def close(self):
        if self.output_stream:
            self.output_stream.stop_stream()
            self.output_stream.close()
        self.pya.terminate()