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
        Lê do Mic e joga na fila de saída.
        Pausa a leitura se control_event estiver false (clear), mas mantém mic aberto.
        """
        self.audio_service.start_input_stream()
        print(" -> [AudioApp] Microfone Iniciado (Hardware ON).")
        print(f"DEBUG: Task Event ID: {id(control_event)}")
        
        try:
            while True:

                if not control_event.is_set():
                    print("🔴 [Audio] Evento está FALSE. Vou parar e esperar...")
                # --- PONTO DE CONTROLE ---
                # Se o evento estiver .clear(), o código PARA aqui e aguarda.
                # O loop não consome CPU e não lê dados do buffer enquanto espera.
                await control_event.wait()
                
                # Se passar daqui, significa que o evento está True
                # Vamos imprimir apenas 1 vez a cada ~20 chunks para não floodar o terminal
                if int(time.time()) % 2 == 0: 
                    print("🟢 [Audio] Processando... (Fluxo liberado)", end="\r")

                # Executa operação bloqueante em thread separada
                data = await asyncio.to_thread(self.audio_service.read_chunk)
                
                # Envia para o Gemini
                await out_queue.put({"data": data, "mime_type": "audio/pcm"})

        except asyncio.CancelledError:
            print(" -> [AudioApp] Tarefa de captura cancelada.")
        finally:
            # Aqui sim, ao encerrar o app, fechamos o hardware
            # (assumindo que você tenha um método stop_stream no seu service)
            self.audio_service.close() 
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