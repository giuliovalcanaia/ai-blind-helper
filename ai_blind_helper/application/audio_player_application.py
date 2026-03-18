import asyncio
from manager import InputAudioManager, OutputAudioManager
from reader import WavReader
from config import Config

class AudioPlayerApplication:
    def __init__(self, input_manager, output_manager, wav_reader):
        self.audio_input_manager = input_manager
        self.audio_output_manager = output_manager
        self.wav_reader = wav_reader

    async def task_capture_audio(self, out_queue: asyncio.Queue, control_event: asyncio.Event):
        self.audio_input_manager.start_input_stream()
        print(f"[{self.__class__.__name__} task_capture_audio] Microphone started (Low Latency Mode).")

        try:
            while True:
                if not control_event.is_set():
                    await control_event.wait()
                    await asyncio.to_thread(self._flush_input_buffer)
                
                try:
                    data = await asyncio.to_thread(self.audio_input_manager.read_chunk)
                except Exception as e:
                    continue

                if data:
                    try:
                        out_queue.put_nowait({"data": data, "mime_type": "audio/pcm"})
                    except asyncio.QueueFull:
                        pass # Intentional drop frame to keep sync

        except asyncio.CancelledError:
            print(f"[{self.__class__.__name__} task_capture_audio] Task cancelled.")
        except Exception as e:
            print(f"[{self.__class__.__name__} task_capture_audio] Fatal error: {e}")

    def _flush_input_buffer(self):
        try:
            if hasattr(self.audio_input_manager, 'input_stream'):
                available = self.audio_input_manager.input_stream.get_read_available()
                if available > 0:
                    self.audio_input_manager.input_stream.read(available, exception_on_overflow=False)
        except Exception:
            pass

    async def task_play_audio(self, input_queue: asyncio.Queue):
        
        self.audio_output_manager.start_output_stream()
        print(f"[{self.__class__.__name__} task_play_audio] Output stream started.")
        
        try:
            while True:
                bytestream = await input_queue.get()
                
                await asyncio.to_thread(self.audio_output_manager.write_chunk, bytestream)
                
                input_queue.task_done()
        except asyncio.CancelledError:
             print(f"[{self.__class__.__name__} task_play_audio] Task cancelled.")

    def drain_audio_queue(self, queue: asyncio.Queue):
        items_dropped = 0
        while not queue.empty():
            try:
                queue.get_nowait()
                queue.task_done()
                items_dropped += 1
            except (asyncio.QueueEmpty, ValueError):
                break
        
        if items_dropped > 0:
            print(f"[{self.__class__.__name__}] Drain: {items_dropped} audio chunks dropped.")

    async def play_file(self, file_path: str, target_queue: asyncio.Queue, loop):
        print(f"[{self.__class__.__name__} play_file] Playing: {file_path}")
        def process_file():
            for chunk in self.wav_reader.read_chunks(file_path):
                loop.call_soon_threadsafe(target_queue.put_nowait, chunk)
        await asyncio.to_thread(process_file)

    def close(self):
        print(f"[{self.__class__.__name__} close] Closing managers.")
        self.audio_input_manager.close()
        self.audio_output_manager.close()