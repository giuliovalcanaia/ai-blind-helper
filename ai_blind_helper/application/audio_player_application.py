import asyncio
import wave
import os
import time
from datetime import datetime
from manager import InputAudioManager, OutputAudioManager
from reader import WavReader
from config import Config

class AudioPlayerApplication:
    def __init__(self):
        # --- MANTENDO SEUS MANAGERS ORIGINAIS ---
        self.audio_input_manager = InputAudioManager()
        self.audio_output_manager = OutputAudioManager()
        self.wav_reader = WavReader(
            target_rate=Config.RECEIVE_SAMPLE_RATE,
            target_channels=Config.CHANNELS
        )
        
        self.base_debug_folder = "gravacoes_debug"

        # --- NOVA LÓGICA DE PLAYBACK (Estado) ---
        self.audio_buffer = bytearray()  # O "histórico" do áudio atual
        self.playback_cursor = 0         # Cabeçote de leitura (bytes)
        self.is_paused = False
        
        # Constante para cálculo de segundos (Taxa * Canais * Bytes por amostra)
        # Assumindo 16-bit PCM (2 bytes)
        self.BYTES_PER_SECOND = Config.RECEIVE_SAMPLE_RATE * Config.CHANNELS * 2

    # ---------------------------------------------------------
    # 1. INPUT (Mantido idêntico ao que funciona)
    # ---------------------------------------------------------
    async def task_capture_audio(self, out_queue: asyncio.Queue, control_event: asyncio.Event):
        # ... (Sua implementação original do task_capture_audio fica AQUI inalterada) ...
        # Apenas para resumir no código final, estou omitindo o corpo, 
        # mas use EXATAMENTE o código do seu exemplo "Correto".
        self.audio_input_manager.start_input_stream()
        print(" -> [AudioApp] Microfone Iniciado.")
        
        # ... (Lógica de gravação e envio para out_queue) ...
        # Se quiser que eu repita o código inteiro do input, me avise,
        # mas o foco do erro é no output.

    # ---------------------------------------------------------
    # 2. OUTPUT (Refatorado para suportar Pausa/Rewind + Managers)
    # ---------------------------------------------------------
    async def task_play_audio(self, input_queue: asyncio.Queue):
        """
        Consome a fila da IA e gerencia o playback usando o OutputAudioManager.
        """
        self.audio_output_manager.start_output_stream()
        
        # Limpa estado anterior
        self.reset_playback_state()

        # Roda dois loops em paralelo:
        # 1. Ingestão: Pega da fila e guarda no buffer.
        # 2. Playback: Pega do buffer e manda para o Manager.
        await asyncio.gather(
            self._loop_ingest_data(input_queue),
            self._loop_playback_stream()
        )

    async def _loop_ingest_data(self, input_queue: asyncio.Queue):
        """Lê da fila do Gemini e acumula no buffer RAM"""
        while True:
            try:
                chunk_dict = await input_queue.get() # Assumindo dict {"data": bytes, ...} ou bytes diretos
                
                # Tratamento caso venha dict ou bytes puros
                data = chunk_dict["data"] if isinstance(chunk_dict, dict) else chunk_dict

                if data:
                    self.audio_buffer.extend(data)
                
                input_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[AudioApp] Erro ingestão: {e}")
                break

    async def _loop_playback_stream(self):
        """Lê do buffer interno e manda para o OutputAudioManager"""
        # Tamanho do pedaço a ler do buffer por vez (ex: 4096 bytes)
        chunk_read_size = 4096 

        while True:
            # A. Se estiver pausado, aguarda sem travar a thread
            if self.is_paused:
                await asyncio.sleep(0.1)
                continue

            # B. Verifica se o cursor está atrás do final do buffer (tem algo pra tocar)
            buffer_len = len(self.audio_buffer)
            
            if self.playback_cursor < buffer_len:
                # Define o pedaço (slice)
                end_pos = min(self.playback_cursor + chunk_read_size, buffer_len)
                data_chunk = self.audio_buffer[self.playback_cursor : end_pos]

                # C. Manda para o MANAGER (AQUI ESTÁ A CORREÇÃO CRUCIAL)
                # Usamos to_thread para não bloquear o loop async enquanto o áudio é escrito
                await asyncio.to_thread(self.audio_output_manager.write_chunk, bytes(data_chunk))

                # Avança o cursor
                self.playback_cursor = end_pos
            else:
                # Buffer vazio ou chegamos ao fim do que foi baixado até agora
                await asyncio.sleep(0.01)

    async def play_file(self, file_path: str, target_queue: asyncio.Queue, loop):
        """Lê um arquivo WAV e injeta os chunks na fila de áudio para ser tocado"""
        def process_file():
            # Lê o arquivo e joga na fila usando threadsafe pois roda em thread
            for chunk in self.wav_reader.read_chunks(file_path):
                loop.call_soon_threadsafe(
                    target_queue.put_nowait, chunk)
        await asyncio.to_thread(process_file)

    # ---------------------------------------------------------
    # 3. MÉTODOS DE CONTROLE (Play/Pause/Rewind)
    # ---------------------------------------------------------
    def toggle_pause(self):
        self.is_paused = not self.is_paused
        state = "PAUSADO" if self.is_paused else "TOCANDO"
        print(f">>> [Audio] {state}")

    def rewind(self, seconds=5):
        """Volta X segundos no buffer"""
        bytes_to_rewind = int(seconds * self.BYTES_PER_SECOND)
        old_cursor = self.playback_cursor
        
        # Garante que não volta para antes do zero
        self.playback_cursor = max(0, self.playback_cursor - bytes_to_rewind)
        
        print(f">>> [Audio] Rewind {seconds}s. Cursor: {old_cursor} -> {self.playback_cursor}")

    def forward(self, seconds=5):
        """Avança X segundos"""
        bytes_to_forward = int(seconds * self.BYTES_PER_SECOND)
        buffer_len = len(self.audio_buffer)
        
        # Garante que não passa do que já temos baixado
        self.playback_cursor = min(buffer_len, self.playback_cursor + bytes_to_forward)
        print(f">>> [Audio] Forward {seconds}s")

    def reset_playback_state(self):
        """Chamado sempre que uma nova interação (nova fala do usuário) começa"""
        self.audio_buffer = bytearray()
        self.playback_cursor = 0
        self.is_paused = False

    # ---------------------------------------------------------
    # 4. ENCERRAMENTO
    # ---------------------------------------------------------
    def close(self):
        print(" -> [AudioApp] Encerrando managers...")
        self.audio_input_manager.close()
        self.audio_output_manager.close()
        # Se houver streams abertas no wav_reader, fechar também, se aplicável