import asyncio
import os
import wave
import traceback
import time
from datetime import datetime
from config import Config

class AudioPlayerApplication:
    def __init__(self, audio_input_manager, audio_output_manager, wav_reader):
        try:
            print("🛠️ [AudioApp] Inicializando construtor...")
            self.audio_input_manager = audio_input_manager
            self.audio_output_manager = audio_output_manager
            self.wav_reader = wav_reader 
            
            # --- Configuração de Buffer (Necessário para Pause/Rewind) ---
            self.audio_buffer = bytearray()
            self.playback_cursor = 0
            self.is_paused = False
            self.BYTES_PER_SECOND = Config.RECEIVE_SAMPLE_RATE * Config.CHANNELS * 2

            # --- Configuração de Debug (Nova Feature) ---
            self.base_debug_folder = "gravacoes_debug"
            
            print("✅ [AudioApp] Construtor OK.")
        except Exception as e:
            print(f"❌ [AudioApp] ERRO FATAL no __init__: {e}")
            traceback.print_exc()

    # =========================================================================
    # INPUT TASK (Com gravação de Debug - Feature Nova)
    # =========================================================================
    async def task_capture_audio(self, out_queue: asyncio.Queue, control_event: asyncio.Event):
        """
        Lê do Mic e realiza ações simultâneas:
        1. Salva arquivo contínuo.
        2. Salva chunks individuais.
        3. Envia para a fila da IA.
        """
        try:
            self.audio_input_manager.start_input_stream()
            print("🎙️ [AudioApp] Input stream iniciado.")

            # --- PREPARAÇÃO DAS PASTAS DESTA SESSÃO ---
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_dir = os.path.join(self.base_debug_folder, f"sessao_{timestamp}")
            chunks_dir = os.path.join(session_dir, "chunks")

            os.makedirs(chunks_dir, exist_ok=True)
            print(f"🎙️ [Audio] Salvando debug completo e chunks em: {session_dir}")

            full_filename = os.path.join(session_dir, "full_recording.wav")
            chunk_counter = 0

            # Abre o arquivo "PAI" (Gravação contínua)
            with wave.open(full_filename, 'wb') as wf_full:
                self._setup_wav_header(wf_full)

                while True:
                    # 1. PAUSA / RESUME (Controle de Input)
                    if not control_event.is_set():
                        print("🔴 [Audio Input] Pausado...")
                        await control_event.wait()
                        print("🟢 [Audio Input] Retomando...")
                        self._flush_input_buffer()

                    # 2. LEITURA DO HARDWARE
                    data = await asyncio.to_thread(self.audio_input_manager.read_chunk)

                    if data:
                        # A: Salva no arquivo contínuo
                        wf_full.writeframes(data)

                        # B: Salva o Chunk isolado
                        chunk_filename = os.path.join(chunks_dir, f"chunk_{chunk_counter:05d}.wav")
                        with wave.open(chunk_filename, 'wb') as wf_chunk:
                            self._setup_wav_header(wf_chunk)
                            wf_chunk.writeframes(data)
                        
                        chunk_counter += 1

                        # C: Envia para a IA (Output Queue)
                        await out_queue.put({"data": data, "mime_type": "audio/pcm"})
                    else:
                        await asyncio.sleep(0.01)

        except asyncio.CancelledError:
            print("⏹️ [AudioApp] Captura cancelada. Arquivos salvos.")
        except Exception as e:
            print(f"❌ [AudioApp] Erro na CAPTURA: {e}")
            traceback.print_exc()

    # =========================================================================
    # OUTPUT TASK (Com Buffer para Controles - Feature Restaurada)
    # =========================================================================
    async def task_play_audio(self, input_queue: asyncio.Queue):
        print("🛠️ [AudioApp] Iniciando task_play_audio...")
        
        try:
            # 1. Tenta iniciar o hardware de saída
            print("🛠️ [AudioApp] Tentando iniciar output stream...")
            self.audio_output_manager.start_output_stream()
            print("✅ [AudioApp] Output stream iniciado.")
        except Exception as e:
            print(f"❌ [AudioApp] FALHA AO ABRIR AUDIO OUTPUT: {e}")
            print("⚠️ [AudioApp] Continuando apenas ingestão para debug...")

        self.reset_playback_state()

        # 2. Inicia os loops protegidos (Ingestão + Playback Bufferizado)
        try:
            await asyncio.gather(
                self._loop_ingest_data(input_queue),
                self._loop_playback_stream()
            )
        except Exception as e:
            print(f"❌ [AudioApp] Erro CRÍTICO no gather: {e}")
            traceback.print_exc()

    async def _loop_ingest_data(self, input_queue: asyncio.Queue):
        """Consome da fila e joga no buffer interno"""
        print("Start: Ingest Loop")
        while True:
            try:
                chunk_wrapper = await input_queue.get()
                
                # Extração segura dos dados (Compatível com dict ou bytes)
                data = None
                if isinstance(chunk_wrapper, dict):
                    data = chunk_wrapper.get("data")
                elif isinstance(chunk_wrapper, (bytes, bytearray)):
                    data = chunk_wrapper
                
                if data:
                    self.audio_buffer.extend(data)
                
                input_queue.task_done()

            except asyncio.CancelledError:
                print("Stop: Ingest Loop (Cancelled)")
                break
            except Exception as e:
                print(f"❌ [AudioApp] Erro Ingestão: {e}")
                await asyncio.sleep(0.1)

    async def _loop_playback_stream(self):
        """Consome do buffer interno respeitando o cursor e pause"""
        print("Start: Playback Loop")
        chunk_read_size = 4096 

        while True:
            try:
                if self.is_paused:
                    await asyncio.sleep(0.1)
                    continue

                buffer_len = len(self.audio_buffer)
                
                if self.playback_cursor < buffer_len:
                    end_pos = min(self.playback_cursor + chunk_read_size, buffer_len)
                    data_chunk = self.audio_buffer[self.playback_cursor : end_pos]

                    # Verifica se o hardware existe
                    if self.audio_output_manager and self.audio_output_manager.output_stream:
                        # Executa escrita bloqueante em thread
                        await asyncio.to_thread(self.audio_output_manager.write_chunk, bytes(data_chunk))
                        self.playback_cursor = end_pos
                    else:
                        # Simulação se sem hardware
                        self.playback_cursor = end_pos
                        await asyncio.sleep(0.01)
                        
                else:
                    # Buffer vazio ou chegou ao fim
                    await asyncio.sleep(0.01)

            except asyncio.CancelledError:
                print("Stop: Playback Loop (Cancelled)")
                break
            except OSError as oe:
                print(f"⚠️ [AudioApp] Erro de Hardware (OSError): {oe}")
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"❌ [AudioApp] Erro Playback Genérico: {e}")
                traceback.print_exc()
                await asyncio.sleep(0.5)

    # =========================================================================
    # CONTROLES (Pause, Forward, Rewind)
    # =========================================================================
    def toggle_pause(self):
        self.is_paused = not self.is_paused
        status = "PAUSADO" if self.is_paused else "TOCANDO"
        print(f">>> [Audio Control] {status}")

    def rewind(self, seconds=5):
        try:
            bytes_to_rewind = int(seconds * self.BYTES_PER_SECOND)
            self.playback_cursor = max(0, self.playback_cursor - bytes_to_rewind)
            print(f">>> [Audio Control] Rewind -{seconds}s. Cursor: {self.playback_cursor}")
        except: pass

    def forward(self, seconds=5):
        try:
            bytes_to_forward = int(seconds * self.BYTES_PER_SECOND)
            self.playback_cursor = min(len(self.audio_buffer), self.playback_cursor + bytes_to_forward)
            print(f">>> [Audio Control] Forward +{seconds}s. Cursor: {self.playback_cursor}")
        except: pass    

    def reset_playback_state(self):
        self.audio_buffer = bytearray()
        self.playback_cursor = 0
        self.is_paused = False

    # =========================================================================
    # UTILITÁRIOS E HELPERS
    # =========================================================================
    async def play_file(self, file_path: str, target_queue: asyncio.Queue, loop):
        """Lê um arquivo WAV e injeta na fila (Feature mantida do código novo)"""
        def process_file():
            for chunk in self.wav_reader.read_chunks(file_path):
                loop.call_soon_threadsafe(
                    target_queue.put_nowait, chunk)
        await asyncio.to_thread(process_file)

    def _setup_wav_header(self, wav_file):
        """Configura o cabeçalho WAV padrão"""
        wav_file.setnchannels(Config.CHANNELS)
        wav_file.setsampwidth(2)  # 16-bit PCM
        wav_file.setframerate(Config.RECEIVE_SAMPLE_RATE)

    def _flush_input_buffer(self):
        """Limpeza de buffer ao retomar pause no input"""
        try:
            if self.audio_input_manager.input_stream:
                available = self.audio_input_manager.input_stream.get_read_available()
                if available > 0:
                    self.audio_input_manager.input_stream.read(available, exception_on_overflow=False)
        except: pass

    def close(self):
        try:
            if self.audio_input_manager: self.audio_input_manager.close()
            if self.audio_output_manager: self.audio_output_manager.close()
            print("✅ [AudioApp] Fechado com sucesso.")
        except Exception as e:
            print(f"⚠️ [AudioApp] Erro ao fechar: {e}")