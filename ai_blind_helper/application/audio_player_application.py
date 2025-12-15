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

    async def play_file(self, file_path: str, target_queue: asyncio.Queue, loop):
        """Lê um arquivo WAV e injeta os chunks na fila de áudio para ser tocado"""
        def process_file():
            # Lê o arquivo e joga na fila usando threadsafe pois roda em thread
            for chunk in self.wav_reader.read_chunks(file_path):
                loop.call_soon_threadsafe(
                    target_queue.put_nowait, chunk)
        await asyncio.to_thread(process_file)

    async def task_capture_audio(self, out_queue: asyncio.Queue, control_event: asyncio.Event):
        """
        Lê do Mic continuamente.
        Se o botão A estiver ATIVO: Envia o som real.
        Se o botão A estiver INATIVO: Substitui por silêncio (0x00), mas continua enviando.
        """
        self.audio_input_manager.start_input_stream()
        print(" -> [AudioApp] Microfone Iniciado (Modo Always-On).")

        try:
            while True:
                # 1. LEITURA DO HARDWARE (Sempre executada)
                # É crucial ler mesmo quando "pausado" para manter o clock do hardware
                # e esvaziar o buffer do sistema operacional.
                data = await asyncio.to_thread(self.audio_input_manager.read_chunk)

                if data:
                    # 2. LÓGICA DO BOTÃO "A"
                    # Se o evento NÃO estiver setado (Botão desligado), forçamos silêncio.
                    if not control_event.is_set():
                        # Cria um bloco de bytes nulos do mesmo tamanho do chunk lido
                        data = b'\x00' * len(data)

                        # Opcional: Se quiser um debug visual para saber que está em "Mute Ativo"
                        # print(".", end="", flush=True)

                    # 3. ENVIO (Voz Real ou Silêncio Fabricado)
                    # O Gemini receberá o fluxo contínuo, mantendo a sessão estável.
                    await out_queue.put({"data": data, "mime_type": "audio/pcm"})

        except asyncio.CancelledError:
            print(" -> [AudioApp] Cancelado.")
        except Exception as e:
            print(f" -> [AudioApp] Erro fatal: {e}")

        except asyncio.CancelledError:
            print(" -> [AudioApp] Cancelado. Arquivos fechados com sucesso.")
        except Exception as e:
            print(f" -> [AudioApp] Erro fatal: {e}")

    def _setup_wav_header(self, wav_file):
        """Configura o cabeçalho WAV padrão para evitar repetição de código"""
        wav_file.setnchannels(Config.CHANNELS)
        wav_file.setsampwidth(2)  # 16-bit PCM
        wav_file.setframerate(Config.SEND_SAMPLE_RATE)

    def _flush_input_buffer(self):
        """Limpeza de buffer ao retomar pause"""
        try:
            available = self.audio_input_manager.input_stream.get_read_available()
            if available > 0:
                self.audio_input_manager.input_stream.read(
                    available, exception_on_overflow=False)
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

    def close(self):
        self.audio_input_manager.close()
        self.audio_output_manager.close()
