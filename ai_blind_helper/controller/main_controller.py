import asyncio
from typing import Optional
from config import Config

# Seus imports de aplicação
from application import (
    ClockApplication, 
    LiveClientApplication, 
    AudioPlayerApplication, 
    VideoPlayerApplication,
    KeyboardApplication
)

class MainController:
    def __init__(self, video_mode):
        # 1. Instanciação dos Sub-Sistemas
        self.clock_service = ClockApplication(language="pt")
        self.gemini_client = LiveClientApplication()
        
        # Audio e Video
        self.audio_app = AudioPlayerApplication()
        self.video_app = VideoPlayerApplication(mode=video_mode)

        # Teclado
        self.keyboard_app = KeyboardApplication(controller=self, device_path=Config.KEYBOARD_PATH)

        # 2. Filas de comunicação
        self.audio_in_queue = asyncio.Queue()     # Recebe do Gemini
        self.out_queue = asyncio.Queue(maxsize=5) # Envia para o Gemini

        # 3. Estado e Controle
        self.app_running = True
        self.session_task: Optional[asyncio.Task] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.audio_playback_task: Optional[asyncio.Task] = None

        # --- NOVOS EVENTOS DE CONTROLE ---
        # Funcionam como "portões". Enquanto não forem ativados (.set()), 
        # a captura não envia dados.
        self.start_audio_event = asyncio.Event()
        self.start_video_event = asyncio.Event()

    # --- PONTO DE ENTRADA ---
    def run(self):
        try:
            asyncio.run(self.start_main_loop())
        except KeyboardInterrupt:
            print("\n[Sistema] Interrupção detectada (CTRL+C).")
        finally:
            self.cleanup()

    # --- Callbacks do Teclado ---

    def handle_toggle_connect(self):
        """
        1. Conecta no WebSocket.
        2. NÃO inicia o envio de áudio/vídeo ainda (ficam aguardando).
        """
        if self.loop is None: return

        if self.session_task and not self.session_task.done():
            print("\n[Comando] Tecla 'I': Encerrando conexão...")
            self.stop_session()
        else:
            print("\n[Comando] Tecla 'I': Conectando WebSocket (Aguardando comando de mídia)...")
            # Reseta os eventos para garantir que comecem travados
            self.start_audio_event.clear()
            self.start_video_event.clear()
            
            asyncio.run_coroutine_threadsafe(self._start_connection_manager(), self.loop)

    def handle_quit(self):
        print("\n[Comando] Tecla Q: Saindo...")
        self.app_running = False
        self.stop_session()

    def handle_time_request(self, duration=0):
        if self.loop is None: return
        print(f"[Comando] Tecla T: Hora ({duration:.2f}s)")
        asyncio.run_coroutine_threadsafe(self.play_current_time(), self.loop)

    # --- MÉTODOS DE CONTROLE DE FLUXO (ATUALIZADOS) ---

    def start_sending_audio_only(self):
        """Libera o fluxo de áudio."""
        print(">>> ATIVANDO: Apenas Áudio")
        self.loop.call_soon_threadsafe(self.start_audio_event.set)
        # Opcional: Se quiser garantir que o vídeo pare ao ligar só áudio:
        # self.loop.call_soon_threadsafe(self.start_video_event.clear) 

    def start_sending_audio_video(self):
        """Libera o fluxo de áudio E vídeo."""
        print(">>> ATIVANDO: Áudio + Vídeo")
        self.loop.call_soon_threadsafe(self.start_audio_event.set)
        self.loop.call_soon_threadsafe(self.start_video_event.set)

    def stop_sending_audio(self):
        """Pausa o envio de áudio (Hardware continua ligado, mas loop trava)."""
        print(">>> PAUSANDO: Áudio")
        self.loop.call_soon_threadsafe(self.start_audio_event.clear)

    def stop_sending_video(self):
        """Pausa o envio de vídeo (Hardware continua ligado, mas loop trava)."""
        print(">>> PAUSANDO: Vídeo")
        self.loop.call_soon_threadsafe(self.start_video_event.clear)

    def stop_all_sending(self):
        """Pausa tudo (modo mute/privacidade)."""
        print(">>> PAUSANDO: Tudo")
        self.stop_sending_audio()
        self.stop_sending_video()

    # --- Gerenciamento da Sessão (Modificado) ---

    async def _start_connection_manager(self):
        self.session_task = asyncio.create_task(self._run_session_lifecycle())

    async def _run_session_lifecycle(self):
        try:
            print(">>> WebSocket Conectado. Aguardando ativação de stream...")
            
            async with asyncio.TaskGroup() as tg:
                # 1. Inicia o WebSocket Client imediatamente (ele fica conectado esperando dados)
                tg.create_task(self.gemini_client.start_session(
                    input_queue=self.out_queue,
                    output_queue=self.audio_in_queue
                ))

                # 2. Inicia os wrappers de captura (que vão esperar os eventos)
                tg.create_task(self._audio_capture_wrapper())
                tg.create_task(self._video_capture_wrapper())

        except asyncio.CancelledError:
            print(">>> Sessão encerrada.")
        except Exception as e:
            print(f"Erro na sessão: {e}")
        finally:
            # Limpeza
            while not self.out_queue.empty():
                try: self.out_queue.get_nowait()
                except: pass





    # --- WRAPPERS (MODIFICADOS) ---
    
    # A MUDANÇA CRUCIAL ESTÁ AQUI: 
    # Passamos o evento para dentro da task, em vez de esperar por ele fora.

    async def _audio_capture_wrapper(self):
        print(">>> Inicializando loop de áudio (Aguardando flag...).")
        print(f"DEBUG: Controller Event ID: {id(self.start_audio_event)}")
        # Passamos o próprio evento (self.start_audio_event) para a função de captura
        await self.audio_app.task_capture_audio(self.out_queue, self.start_audio_event)

    async def _video_capture_wrapper(self):
        print(">>> Inicializando loop de vídeo (Aguardando flag...).")
        # Passamos o próprio evento (self.start_video_event) para a função de captura
        await self.video_app.task_capture_video(self.out_queue, self.start_video_event)
        
        
        
        

    # --- Funcionalidades Extras (Mantidas) ---
    async def play_current_time(self):
        path = await asyncio.to_thread(self.clock_service.get_current_time_audio_path)
        if path:
            asyncio.create_task(self.audio_app.play_file(path, self.audio_in_queue, self.loop))

    async def start_main_loop(self):
        self.loop = asyncio.get_running_loop()
        print("[Sistema] Iniciando monitor de teclado...")
        self.keyboard_app.start()

        self.audio_playback_task = asyncio.create_task(
            self.audio_app.task_play_audio(self.audio_in_queue)
        )

        print("=== Aplicação Pronta ===")
        print(" [I] Conectar WebSocket (Idle)")
        print(" [A] Iniciar captura de áudio")
        print(" [V] Iniciar captura de áudio e vídeo") 
        print(" [T] Falar horas")
        print(" [Q] Sair (hardware off)")
        
        while self.app_running:
            await asyncio.sleep(0.5)
        print("[Sistema] Loop encerrado.")

    def cleanup(self):
        if hasattr(self, 'keyboard_app'): self.keyboard_app.stop()
        if hasattr(self, 'audio_app'): self.audio_app.close()
        if hasattr(self, 'video_app'): self.video_app.release()
    
    def getWebSocketState(self):
        return self.gemini_client.is_connected()