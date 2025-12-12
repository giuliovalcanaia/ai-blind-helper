import pyaudio
from config import Config


class AudioService:
    def __init__(self):
        self.pya = pyaudio.PyAudio()
        self.input_stream = None
        self.output_stream = None

    def start_input_stream(self):
        mic_info = self.pya.get_default_input_device_info()
        self.input_stream = self.pya.open(
            format=Config.AUDIO_FORMAT,
            channels=Config.CHANNELS,
            rate=Config.SEND_SAMPLE_RATE,
            input=True,
            input_device_index=mic_info["index"],
            frames_per_buffer=Config.CHUNK_SIZE,
        )

    def start_output_stream(self):
        self.output_stream = self.pya.open(
            format=Config.AUDIO_FORMAT,
            channels=Config.CHANNELS,
            rate=Config.RECEIVE_SAMPLE_RATE,
            output=True,
        )

    def read_chunk(self):
        return self.input_stream.read(Config.CHUNK_SIZE, exception_on_overflow=False)

    def write_chunk(self, data):
        if self.output_stream:
            self.output_stream.write(data)

    def close(self):
        if self.input_stream:
            self.input_stream.stop_stream()
            self.input_stream.close()
        if self.output_stream:
            self.output_stream.stop_stream()
            self.output_stream.close()
        self.pya.terminate()
