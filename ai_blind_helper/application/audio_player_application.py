import asyncio
import os
import wave
import traceback
import time
from datetime import datetime
from config import Config

class AudioPlayerApplication:
    def __init__(self, audio_input_manager, audio_output_manager, wav_reader):
        print("[AudioPlayerApplication __init__] Inicializando aplicação de áudio e buffers")
        try:
            self.audio_input_manager = audio_input_manager
            self.audio_output_manager = audio_output_manager
            self.wav_reader = wav_reader 
            
            self.audio_buffer = bytearray()
            self.playback_cursor = 0
            self.is_paused = False
            self.BYTES_PER_SECOND = Config.RECEIVE_SAMPLE_RATE * Config.CHANNELS * 2
            self.base_debug_folder = "gravacoes_debug"
            
            print("[AudioPlayerApplication __init__] Configurações de hardware e debug prontas")
        except Exception as e:
            print(f"[AudioPlayerApplication __init__] ERRO FATAL: {e}")
            traceback.print_exc()

    async def task_capture_audio(self, out_queue: asyncio.Queue, control_event: asyncio.Event):
        print("[AudioPlayerApplication task_capture_audio] Iniciando captura de microfone com gravação de debug")
        try:
            self.audio_input_manager.start_input_stream()

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_dir = os.path.join(self.base_debug_folder, f"sessao_{timestamp}")
            chunks_dir = os.path.join(session_dir, "chunks")
            os.makedirs(chunks_dir, exist_ok=True)

            full_filename = os.path.join(session_dir, "full_recording.wav")
            chunk_counter = 0

            with wave.open(full_filename, 'wb') as wf_full:
                self._setup_wav_header(wf_full)

                while True:
                    if not control_event.is_set():
                        print("[AudioPlayerApplication task_capture_audio] Input em espera (control_event bloqueado)")
                        await control_event.wait()
                        print("[AudioPlayerApplication task_capture_audio] Retomando captura e limpando buffer residual")
                        self._flush_input_buffer()

                    data = await asyncio.to_thread(self.audio_input_manager.read_chunk)

                    if data:
                        wf_full.writeframes(data)

                        chunk_filename = os.path.join(chunks_dir, f"chunk_{chunk_counter:05d}.wav")
                        with wave.open(chunk_filename, 'wb') as wf_chunk:
                            self._setup_wav_header(wf_chunk)
                            wf_chunk.writeframes(data)
                        
                        chunk_counter += 1
                        await out_queue.put({"data": data, "mime_type": "audio/pcm"})
                    else:
                        await asyncio.sleep(0.01)

        except asyncio.CancelledError:
            print("[AudioPlayerApplication task_capture_audio] Task de captura cancelada. Finalizando arquivos")
        except Exception as e:
            print(f"[AudioPlayerApplication task_capture_audio] Erro na captura: {e}")
            traceback.print_exc()

    async def task_play_audio(self, input_queue: asyncio.Queue):
        print("[AudioPlayerApplication task_play_audio] Preparando hardware de saída para reprodução")
        try:
            self.audio_output_manager.start_output_stream()
            print("[AudioPlayerApplication task_play_audio] Output stream aberto com sucesso")
        except Exception as e:
            print(f"[AudioPlayerApplication task_play_audio] Falha crítica ao abrir saída: {e}")

        self.reset_playback_state()

        try:
            print("[AudioPlayerApplication task_play_audio] Iniciando loops de ingestão e playback")
            await asyncio.gather(
                self._loop_ingest_data(input_queue),
                self._loop_playback_stream()
            )
        except Exception as e:
            print(f"[AudioPlayerApplication task_play_audio] Erro no gather de reprodução: {e}")
            traceback.print_exc()

    async def _loop_ingest_data(self, input_queue: asyncio.Queue):
        print("[AudioPlayerApplication _loop_ingest_data] Loop de ingestão de dados iniciado")
        while True:
            try:
                chunk_wrapper = await input_queue.get()
                
                data = None
                if isinstance(chunk_wrapper, dict):
                    data = chunk_wrapper.get("data")
                elif isinstance(chunk_wrapper, (bytes, bytearray)):
                    data = chunk_wrapper
                
                if data:
                    self.audio_buffer.extend(data)
                
                input_queue.task_done()

            except asyncio.CancelledError:
                print("[AudioPlayerApplication _loop_ingest_data] Ingestão interrompida")
                break
            except Exception as e:
                print(f"[AudioPlayerApplication _loop_ingest_data] Erro ao processar chunk: {e}")
                await asyncio.sleep(0.1)

    async def _loop_playback_stream(self):
        print("[AudioPlayerApplication _loop_playback_stream] Loop de streaming para hardware iniciado")
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

                    if self.audio_output_manager and self.audio_output_manager.output_stream:
                        await asyncio.to_thread(self.audio_output_manager.write_chunk, bytes(data_chunk))
                        self.playback_cursor = end_pos
                    else:
                        self.playback_cursor = end_pos
                        await asyncio.sleep(0.01)
                else:
                    await asyncio.sleep(0.01)

            except asyncio.CancelledError:
                print("[AudioPlayerApplication _loop_playback_stream] Streaming interrompido")
                break
            except OSError as oe:
                print(f"[AudioPlayerApplication _loop_playback_stream] Erro de hardware: {oe}")
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"[AudioPlayerApplication _loop_playback_stream] Erro genérico no playback: {e}")
                await asyncio.sleep(0.5)

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        print(f"[AudioPlayerApplication toggle_pause] Novo estado de pausa: {self.is_paused}")

    def rewind(self, seconds=5):
        print(f"[AudioPlayerApplication rewind] Retrocedendo {seconds} segundos")
        try:
            bytes_to_rewind = int(seconds * self.BYTES_PER_SECOND)
            self.playback_cursor = max(0, self.playback_cursor - bytes_to_rewind)
            print(f"[AudioPlayerApplication rewind] Novo cursor: {self.playback_cursor}")
        except: pass

    def forward(self, seconds=5):
        print(f"[AudioPlayerApplication forward] Avançando {seconds} segundos")
        try:
            bytes_to_forward = int(seconds * self.BYTES_PER_SECOND)
            self.playback_cursor = min(len(self.audio_buffer), self.playback_cursor + bytes_to_forward)
            print(f"[AudioPlayerApplication forward] Novo cursor: {self.playback_cursor}")
        except: pass    

    def reset_playback_state(self):
        print("[AudioPlayerApplication reset_playback_state] Limpando buffers e reiniciando cursor")
        self.audio_buffer = bytearray()
        self.playback_cursor = 0
        self.is_paused = False

    async def play_file(self, file_path: str, target_queue: asyncio.Queue, loop):
        print(f"[AudioPlayerApplication play_file] Lendo arquivo WAV para injeção na fila: {file_path}")
        def process_file():
            for chunk in self.wav_reader.read_chunks(file_path):
                loop.call_soon_threadsafe(target_queue.put_nowait, chunk)
        await asyncio.to_thread(process_file)

    def _setup_wav_header(self, wav_file):
        wav_file.setnchannels(Config.CHANNELS)
        wav_file.setsampwidth(2)
        wav_file.setframerate(Config.RECEIVE_SAMPLE_RATE)

    def _flush_input_buffer(self):
        print("[AudioPlayerApplication _flush_input_buffer] Descartando áudio acumulado durante pausa")
        try:
            if self.audio_input_manager.input_stream:
                available = self.audio_input_manager.input_stream.get_read_available()
                if available > 0:
                    self.audio_input_manager.input_stream.read(available, exception_on_overflow=False)
        except: pass

    def close(self):
        print("[AudioPlayerApplication close] Encerrando conexões de hardware")
        try:
            if self.audio_input_manager: self.audio_input_manager.close()
            if self.audio_output_manager: self.audio_output_manager.close()
            print("[AudioPlayerApplication close] Recursos liberados com sucesso")
        except Exception as e:
            print(f"[AudioPlayerApplication close] Erro ao fechar recursos: {e}")