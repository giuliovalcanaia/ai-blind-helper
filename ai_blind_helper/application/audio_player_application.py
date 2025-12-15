import asyncio
import os
import traceback
from manager import InputAudioManager, OutputAudioManager
from reader import WavReader
from config import Config

class AudioPlayerApplication:
    def __init__(self):
        try:
            print("🛠️ [AudioApp] Inicializando construtor...")
            self.audio_input_manager = InputAudioManager()
            self.audio_output_manager = OutputAudioManager()
            self.wav_reader = WavReader(
                target_rate=Config.RECEIVE_SAMPLE_RATE,
                target_channels=Config.CHANNELS
            )
            
            # Estado do Player
            self.audio_buffer = bytearray()
            self.playback_cursor = 0
            self.is_paused = False
            self.BYTES_PER_SECOND = Config.RECEIVE_SAMPLE_RATE * Config.CHANNELS * 2
            print("✅ [AudioApp] Construtor OK.")
        except Exception as e:
            print(f"❌ [AudioApp] ERRO FATAL no __init__: {e}")
            traceback.print_exc()

    # --- INPUT (Mantido simples, pois parece estar OK) ---
    async def task_capture_audio(self, out_queue: asyncio.Queue, control_event: asyncio.Event):
        try:
            self.audio_input_manager.start_input_stream()
            print("🎙️ [AudioApp] Input stream iniciado.")
            
            # Simulação do loop de captura para não quebrar o código
            # (Substitua pelo seu código real de captura se ele for diferente)
            while True:
                if not control_event.is_set():
                    await control_event.wait()
                    # Limpa buffer ao retomar
                    try:
                        await asyncio.to_thread(self.audio_input_manager.input_stream.read, 
                                              self.audio_input_manager.input_stream.get_read_available())
                    except: pass

                data = await asyncio.to_thread(self.audio_input_manager.read_chunk)
                if data:
                    await out_queue.put({"data": data, "mime_type": "audio/pcm"})
                else:
                    await asyncio.sleep(0.01)

        except asyncio.CancelledError:
            print("⏹️ [AudioApp] Captura cancelada.")
        except Exception as e:
            print(f"❌ [AudioApp] Erro na CAPTURA: {e}")

    # --- OUTPUT (Onde está o problema) ---
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
            # Não damos raise aqui para não matar o TaskGroup, apenas logamos o erro

        self.reset_playback_state()

        # 2. Inicia os loops protegidos
        try:
            await asyncio.gather(
                self._loop_ingest_data(input_queue),
                self._loop_playback_stream()
            )
        except Exception as e:
            print(f"❌ [AudioApp] Erro CRÍTICO no gather: {e}")
            traceback.print_exc()

    async def _loop_ingest_data(self, input_queue: asyncio.Queue):
        print("Start: Ingest Loop")
        while True:
            try:
                chunk_wrapper = await input_queue.get()
                
                # Extração segura dos dados
                data = None
                if isinstance(chunk_wrapper, dict):
                    data = chunk_wrapper.get("data")
                elif isinstance(chunk_wrapper, bytes) or isinstance(chunk_wrapper, bytearray):
                    data = chunk_wrapper
                
                if data:
                    self.audio_buffer.extend(data)
                
                input_queue.task_done()

            except asyncio.CancelledError:
                print("Stop: Ingest Loop (Cancelled)")
                break
            except Exception as e:
                print(f"❌ [AudioApp] Erro Ingestão: {e}")
                # Não quebra o loop, apenas loga
                await asyncio.sleep(0.1)

    async def _loop_playback_stream(self):
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

                    # Verifica se o manager e a stream existem antes de tentar escrever
                    if self.audio_output_manager and self.audio_output_manager.output_stream:
                        # Executa escrita bloqueante em thread
                        await asyncio.to_thread(self.audio_output_manager.write_chunk, bytes(data_chunk))
                        self.playback_cursor = end_pos
                    else:
                        # Se não tem hardware, simula que tocou para não travar buffer
                        self.playback_cursor = end_pos
                        await asyncio.sleep(0.01) # Simula tempo de playback
                        
                else:
                    await asyncio.sleep(0.01)

            except asyncio.CancelledError:
                print("Stop: Playback Loop (Cancelled)")
                break
            except OSError as oe:
                 # Erros comuns de Audio Device (ex: Input/Output error)
                print(f"⚠️ [AudioApp] Erro de Hardware (OSError): {oe}")
                await asyncio.sleep(0.5) # Espera um pouco antes de tentar de novo
            except Exception as e:
                print(f"❌ [AudioApp] Erro Playback Genérico: {e}")
                traceback.print_exc()
                await asyncio.sleep(0.5)

    def reset_playback_state(self):
        self.audio_buffer = bytearray()
        self.playback_cursor = 0
        self.is_paused = False

    def close(self):
        try:
            if self.audio_input_manager: self.audio_input_manager.close()
            if self.audio_output_manager: self.audio_output_manager.close()
            print("✅ [AudioApp] Fechado com sucesso.")
        except Exception as e:
            print(f"⚠️ [AudioApp] Erro ao fechar: {e}")

    # Métodos de controle
    def toggle_pause(self):
        self.is_paused = not self.is_paused
        print(f">>> [Audio] Pausado: {self.is_paused}")

    def rewind(self, seconds=5):
        try:
            bytes_to_rewind = int(seconds * self.BYTES_PER_SECOND)
            self.playback_cursor = max(0, self.playback_cursor - bytes_to_rewind)
            print(f">>> [Audio] Rewind. Pos: {self.playback_cursor}")
        except: pass

    def forward(self, seconds=5):
        try:
            bytes_to_forward = int(seconds * self.BYTES_PER_SECOND)
            self.playback_cursor = min(len(self.audio_buffer), self.playback_cursor + bytes_to_forward)
            print(f">>> [Audio] Forward. Pos: {self.playback_cursor}")
        except: pass    