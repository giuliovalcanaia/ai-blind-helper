import asyncio
from manager import InputAudioManager
from reader import WavReader
from config import Config

class AudioPlayerApplication:
    def __init__(self):
        self.audio_service = InputAudioManager()
        self.wav_reader = WavReader(
            target_rate=Config.RECEIVE_SAMPLE_RATE,
            target_channels=Config.CHANNELS
        )

    async def task_capture_audio(self, out_queue: asyncio.Queue):
        """Lê do Mic e joga na fila de saída (para o Gemini)"""
        self.audio_service.start_input_stream()
        print(" -> [AudioApp] Microfone Iniciado.")
        try:
            while True:
                # Executa operação bloqueante em thread separada
                data = await asyncio.to_thread(self.audio_service.read_chunk)
                await out_queue.put({"data": data, "mime_type": "audio/pcm"})
        finally:
            # ISSO É CRUCIAL:
            self.audio_service.closeInputs()

    async def task_play_audio(self, input_queue: asyncio.Queue):
        """Lê da fila de entrada (do Gemini ou Relógio) e toca no Speaker"""
        print(" -> [AudioApp] Speaker Ativo.")
        self.audio_service.start_output_stream()
        try:
            while True:
                bytestream = await input_queue.get()
                await asyncio.to_thread(self.audio_service.write_chunk, bytestream)
                input_queue.task_done()
        except asyncio.CancelledError:
            pass

    async def play_file(self, file_path: str, target_queue: asyncio.Queue, loop):
        """Lê um arquivo WAV e injeta os chunks na fila de áudio para ser tocado"""
        def process_file():
            # Lê o arquivo e joga na fila usando threadsafe pois roda em thread
            for chunk in self.wav_reader.read_chunks(file_path):
                loop.call_soon_threadsafe(
                    target_queue.put_nowait, chunk)
        
        await asyncio.to_thread(process_file)

    def close(self):
        self.audio_service.close()