import asyncio
import os
import time
import base64
import traceback

class SessionController:
    
    def __init__(self, gemini_client, video_app, audio_app, session_task, out_queue, audio_in_queue, start_audio_event, start_video_event, state_provider, sfx_controller):
        print(f"[SessionController __init__] Inicializando controlador de sessão")
        self.session_task = session_task
        self.out_queue = out_queue
        self.audio_in_queue = audio_in_queue
        self.gemini_client = gemini_client
        self.video_app = video_app
        self.audio_app = audio_app
        self.start_audio_event = start_audio_event
        self.start_video_event = start_video_event
        # self.loop = loop
        self.state_provider = state_provider
        self.sfx_controller = sfx_controller
    
    @property
    def loop(self):
        return self.state_provider.loop
    
    
    async def _audio_capture_wrapper(self):
        print(f"[SessionController _audio_capture_wrapper] Inicializando loop de áudio (Event ID: {id(self.start_audio_event)})")
        await self.audio_app.task_capture_audio(self.out_queue, self.start_audio_event)
        
    async def _start_audio_connection_manager(self):
        print("[SessionController _start_audio_connection_manager] Criando tarefa para ciclo de vida de áudio")
        self.session_task = asyncio.create_task(self._run_audio_session_lifecycle())

    async def _run_audio_session_lifecycle(self):
        print("[SessionController _run_audio_session_lifecycle] WebSocket Conectado. Iniciando TaskGroup de áudio")
        try:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.gemini_client.start_session(
                    input_queue=self.out_queue,
                    output_queue=self.audio_in_queue
                ))
                tg.create_task(self._audio_capture_wrapper())

        except asyncio.CancelledError:
            print("[SessionController _run_audio_session_lifecycle] Sessão de áudio cancelada")
        except Exception as e:
            print(f"[SessionController _run_audio_session_lifecycle] Erro na sessão: {e}")
        finally:
            print("[SessionController _run_audio_session_lifecycle] Limpando fila de saída")
            while not self.out_queue.empty():
                try:
                    self.out_queue.get_nowait()
                except:
                    pass
                
    async def _video_capture_wrapper(self):
        print("[SessionController _video_capture_wrapper] Inicializando loop de vídeo")
        await self.video_app.task_capture_video(self.out_queue, self.start_video_event)
        
    async def _start_video_connection_manager(self):
        print("[SessionController _start_video_connection_manager] Criando tarefa para ciclo de vida de vídeo")
        self.session_task = asyncio.create_task(self._run_video_session_lifecycle())

    async def _run_video_session_lifecycle(self):
        print("[SessionController _run_video_session_lifecycle] WebSocket Conectado. Iniciando TaskGroup de áudio e vídeo")
        try:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.gemini_client.start_session(
                    input_queue=self.out_queue,
                    output_queue=self.audio_in_queue
                ))
                tg.create_task(self._audio_capture_wrapper())
                tg.create_task(self._video_capture_wrapper())

                self.start_sending_video()
        except asyncio.CancelledError:
            print("[SessionController _run_video_session_lifecycle] Sessão de vídeo cancelada")
        except Exception as e:
            print(f"[SessionController _run_video_session_lifecycle] Erro na sessão: {e}")
        finally:
            print("[SessionController _run_video_session_lifecycle] Limpando fila de saída")
            if hasattr(self.video_app, 'stop_capture'):
                await self.video_app.stop_capture() 
            elif hasattr(self.video_app, 'release'):
                 self.video_app.release()
            while not self.out_queue.empty():
                try:
                    self.out_queue.get_nowait()
                except:
                    pass
    
    def getWebSocketState(self):
        state = self.gemini_client.is_connected()
        print(f"[SessionController getWebSocketState] Estado atual: {state}")
        return state
    
    def stop_session(self):
        print("[SessionController stop_session] Solicitando encerramento gracioso da sessão")
        if self.loop is None:
            print("[SessionController stop_session] Erro: Loop não disponível")
            return

        self.loop.call_soon_threadsafe(self.start_audio_event.clear)
        self.loop.call_soon_threadsafe(self.start_video_event.clear)

        if self.session_task and not self.session_task.done():
            asyncio.run_coroutine_threadsafe(
                self._stop_session_task(), self.loop)

    async def _stop_session_task(self):
        print("[SessionController _stop_session_task] Iniciando parada assíncrona")
        if self.session_task:
            self.session_task.cancel()
            try:
                await self.session_task
            except asyncio.CancelledError:
                print("[SessionController _stop_session_task] TaskGroup cancelada com sucesso")
            except Exception as e:
                print(f"[SessionController _stop_session_task] Erro ao cancelar: {e}")
            finally:
                self.session_task = None

        purged_count = 0
        while not self.audio_in_queue.empty():
            try:
                self.audio_in_queue.get_nowait()
                purged_count += 1
            except asyncio.QueueEmpty:
                break

        print(f"[SessionController _stop_session_task] Sessão encerrada. Itens de áudio removidos: {purged_count}")
        
    def handle_audio_live_connect(self):
        print("[SessionController handle_audio_live_connect] Processando solicitação de conexão de áudio")
        if self.loop is None:
            print("SessionController handle_audio_live_connect] Loop é None")
            return

        if self.session_task and not self.session_task.done():
            print("[SessionController handle_audio_live_connect] Sessão ativa detectada, encerrando...")
            asyncio.run_coroutine_threadsafe(self.sfx_controller.closing_gemini_audio(), self.loop)
            self.stop_session()
        else:
            print("[SessionController handle_audio_live_connect] Iniciando nova conexão...")
            self.start_audio_event.clear()
            self.start_video_event.clear()
            asyncio.run_coroutine_threadsafe(self.sfx_controller.initiating_gemini_audio(), self.loop)
            asyncio.run_coroutine_threadsafe(self._start_audio_connection_manager(), self.loop)

    def handle_video_live_connect(self):
        print("[SessionController handle_video_live_connect] Processando solicitação de conexão de vídeo")
        if self.loop is None:
            return

        if self.session_task and not self.session_task.done():
            print("[SessionController handle_video_live_connect] Sessão ativa detectada, encerrando...")
            asyncio.run_coroutine_threadsafe(self.sfx_controller.closing_gemini_video(), self.loop)
            self.stop_session()
        else:
            print("[SessionController handle_video_live_connect] Iniciando nova conexão...")
            self.start_audio_event.clear()
            self.start_video_event.clear()
            asyncio.run_coroutine_threadsafe(self.sfx_controller.initiating_gemini_video(), self.loop)
            asyncio.run_coroutine_threadsafe(self._start_video_connection_manager(), self.loop)

    def start_sending_audio_only(self):
        print("[SessionController start_sending_audio_only] Ativando fluxo de áudio")
        if hasattr(self.audio_app, 'reset_buffer'):
            self.audio_app.reset_playback_state()
        self.loop.call_soon_threadsafe(self.start_audio_event.set)

    def start_sending_video(self):
        print("[SessionController start_sending_video] Ativando fluxo de vídeo")
        self.loop.call_soon_threadsafe(self.start_video_event.set)

    def stop_sending_audio(self):
        print("[SessionController stop_sending_audio] Pausando fluxo de áudio")
        self.loop.call_soon_threadsafe(self.start_audio_event.clear)

    def stop_sending_video(self):
        print("[SessionController stop_sending_video] Pausando fluxo de vídeo")
        self.loop.call_soon_threadsafe(self.start_video_event.clear)