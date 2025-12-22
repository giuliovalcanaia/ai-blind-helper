import asyncio
from manager import InputAudioManager, OutputAudioManager
from reader import WavReader
from config import Config

class AudioApplication:
    def __init__(self, input_manager, output_manager, wav_reader):
        self.audio_input_manager = input_manager
        self.audio_output_manager = output_manager
        self.wav_reader = wav_reader

    async def task_capture_audio(self, out_queue: asyncio.Queue, control_event: asyncio.Event):
        """
        Lê do Mic e envia para a fila da IA com proteção contra latência (Drop frame).
        """
        self.audio_input_manager.start_input_stream()
        print(f"[{self.__class__.__name__} task_capture_audio] Microfone iniciado (Modo Baixa Latência).")

        try:
            while True:
                # 1. GERENCIAMENTO DE PAUSA E FLUSH
                if not control_event.is_set():
                    # print(f"[{self.__class__.__name__}] Pausado. Aguardando...")
                    await control_event.wait()
                    # Ao retomar, limpa o buffer de hardware para não enviar áudio "velho"
                    await asyncio.to_thread(self._flush_input_buffer)
                
                # 2. LEITURA OTIMIZADA DO HARDWARE
                # Read chunk deve ser rápido. Se o hardware tiver overflow, ignoramos o erro
                try:
                    data = await asyncio.to_thread(self.audio_input_manager.read_chunk)
                except Exception as e:
                    # Input Overflow é comum em tempo real se a CPU pular. Ignora e segue.
                    continue

                if data:
                    # 3. ENVIO NÃO-BLOQUEANTE (REAL-TIME)
                    # Se a fila estiver cheia (rede lenta), descartamos o pacote (Drop)
                    # Isso garante que a IA sempre receba o áudio MAIS RECENTE, não o antigo.
                    try:
                        out_queue.put_nowait({"data": data, "mime_type": "audio/pcm"})
                    except asyncio.QueueFull:
                        pass # Drop frame intencional para manter sincronia

        except asyncio.CancelledError:
            print(f"[{self.__class__.__name__} task_capture_audio] Tarefa cancelada.")
        except Exception as e:
            print(f"[{self.__class__.__name__} task_capture_audio] Erro fatal: {e}")

    def _flush_input_buffer(self):
        """Limpeza agressiva de buffer de entrada"""
        try:
            if hasattr(self.audio_input_manager, 'input_stream'):
                available = self.audio_input_manager.input_stream.get_read_available()
                if available > 0:
                    self.audio_input_manager.input_stream.read(available, exception_on_overflow=False)
        except Exception:
            pass

    async def task_play_audio(self, input_queue: asyncio.Queue):
        """
        Consome a fila de áudio e escreve na saída.
        """
        self.audio_output_manager.start_output_stream()
        print(f"[{self.__class__.__name__} task_play_audio] Stream de saída iniciado.")
        
        try:
            while True:
                bytestream = await input_queue.get()
                
                # Escreve no hardware (bloqueante, mas em thread separada)
                await asyncio.to_thread(self.audio_output_manager.write_chunk, bytestream)
                
                input_queue.task_done()
        except asyncio.CancelledError:
             print(f"[{self.__class__.__name__} task_play_audio] Tarefa cancelada.")

    def drain_audio_queue(self, queue: asyncio.Queue):
        """
        Método CRÍTICO para sensação de tempo real.
        Esvazia a fila de reprodução imediatamente (Barge-in).
        """
        items_dropped = 0
        while not queue.empty():
            try:
                queue.get_nowait()
                queue.task_done()
                items_dropped += 1
            except (asyncio.QueueEmpty, ValueError):
                break
        
        if items_dropped > 0:
            print(f"[{self.__class__.__name__}] Drain: {items_dropped} chunks de áudio descartados.")

    async def play_file(self, file_path: str, target_queue: asyncio.Queue, loop):
        print(f"[{self.__class__.__name__} play_file] Reproduzindo: {file_path}")
        def process_file():
            for chunk in self.wav_reader.read_chunks(file_path):
                loop.call_soon_threadsafe(target_queue.put_nowait, chunk)
        await asyncio.to_thread(process_file)

    def close(self):
        print(f"[{self.__class__.__name__} close] Encerrando gerenciadores.")
        self.audio_input_manager.close()
        self.audio_output_manager.close()