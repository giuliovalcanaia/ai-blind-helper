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
        self.audio_input_manager = InputAudioManager()
        self.audio_output_manager = OutputAudioManager()
        self.wav_reader = WavReader(
            target_rate=Config.RECEIVE_SAMPLE_RATE,
            target_channels=Config.CHANNELS
        )
        # Configuração base
        self.base_debug_folder = "gravacoes_debug"

    async def task_capture_audio(self, out_queue: asyncio.Queue, control_event: asyncio.Event):
        """
        Lê do Mic e realiza três ações simultâneas:
        1. Salva no arquivo 'completo'.
        2. Salva cada pedaço em um arquivo individual na pasta 'chunks'.
        3. Envia para a fila da IA.
        """
        self.audio_input_manager.start_input_stream()
        print(" -> [AudioApp] Microfone Iniciado.")
        
        # --- PREPARAÇÃO DAS PASTAS DESTA SESSÃO ---
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = os.path.join(self.base_debug_folder, f"sessao_{timestamp}")
        chunks_dir = os.path.join(session_dir, "chunks")
        
        os.makedirs(chunks_dir, exist_ok=True)
        print(f"🎙️ [Audio] Salvando debug completo e chunks em: {session_dir}")

        full_filename = os.path.join(session_dir, "full_recording.wav")
        chunk_counter = 0

        try:
            # Abre o arquivo "PAI" (Gravação contínua)
            with wave.open(full_filename, 'wb') as wf_full:
                self._setup_wav_header(wf_full)

                while True:
                    # 1. PAUSA / RESUME
                    if not control_event.is_set():
                        print("🔴 [Audio] Pausado...")
                        await control_event.wait()
                        print("🟢 [Audio] Retomando...")
                        try:
                            await asyncio.to_thread(self._flush_input_buffer)
                        except Exception:
                            pass

                    # 2. LEITURA DO HARDWARE
                    data = await asyncio.to_thread(self.audio_input_manager.read_chunk)
                    
                    if data:
                        # --- A: Salva no arquivo contínuo ---
                        wf_full.writeframes(data)

                        # --- B: Salva o Chunk isolado (EXATAMENTE como a IA recebe) ---
                        chunk_filename = os.path.join(chunks_dir, f"chunk_{chunk_counter:05d}.wav")
                        # Atenção: Abrir e fechar arquivos em loop é custoso (IO), 
                        # mas necessário para isolar os arquivos.
                        with wave.open(chunk_filename, 'wb') as wf_chunk:
                            self._setup_wav_header(wf_chunk)
                            wf_chunk.writeframes(data)
                        
                        chunk_counter += 1

                        # --- C: Envia para a IA ---
                        await out_queue.put({"data": data, "mime_type": "audio/pcm"})

        except asyncio.CancelledError:
            print(" -> [AudioApp] Cancelado. Arquivos fechados com sucesso.")
        except Exception as e:
            print(f" -> [AudioApp] Erro fatal: {e}")

    def _setup_wav_header(self, wav_file):
        """Configura o cabeçalho WAV padrão para evitar repetição de código"""
        wav_file.setnchannels(Config.CHANNELS)
        wav_file.setsampwidth(2) # 16-bit PCM
        wav_file.setframerate(Config.RECEIVE_SAMPLE_RATE)

    def _flush_input_buffer(self):
        """Limpeza de buffer ao retomar pause"""
        try:
            available = self.audio_input_manager.input_stream.get_read_available()
            if available > 0:
                self.audio_input_manager.input_stream.read(available, exception_on_overflow=False)
        except:
            pass

    # ... (Restante dos métodos task_play_audio e play_file permanecem iguais)
    
    async def task_play_audio(self, input_queue: asyncio.Queue):
        self.audio_output_manager.start_output_stream()
        try:
            while True:
                bytestream = await input_queue.get()
                await asyncio.to_thread(self.audio_output_manager.write_chunk, bytestream)
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
        self.audio_input_manager.close()
        self.audio_output_manager.close()