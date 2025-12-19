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
        """
        Lê do Mic e envia diretamente para a fila da IA.
        Lógica de gravação em disco (debug) foi removida.
        """
        self.audio_input_manager.start_input_stream()
        print(f"[{self.__class__.__name__} task_capture_audio] Microfone iniciado.")

        try:
            while True:
                # 1. PAUSA / RESUME
                if not control_event.is_set():
                    print(f"[{self.__class__.__name__} task_capture_audio] Loop pausado. Aguardando evento...")
                    await control_event.wait()
                    print(f"[{self.__class__.__name__} task_capture_audio] Loop retomado.")
                    
                    try:
                        await asyncio.to_thread(self._flush_input_buffer)
                    except Exception as e:
                        print(f"[{self.__class__.__name__} task_capture_audio] Erro ao limpar buffer: {e}")

                # 2. LEITURA DO HARDWARE
                data = await asyncio.to_thread(self.audio_input_manager.read_chunk)

                if data:
                    # Envia para a IA
                    await out_queue.put({"data": data, "mime_type": "audio/pcm"})

        except asyncio.CancelledError:
            print(f"[{self.__class__.__name__} task_capture_audio] Tarefa cancelada.")
        except Exception as e:
            print(f"[{self.__class__.__name__} task_capture_audio] Erro fatal: {e}")

    def _flush_input_buffer(self):
        """Limpeza de buffer ao retomar pause"""
        try:
            available = self.audio_input_manager.input_stream.get_read_available()
            if available > 0:
                self.audio_input_manager.input_stream.read(
                    available, exception_on_overflow=False)
                print(f"[{self.__class__.__name__} _flush_input_buffer] Buffer limpo com sucesso ({available} frames descartados).")
        except Exception as e:
            print(f"[{self.__class__.__name__} _flush_input_buffer] Falha ao limpar buffer: {e}")

    async def task_play_audio(self, input_queue: asyncio.Queue):
        self.audio_output_manager.start_output_stream()
        print(f"[{self.__class__.__name__} task_play_audio] Stream de saída iniciado.")
        
        try:
            while True:
                bytestream = await input_queue.get()
                await asyncio.to_thread(self.audio_output_manager.write_chunk, bytestream)
                input_queue.task_done()
        except asyncio.CancelledError:
             print(f"[{self.__class__.__name__} task_play_audio] Tarefa cancelada.")

    async def play_file(self, file_path: str, target_queue: asyncio.Queue, loop):
        """Lê um arquivo WAV e injeta os chunks na fila de áudio para ser tocado"""
        print(f"[{self.__class__.__name__} play_file] Iniciando reprodução do arquivo: {file_path}")
        
        def process_file():
            # Lê o arquivo e joga na fila usando threadsafe pois roda em thread
            for chunk in self.wav_reader.read_chunks(file_path):
                loop.call_soon_threadsafe(
                    target_queue.put_nowait, chunk)
                    
        await asyncio.to_thread(process_file)
        print(f"[{self.__class__.__name__} play_file] Arquivo processado e enviado para a fila.")

    def close(self):
        print(f"[{self.__class__.__name__} close] Encerrando gerenciadores de áudio.")
        self.audio_input_manager.close()
        self.audio_output_manager.close()