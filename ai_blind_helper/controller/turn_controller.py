import asyncio
import traceback

class TurnController:
    def __init__(self, gemini_client, audio_app, session_task, out_queue, audio_in_queue, 
                 start_audio_event, state_provider, sfx_controller):
        print(f"[TurnController __init__] Inicializando controlador por turnos")
        
        self.gemini_client = gemini_client
        self.audio_app = audio_app
        self.session_task = session_task
        
        # Queues
        self.out_queue = out_queue          # O que vai para o Gemini
        self.audio_in_queue = audio_in_queue # O que vem do Gemini
        
        # Events & State
        self.start_audio_event = start_audio_event
        self.state_provider = state_provider
        self.sfx_controller = sfx_controller
        self.background_tasks = set()

    @property
    def loop(self):
        return self.state_provider.loop

    def _fire_and_forget_sfx(self, coro):
        task = asyncio.create_task(coro)
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)

    # --- CICLO DE VIDA DA SESSÃO ---

    async def _run_turn_session_lifecycle(self):
        """Gerencia a conexão WebSocket e os workers de áudio"""
        print("[TurnController] Iniciando ciclo de vida da sessão por TURNOS")
        try:
            self._fire_and_forget_sfx(self.sfx_controller.initiating_gemini_audio_sfx())
            
            async with asyncio.TaskGroup() as tg:
                # 1. Inicia o cliente Gemini (Sender e Receiver)
                tg.create_task(self.gemini_client.start_session(
                    input_queue=self.out_queue,
                    output_queue=self.audio_in_queue
                ))
                
                # 2. Inicia a captura de áudio (fica em wait até o event ser setado)
                tg.create_task(self._audio_capture_bridge())

        except asyncio.CancelledError:
            print("[TurnController] Sessão de turno cancelada")
        except Exception as e:
            print(f"[TurnController] Erro crítico na sessão de turno: {e}")
            traceback.print_exc()
        finally:
            print("[TurnController] Finalizando sessão e limpando filas")
            self._cleanup_session()

    def _cleanup_session(self):
        """Limpa as filas e toca SFX de encerramento"""
        if hasattr(self.audio_app, 'reset_playback_state'):
            self.audio_app.reset_playback_state()
        
        self._fire_and_forget_sfx(self.sfx_controller.closing_gemini_audio_sfx())
        
        # Limpa fila de saída
        while not self.out_queue.empty():
            try: self.out_queue.get_nowait()
            except: pass

    # --- CONTROLE DE TURNOS (AÇÕES DO USUÁRIO) ---

    def start_recording(self):
        """Ativa a captura de áudio do microfone"""
        print("🎙️ [TurnController] Iniciando gravação do turno...")
        if self.loop is None: return
        
        self.loop.call_soon_threadsafe(self.start_audio_event.set)

    def stop_recording_and_send(self):
        """Para a captura e envia a flag de fim de turno para o Gemini processar"""
        print("📤 [TurnController] Parando gravação e enviando flag de processamento...")
        if self.loop is None: return

        # 1. Para a captura imediatamente
        self.loop.call_soon_threadsafe(self.start_audio_event.clear)

        # 2. Envia a flag "mágica" para a fila que o TurnClientApplication._sender consome
        # Note que usamos 'msg': None ou b'' para não enviar lixo, apenas a flag eot
        asyncio.run_coroutine_threadsafe(
            self.out_queue.put({"msg": None, "end_of_turn": True}), 
            self.loop
        )

    # --- WRAPPERS E AUXILIARES ---

    async def _audio_capture_bridge(self):
        """
        Faz a ponte entre o AudioPlayerApplication (que gera 'data') 
        e o TurnClientApplication (que espera 'msg')
        """
        # Criamos uma fila interna temporária para o capture_audio original
        internal_audio_q = asyncio.Queue()
        
        # Inicia a task de captura do seu AudioApp
        capture_task = asyncio.create_task(
            self.audio_app.task_capture_audio(internal_audio_q, self.start_audio_event)
        )

        try:
            while True:
                # Pega o áudio bruto do hardware
                audio_item = await internal_audio_q.get()
                audio_data = audio_item.get("data")

                if audio_data:
                    # Formata para o padrão que o seu TurnClientApplication._sender espera
                    await self.out_queue.put({
                        "msg": audio_data,
                        "end_of_turn": False
                    })
                
                internal_audio_q.task_done()
        except asyncio.CancelledError:
            capture_task.cancel()

    def handle_toggle_session(self):
        """Liga ou desliga a conexão WebSocket com o Gemini de forma segura entre threads"""
        if self.loop is None: 
            print("❌ [TurnController] Loop não inicializado.")
            return

        if self.session_task and not self.session_task.done():
            print("[TurnController] Parando sessão ativa...")
            # Para cancelar de outra thread, usamos call_soon_threadsafe
            self.loop.call_soon_threadsafe(self.session_task.cancel)
        else:
            print("[TurnController] Iniciando nova sessão...")
            self.start_audio_event.clear()
            
            # CORREÇÃO AQUI: run_coroutine_threadsafe agenda a corotina no loop correto
            # e retorna um Future. Armazenamos a task para controle futuro.
            future = asyncio.run_coroutine_threadsafe(
                self._run_turn_session_lifecycle(), 
                self.loop
            )
            
            # Para manter compatibilidade com seu check 'self.session_task.done()'
            # Podemos extrair a Task real do loop se necessário, ou apenas gerenciar o future.
            self.session_task = future 