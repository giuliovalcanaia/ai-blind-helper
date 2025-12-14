import asyncio
import pyaudio
from config import Config

class AudioPlayerApplication:
    def __init__(self):
        self.pya = pyaudio.PyAudio()
        self.output_stream = None
        self._init_stream()
        
        # --- Lógica de Controle de Playback ---
        self.audio_buffer = bytearray() # Armazena todo o áudio da resposta atual
        self.cursor = 0                 # Onde estamos tocando agora (em bytes)
        self.is_paused = False
        
        # Constantes para navegação (Calculadas baseadas no Config)
        # Ex: 24000Hz * 1 canal * 2 bytes (16bit) = 48000 bytes/seg
        self.BYTES_PER_SECOND = Config.RECEIVE_SAMPLE_RATE * Config.CHANNELS * 2 

    def _init_stream(self):
        """Inicializa o stream do PyAudio"""
        if self.output_stream:
            self.output_stream.close()
            
        self.output_stream = self.pya.open(
            format=Config.AUDIO_FORMAT,
            channels=Config.CHANNELS,
            rate=Config.RECEIVE_SAMPLE_RATE,
            output=True,
        )

    async def task_play_audio(self, input_queue: asyncio.Queue):
        """
        Tarefa principal: Consome a fila (ingestão) E toca o buffer (playback).
        Roda dois loops simultâneos via asyncio.gather ou tarefas background.
        """
        # Limpa o buffer ao iniciar uma nova sessão de escuta
        self.reset_buffer()
        
        # Cria duas tarefas: uma para encher o buffer, outra para tocar
        ingest_task = asyncio.create_task(self._buffer_ingestion_loop(input_queue))
        playback_task = asyncio.create_task(self._playback_loop())
        
        await asyncio.gather(ingest_task, playback_task)

    async def _buffer_ingestion_loop(self, input_queue: asyncio.Queue):
        """Lê da fila do Gemini e anexa ao buffer interno."""
        while True:
            try:
                chunk = await input_queue.get()
                if chunk:
                    self.audio_buffer.extend(chunk)
                input_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[Audio Error] Ingestão falhou: {e}")
                break

    async def _playback_loop(self):
        """Lê do buffer interno baseando-se no cursor e envia para o falante."""
        chunk_size = Config.CHUNK_SIZE
        
        while True:
            # 1. Se estiver pausado, apenas espera
            if self.is_paused:
                await asyncio.sleep(0.1)
                continue

            # 2. Verifica se temos dados para tocar a partir do cursor
            buffer_len = len(self.audio_buffer)
            
            if self.cursor < buffer_len:
                # Calcula o pedaço a tocar
                end_pos = min(self.cursor + chunk_size, buffer_len)
                data_chunk = self.audio_buffer[self.cursor : end_pos]
                
                # Envia para o hardware (bloqueante mas rápido o suficiente)
                # Rodamos em thread separada para não travar o loop async se o buffer do SO encher
                await asyncio.to_thread(self._write_to_stream, data_chunk)
                
                # Avança o cursor
                self.cursor = end_pos
            else:
                # Se chegamos ao fim do buffer (e a stream ainda está ativa), esperamos mais dados
                await asyncio.sleep(0.01)

    def _write_to_stream(self, data):
        if self.output_stream:
            self.output_stream.write(bytes(data))

    # --- Métodos de Controle (Chamados pelo MainController) ---

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        status = "PAUSADO" if self.is_paused else "TOCANDO"
        print(f">>> [Audio] {status}")

    def rewind(self, seconds=5):
        """Volta X segundos no áudio"""
        bytes_to_rewind = int(seconds * self.BYTES_PER_SECOND)
        old_cursor = self.cursor
        self.cursor = max(0, self.cursor - bytes_to_rewind)
        print(f">>> [Audio] Retroceder {seconds}s (Pos: {self.cursor}/{len(self.audio_buffer)})")

    def forward(self, seconds=5):
        """Avança X segundos no áudio"""
        bytes_to_forward = int(seconds * self.BYTES_PER_SECOND)
        self.cursor = min(len(self.audio_buffer), self.cursor + bytes_to_forward)
        print(f">>> [Audio] Avançar {seconds}s")

    def reset_buffer(self):
        """Chame isso quando o usuário começar a falar para limpar a resposta anterior"""
        self.audio_buffer = bytearray()
        self.cursor = 0
        self.is_paused = False

    def close(self):
        if self.output_stream:
            self.output_stream.stop_stream()
            self.output_stream.close()
        self.pya.terminate()
        
    # Método legado para manter compatibilidade com sons de sistema (clock/date)
    async def play_file(self, file_path, queue, loop):
        # Implementação simplificada: lê arquivo e joga na queue
        # Nota: Isso vai entrar no buffer do fluxo principal. 
        # Idealmente sons de sistema usariam um canal separado, mas para simplificar:
        import wave
        def _read_wave():
            with wave.open(file_path, 'rb') as wf:
                data = wf.readframes(1024)
                while data:
                    asyncio.run_coroutine_threadsafe(queue.put(data), loop)
                    data = wf.readframes(1024)
        await asyncio.to_thread(_read_wave)