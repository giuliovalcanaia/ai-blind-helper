from reader import StreamerReader, WavReader
from config import Config

class ReaderProvider:
    def __init__(self):
        self.streamer = StreamerReader()
        self.wav = WavReader(target_rate=Config.RECEIVE_SAMPLE_RATE, target_channels=Config.CHANNELS)