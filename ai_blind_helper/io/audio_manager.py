import pyaudio
import asyncio
from config import (MODEL, FORMAT, CHANNELS, SEND_SAMPLE_RATE, RECEIVE_SAMPLE_RATE, CHUNK_SIZE)

class AudioHardwareManager:
    def __init__(self):
        self.pya = pyaudio.PyAudio()
        self.input_stream = None
        self.output_stream = None

    async def start_input_stream(self):
        mic_info = self.pya.get_default_input_device_info()
        self.input_stream = await asyncio.to_thread(
            self.pya.open,
            format=config.FORMAT,
            channels=CHANNELS,
            rate=SEND_SAMPLE_RATE,
            input=True,
            input_device_index=mic_info["index"],
            frames_per_buffer=CHUNK_SIZE,
        )

    async def start_output_stream(self):
        self.output_stream = await asyncio.to_thread(
            self.pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
        )

    async def read_chunk(self):
        if not self.input_stream:
            return None
        kwargs = {"exception_on_overflow": False} if __debug__ else {}
        return await asyncio.to_thread(self.input_stream.read, CHUNK_SIZE, **kwargs)

    async def write_chunk(self, data):
        if self.output_stream:
            await asyncio.to_thread(self.output_stream.write, data)

    def close(self):
        if self.input_stream: self.input_stream.close()
        if self.output_stream: self.output_stream.close()
        self.pya.terminate()