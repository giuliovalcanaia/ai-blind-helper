import asyncio
import traceback
from typing import Optional
from clock_service import ClockService
import wave  # Necessário para ler o arquivo wav corretamente se for PCM
from config import Config
from audio_service import AudioService
from gemini_client import GeminiClient
from video_sources import IVideoSource, CameraSource, ScreenSource
# ... outros imports
from wav_reader import WavReader  # <--- Importe a nova classe


class Application:
    def __init__(self, video_mode: str):
        self.video_mode = video_mode
        self.audio_service = AudioService()
        self.gemini_client = GeminiClient()

        self.audio_in_queue = asyncio.Queue()
        self.out_queue = asyncio.Queue(maxsize=5)

        self.video_source: Optional[IVideoSource] = None
        if video_mode == "camera":
            self.video_source = CameraSource()
        elif video_mode == "screen":
            self.video_source = ScreenSource()

        # Estado
        self.app_running = True
        self.session_task: Optional[asyncio.Task] = None
        # <--- Nova variável para guardar o loop
        self.loop: Optional[asyncio.AbstractEventLoop] = None

        # Relógio com idioma português
        self.clock_service = ClockService(language="pt")
        # Inicializa o Leitor com as configurações do SEU config.py
        self.wav_reader = WavReader(
            target_rate=Config.RECEIVE_SAMPLE_RATE,
            target_channels=Config.CHANNELS
        )
    # --- Callbacks do Teclado (Thread-Safe) ---

    def handle_toggle_connect(self):
        """Chamado pela Thread do Teclado."""
        if self.loop is None:
            print("Loop ainda não iniciado.")
            return

        # Precisamos agendar a execução na Thread Principal
        if self.session_task and not self.session_task.done():
            print("\n[Comando] Tecla V: Encerrando conexão...")
            # Thread-safe cancel: Agenda o cancelamento no loop principal
            self.loop.call_soon_threadsafe(self.session_task.cancel)
        else:
            print("\n[Comando] Tecla V: Iniciando conexão com Gemini...")
            # Thread-safe create: Agenda a criação da task no loop principal
            asyncio.run_coroutine_threadsafe(
                self._start_connection_task(), self.loop)

    def handle_quit(self):
        """Chamado pela Thread do Teclado."""
        print("\n[Comando] Tecla Q: Saindo...")
        self.app_running = False

        if self.session_task and not self.session_task.done() and self.loop:
            self.loop.call_soon_threadsafe(self.session_task.cancel)

    # --- Helper Interno para Criação de Task ---

    async def _start_connection_task(self):
        """Este método roda na MainThread, chamado pelo run_coroutine_threadsafe"""
        # Agora estamos no loop certo, podemos usar create_task
        self.session_task = asyncio.create_task(self._connect_and_stream())

    # --- Workers (Igual ao anterior) ---

    async def task_capture_video(self):
        if not self.video_source:
            return
        print(" -> Câmera Iniciada.")
        while True:
            frame_data = await asyncio.to_thread(self.video_source.get_frame)
            if frame_data is None:
                break

            if self.out_queue.full():
                try:
                    self.out_queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass

            await self.out_queue.put(frame_data)
            await asyncio.sleep(1.0)

    async def task_capture_audio(self):
        self.audio_service.start_input_stream()
        print(" -> Microfone Iniciado.")
        try:
            while True:
                data = await asyncio.to_thread(self.audio_service.read_chunk)
                await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})
        finally:
            pass

    async def task_play_audio(self):
        """
        Agora este worker roda o tempo todo.
        Ele consome qualquer coisa que cair na fila de áudio (seja da IA ou do Relógio).
        """
        print(" -> Sistema de Áudio Ativo (Aguardando som...)")
        self.audio_service.start_output_stream()
        try:
            while True:
                # O get() bloqueia a execução até chegar algo na fila
                bytestream = await self.audio_in_queue.get()
                await asyncio.to_thread(self.audio_service.write_chunk, bytestream)
        except asyncio.CancelledError:
            pass
        finally:
            # Só fecha o stream quando a aplicação inteira fechar
            pass

    async def task_sender_worker(self, session):
        while True:
            msg = await self.out_queue.get()
            await session.send(input=msg)

    async def task_receiver_worker(self, session):
        turn = session.receive()
        async for response in turn:
            if data := response.data:
                self.audio_in_queue.put_nowait(data)
            if text := response.text:
                print(text, end="", flush=True)

    # --- Lógica de Conexão ---

    async def _connect_and_stream(self):
        try:
            print(">>> Conectando ao Gemini...")
            async with (
                self.gemini_client.connect() as session,
                asyncio.TaskGroup() as tg
            ):
                print(">>> Conectado! Stream ativo.")
                tg.create_task(self.task_sender_worker(session))
                tg.create_task(self.task_capture_audio())
                tg.create_task(self.task_capture_video())
                tg.create_task(self.task_receiver_worker(session))

                # REMOVIDO: tg.create_task(self.task_play_audio())
                # O player de áudio agora é global e já está rodando!

        except asyncio.CancelledError:
            print("\n<<< Conexão interrompida.")
        except Exception as e:
            print(f"\n!!! Erro na sessão: {e}")
            traceback.print_exc()
        finally:
            print("<<< Limpando filas de sessão...")
            # CUIDADO: Não limpamos a audio_in_queue aqui violentamente,
            # pois pode ter um áudio de "Hora" tocando.
            pass

    async def play_current_time(self):
        """Busca o caminho do arquivo e inicia o streaming em background."""
        path = await asyncio.to_thread(self.clock_service.get_current_time_audio_path)

        if path:
            print(f" -> Anunciando hora: {path}")
            # Inicia a tarefa de ingestão de áudio sem travar o loop principal
            asyncio.create_task(self._ingest_file_audio(path))

    async def _ingest_file_audio(self, path):
        """
        Método interno que usa a classe WavReader para alimentar a fila.
        Roda em uma thread separada para não bloquear o AsyncIO com leitura de disco.
        """
        def process_file():
            # Itera sobre os pedaços (chunks) que o WavReader gera
            for chunk in self.wav_reader.read_chunks(path):
                # Coloca na fila de forma thread-safe
                self.loop.call_soon_threadsafe(
                    self.audio_in_queue.put_nowait, chunk)

        # Executa o loop de leitura/processamento fora da thread principal
        await asyncio.to_thread(process_file)

    # --- Loop Principal ---

    async def start_main_loop(self):
        self.loop = asyncio.get_running_loop()

        # INICIA O PLAYER DE ÁUDIO AQUI (GLOBAL)
        # Ele vai rodar em paralelo com o while loop abaixo
        self.audio_task = asyncio.create_task(self.task_play_audio())

        print("Aplicação pronta. Aguardando comandos (V=Connect, T=Time, Q=Quit)...")

        while self.app_running:
            await asyncio.sleep(0.5)

        print("Loop principal encerrado.")
        self.cleanup()

    def cleanup(self):
        print("Limpando recursos globais...")

        # Cancela o player de áudio global
        if hasattr(self, 'audio_task'):
            self.audio_task.cancel()

        self.audio_service.close()
        if self.video_source:
            self.video_source.release()
