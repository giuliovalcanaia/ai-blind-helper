
import asyncio

class SessionController:
    
    
    def __init__(self, gemini_client, video_app, audio_app, session_task, out_queue, audio_in_queue, start_audio_event, start_video_event, loop):
        self.session_task = session_task
        self.out_queue = out_queue
        self.audio_in_queue = audio_in_queue
        self.gemini_client = gemini_client
        self.video_app = video_app
        self.audio_app = audio_app
        self.start_audio_event = start_audio_event
        self.start_video_event = start_video_event
        self.loop = loop
    
    
    async def _audio_capture_wrapper(self):
        print(">>> Inicializando loop de áudio (Aguardando flag...).")
        print(f"DEBUG: Controller Event ID: {id(self.start_audio_event)}")
        # Passamos o próprio evento (self.start_audio_event) para a função de captura
        await self.audio_app.task_capture_audio(self.out_queue, self.start_audio_event)
        
    async def _start_audio_connection_manager(self):
        self.session_task = asyncio.create_task(self._run_audio_session_lifecycle())

    async def _run_audio_session_lifecycle(self):
        try:
            print(">>> WebSocket Conectado. Aguardando ativação de stream...")

            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.gemini_client.start_session(
                    input_queue=self.out_queue,
                    output_queue=self.audio_in_queue
                ))

                # 2. Wrappers de captura (Loops de monitoramento)
                tg.create_task(self._audio_capture_wrapper())


        except asyncio.CancelledError:
            print(">>> Sessão encerrada.")
        except Exception as e:
            print(f"Erro na sessão: {e}")
        finally:
            # Limpeza da fila de saída
            while not self.out_queue.empty():
                try:
                    self.out_queue.get_nowait()
                except:
                    pass
                
                
                
    async def _video_capture_wrapper(self):
        
        
        print(">>> Inicializando loop de vídeo (Aguardando flag...).")
        # Passamos o próprio evento (self.start_video_event) para a função de captura
        await self.video_app.task_capture_video(self.out_queue, self.start_video_event)
        
        
    async def _start_video_connection_manager(self):
        self.session_task = asyncio.create_task(self._run_video_session_lifecycle())
        

    async def _run_video_session_lifecycle(self):
        try:
            print(">>> WebSocket Conectado. Aguardando ativação de stream...")

            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.gemini_client.start_session(
                    input_queue=self.out_queue,
                    output_queue=self.audio_in_queue
                ))

                # 2. Wrappers de captura (Loops de monitoramento)
                tg.create_task(self._audio_capture_wrapper())
                tg.create_task(self._video_capture_wrapper())

                self.start_sending_video()
        except asyncio.CancelledError:
            print(">>> Sessão encerrada.")
        except Exception as e:
            print(f"Erro na sessão: {e}")
        finally:
            # Limpeza da fila de saída
            while not self.out_queue.empty():
                try:
                    self.out_queue.get_nowait()
                except:
                    pass
                
    
    def getWebSocketState(self):
        return self.gemini_client.is_connected()
    
    
    def stop_session(self):
        """
        Método síncrono chamado pelo Teclado (handle_toggle_connect) ou shutdown.
        Agenda a parada graciosa no Event Loop principal.
        """
        if self.loop is None:
            return

        print(">>> [Stop] Solicitando encerramento da sessão...")

        # 1. Trava capturas imediatamente (Thread-safe)
        self.loop.call_soon_threadsafe(self.start_audio_event.clear)
        self.loop.call_soon_threadsafe(self.start_video_event.clear)

        # 2. Agenda a corrotina de limpeza
        if self.session_task and not self.session_task.done():
            asyncio.run_coroutine_threadsafe(
                self._stop_session_task(), self.loop)

    async def _stop_session_task(self):
        """
        Lógica assíncrona real de parada.
        Cancela a TaskGroup e limpa resíduos de áudio.
        """
        if self.session_task:
            print(">>> [Stop] Cancelando TaskGroup da sessão...")
            self.session_task.cancel()
            try:
                # Aguarda o cancelamento propagar (vai disparar CancelledError no _run_session_lifecycle)
                await self.session_task
            except asyncio.CancelledError:
                # O erro é esperado aqui, pois acabamos de cancelar
                pass
            except Exception as e:
                print(f"[Erro] Falha ao aguardar cancelamento: {e}")
            finally:
                self.session_task = None

        # 3. Limpeza de filas (Opcional, mas recomendado)
        # Evita que áudio antigo toque quando você conectar novamente
        purged_count = 0
        while not self.audio_in_queue.empty():
            try:
                self.audio_in_queue.get_nowait()
                purged_count += 1
            except asyncio.QueueEmpty:
                break

        if purged_count > 0:
            print(f">>> [Limpeza] {
                  purged_count} itens de áudio removidos da fila.")

        print(">>> [Stop] Sessão encerrada e limpa.")
        
    def handle_audio_live_connect(self):
        print("Conectando com o Websocket para comunicação somente de áudio")
        if self.loop is None:
            return

        if self.session_task and not self.session_task.done():
            print("\n[Comando] Tecla 'W': Encerrando conexão...")
            self.stop_session()
        else:
            print("\n[Comando] Tecla 'W': Conectando WebSocket...")
            # Garante que começa travado
            self.start_audio_event.clear()
            self.start_video_event.clear()

            asyncio.run_coroutine_threadsafe(
                self._start_audio_connection_manager(), self.loop)

    

    async def _video_capture_wrapper(self):
        print(">>> Inicializando loop de vídeo (Aguardando flag...).")
        # Passamos o próprio evento (self.start_video_event) para a função de captura
        await self.video_app.task_capture_video(self.out_queue, self.start_video_event)
        
        
    async def _start_video_connection_manager(self):
        self.session_task = asyncio.create_task(self._run_video_session_lifecycle())
        

    async def _run_video_session_lifecycle(self):
        try:
            print(">>> WebSocket Conectado. Aguardando ativação de stream...")

            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.gemini_client.start_session(
                    input_queue=self.out_queue,
                    output_queue=self.audio_in_queue
                ))

                # 2. Wrappers de captura (Loops de monitoramento)
                tg.create_task(self._audio_capture_wrapper())
                tg.create_task(self._video_capture_wrapper())

                self.start_sending_video()
        except asyncio.CancelledError:
            print(">>> Sessão encerrada.")
        except Exception as e:
            print(f"Erro na sessão: {e}")
        finally:
            # Limpeza da fila de saída
            while not self.out_queue.empty():
                try:
                    self.out_queue.get_nowait()
                except:
                    pass
                
                
    def start_sending_audio_only(self):
        """Libera o fluxo de áudio."""
        print(">>> ATIVANDO: Apenas Áudio")
        if hasattr(self.audio_app, 'reset_buffer'):
            self.audio_app.reset_playback_state()
        self.loop.call_soon_threadsafe(self.start_audio_event.set)
        # Opcional: Se quiser garantir que o vídeo pare ao ligar só áudio:
        # self.loop.call_soon_threadsafe(self.start_video_event.clear)

    def start_sending_video(self):
        """Libera o fluxo de áudio E vídeo."""
        print(">>> ATIVANDO: Vídeo")
        self.loop.call_soon_threadsafe(self.start_video_event.set)

    def stop_sending_audio(self):
        """Pausa o envio de áudio (Hardware continua ligado, mas loop trava)."""
        print(">>> PAUSANDO: Áudio")
        self.loop.call_soon_threadsafe(self.start_audio_event.clear)

    def stop_sending_video(self):
        """Pausa o envio de vídeo (Hardware continua ligado, mas loop trava)."""
        print(">>> PAUSANDO: Vídeo")
        self.loop.call_soon_threadsafe(self.start_video_event.clear)