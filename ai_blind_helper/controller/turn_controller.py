import asyncio
import os
import time
import base64
import traceback

class TurnController:
    
    def __init__(self, gemini_client, audio_app, session_task, out_queue, audio_in_queue, start_audio_event, state_provider, sfx_controller):
        print(f"[SessionController __init__] Inicializando controlador de sessão")
        self.session_task = session_task
        self.out_queue = out_queue
        self.audio_in_queue = audio_in_queue
        self.gemini_client = gemini_client
        self.audio_app = audio_app 
        self.start_audio_event = start_audio_event
        self.state_provider = state_provider
        self.sfx_controller = sfx_controller
        self.background_tasks = set()
        
        # --- Lógica de Turno (Flags) ---
        self.is_ai_talking = False  # Flag para controle de interrupção
    
    @property
    def loop(self):
        return self.state_provider.loop

    def _fire_and_forget_sfx(self, coro):
        task = asyncio.create_task(coro)
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)

    async def _orchestrate_audio_start(self):
        await self.sfx_controller.initiating_gemini_audio()
        await self._start_audio_connection_manager()

    async def _audio_capture_wrapper(self):
        print(f"[SessionController] Wrapper de áudio iniciado")
        await self.audio_app.task_capture_audio(self.out_queue, self.start_audio_event)
        
    async def _start_audio_connection_manager(self):
        self.session_task = asyncio.create_task(self._run_audio_session_lifecycle())

    async def _run_audio_session_lifecycle(self):
        print("[SessionController] Iniciando ciclo de vida de Áudio")
        try:
            self._fire_and_forget_sfx(self.sfx_controller.initiating_gemini_audio_sfx())
            
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.gemini_client.start_session(
                    input_queue=self.out_queue,
                    output_queue=self.audio_in_queue
                ))
                tg.create_task(self._audio_capture_wrapper())

        except asyncio.CancelledError:
            print("[SessionController] Sessão de áudio cancelada")
        except Exception as e:
            print(f"[SessionController] Erro na sessão: {e}")
        finally:
            self.is_ai_talking = False # Reset de turno ao finalizar
            print("[SessionController] Finalizando sessão e limpando áudios pendentes...")
            
            if hasattr(self.audio_app, 'drain_audio_queue'):
                self.audio_app.drain_audio_queue(self.audio_in_queue)

            self._fire_and_forget_sfx(self.sfx_controller.closing_gemini_audio_sfx())
            while not self.out_queue.empty():
                try: self.out_queue.get_nowait()
                except: pass

    def getWebSocketState(self):
        return self.gemini_client.is_connected()
    
    def stop_session(self):
        print("[SessionController stop_session] Solicitando parada imediata")
        if self.loop is None: return

        self.is_ai_talking = False # Usuário interrompeu ou sessão parou
        self.loop.call_soon_threadsafe(self.start_audio_event.clear)

        if hasattr(self.audio_app, 'drain_audio_queue'):
             self.loop.call_soon_threadsafe(
                 self.audio_app.drain_audio_queue, self.audio_in_queue
             )

        if self.session_task and not self.session_task.done():
            asyncio.run_coroutine_threadsafe(
                self._stop_session_task(), self.loop)

    async def _stop_session_task(self):
        if self.session_task:
            self.session_task.cancel()
            try:
                await self.session_task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                print(f"[SessionController] Erro ao cancelar: {e}")
            finally:
                self.session_task = None
        
        if hasattr(self.audio_app, 'drain_audio_queue'):
             self.audio_app.drain_audio_queue(self.audio_in_queue)
        
    def handle_audio_live_connect(self):
        if self.loop is None: return

        if self.session_task and not self.session_task.done():
            self.stop_session()
        else:
            self.is_ai_talking = False
            self.start_audio_event.clear()
            asyncio.run_coroutine_threadsafe(self._orchestrate_audio_start(), self.loop)

    def start_sending_audio_only(self):
        # Lógica de turno: Se a IA estiver falando, podemos implementar o "Barge-in" 
        # limpando a fila dela antes de abrir o mic do usuário
        if self.is_ai_talking:
            if hasattr(self.audio_app, 'drain_audio_queue'):
                self.audio_app.drain_audio_queue(self.audio_in_queue)
            self.is_ai_talking = False

        if hasattr(self.audio_app, 'reset_playback_state'):
            self.audio_app.reset_playback_state()
            
        self.loop.call_soon_threadsafe(self.start_audio_event.set)

    def stop_sending_audio(self):
        # Quando o usuário para de enviar áudio, a IA geralmente começa a processar/falar
        self.is_ai_talking = True 
        self.loop.call_soon_threadsafe(self.start_audio_event.clear)