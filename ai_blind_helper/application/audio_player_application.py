import asyncio
from manager import InputAudioManager
from reader import WavReader
from config import Config
import time

class AudioPlayerApplication:
    def __init__(self):
        self.audio_service = InputAudioManager()
        self.wav_reader = WavReader(
            target_rate=Config.RECEIVE_SAMPLE_RATE,
            target_channels=Config.CHANNELS
        )

    async def task_capture_audio(self, out_queue: asyncio.Queue, control_event: asyncio.Event):
        """
        Lê do Mic e joga na fila. 
        Pausa lógica sem fechar hardware, com limpeza de buffer ao retomar.
        """
        self.audio_service.start_input_stream()
        print(f"DEBUG: Task Event ID: {id(control_event)}") 
        print(" -> [AudioApp] Microfone Iniciado (Hardware ON).")
        
        chunk_size = 1024 # Ou o valor que você usa no config
        
        try:
            while True:
                # 1. VERIFICAÇÃO DE PAUSA
                if not control_event.is_set():
                    print("🔴 [Audio] Pausado (Aguardando)...")
                    await control_event.wait()
                    print("🟢 [Audio] Retomando capturas...")

                    # --- 2. LIMPEZA DE BUFFER (O SEGREDO) ---
                    # Ao acordar, o buffer do OS está cheio de áudio "velho" (do tempo que ficou pausado).
                    # Precisamos ler tudo e jogar fora para ficar "Live" novamente.
                    try:
                        # Tenta rodar em thread para não travar o loop principal enquanto limpa
                        await asyncio.to_thread(self._flush_input_buffer)
                    except Exception as e:
                        print(f"⚠️ [Audio] Aviso ao limpar buffer: {e}")

                # 3. LEITURA REAL
                data = await asyncio.to_thread(self.audio_service.read_chunk)
                
                # Envia
                await out_queue.put({"data": data, "mime_type": "audio/pcm"})

        except asyncio.CancelledError:
            print(" -> [AudioApp] Tarefa cancelada.")

    def _flush_input_buffer(self):
        """Lê todos os dados disponíveis no buffer e descarta."""
        # Esta implementação depende da biblioteca que você usa (PyAudio vs SoundDevice).
        # Exemplo genérico para PyAudio:
        try:
            # Verifica quantos frames tem parados no buffer
            available = self.audio_service.input_stream.get_read_available()
            if available > 0:
                # Lê e joga no lixo
                self.audio_service.input_stream.read(available, exception_on_overflow=False)
                print(f"🧹 [Audio] Buffer limpo: {available} frames descartados.")
        except AttributeError:
            # Se sua classe audio_service não expõe o stream diretamente, 
            # você pode apenas ler alguns chunks num loop rápido:
            for _ in range(5): 
                self.audio_service.read_chunk()
        except Exception as e:
            pass

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