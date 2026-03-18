import asyncio
import os
import time
import base64
import traceback
from event import (EventBus, SESSION_AUDIO_LIVE_CONNECT_TOGGLE, SESSION_STOP_AUDIO_STREAM, SESSION_VIDEO_LIVE_CONNECT_TOGGLE, SESSION_START_AUDIO_STREAM, SESSION_STOP)

class SessionController:
    
    def __init__(self, gemini_client, video_app, audio_app, session_task, out_queue, audio_in_queue, start_audio_event, start_video_event, state_provider, sfx_controller, event_bus: EventBus):
        print(f"[SessionController __init__] Initializing session controller")
        self.session_task = session_task
        self.out_queue = out_queue
        self.audio_in_queue = audio_in_queue
        self.gemini_client = gemini_client
        self.video_app = video_app
        self.audio_app = audio_app # Now we use methods from this app
        self.start_audio_event = start_audio_event
        self.start_video_event = start_video_event
        self.state_provider = state_provider
        self.sfx_controller = sfx_controller
        self.background_tasks = set()
        
        event_bus.subscribe(
            SESSION_AUDIO_LIVE_CONNECT_TOGGLE,
            self.handle_audio_live_connect
        )
        
        event_bus.subscribe(
            SESSION_VIDEO_LIVE_CONNECT_TOGGLE,
            self.handle_video_live_connect
        )
        
        event_bus.subscribe(
            SESSION_START_AUDIO_STREAM,
            self.start_sending_audio_only
        )
        
        event_bus.subscribe(
            SESSION_STOP_AUDIO_STREAM,
            self.stop_sending_audio
        )
        
        event_bus.subscribe(
            SESSION_STOP,
            self.stop_session
        )
    
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

    async def _orchestrate_video_start(self):
        await self.sfx_controller.initiating_gemini_video()
        await self._start_video_connection_manager()
    
    async def _audio_capture_wrapper(self):
        print(f"[SessionController] Audio wrapper started")
        await self.audio_app.task_capture_audio(self.out_queue, self.start_audio_event)
        
    async def _start_audio_connection_manager(self):
        self.session_task = asyncio.create_task(self._run_audio_session_lifecycle())

    async def _run_audio_session_lifecycle(self):
        print("[SessionController] Starting audio lifecycle")
        try:
            self._fire_and_forget_sfx(self.sfx_controller.initiating_gemini_audio_sfx())
            
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.gemini_client.start_session(
                    input_queue=self.out_queue,
                    output_queue=self.audio_in_queue
                ))
                tg.create_task(self._audio_capture_wrapper())

        except asyncio.CancelledError:
            print("[SessionController] Audio session cancelled")
        except Exception as e:
            print(f"[SessionController] Error in session: {e}")
        finally:
            # CRITICAL REAL-TIME CLEANUP
            print("[SessionController] Finalizing session and clearing pending audio...")
            
            # 1. Cala a boca da IA imediatamente (Drain)
            if hasattr(self.audio_app, 'drain_audio_queue'):
                self.audio_app.drain_audio_queue(self.audio_in_queue)

            # 2. SFX e limpeza de saida
            self._fire_and_forget_sfx(self.sfx_controller.closing_gemini_audio_sfx())
            while not self.out_queue.empty():
                try: self.out_queue.get_nowait()
                except: pass
                
    async def _video_capture_wrapper(self):
        print("[SessionController] Video wrapper started")
        await self.video_app.task_capture_video(self.out_queue, self.start_video_event)
        
    async def _start_video_connection_manager(self):
        self.session_task = asyncio.create_task(self._run_video_session_lifecycle())

    async def _run_video_session_lifecycle(self):
        print("[SessionController] Starting video lifecycle")
        try:
            self._fire_and_forget_sfx(self.sfx_controller.initiating_gemini_audio_sfx())
            
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.gemini_client.start_session(
                    input_queue=self.out_queue,
                    output_queue=self.audio_in_queue
                ))
                tg.create_task(self._audio_capture_wrapper())
                tg.create_task(self._video_capture_wrapper())

                self.start_sending_video()
        except asyncio.CancelledError:
            print("[SessionController] Video session cancelled")
        except Exception as e:
            print(f"[SessionController] Error in session: {e}")
        finally:
            # CRITICAL CLEANUP
            print("[SessionController] Finalizing video session...")
            
            # 1. Drain Audio
            if hasattr(self.audio_app, 'drain_audio_queue'):
                self.audio_app.drain_audio_queue(self.audio_in_queue)

            if hasattr(self.sfx_controller, 'closing_gemini_video_sfx'):
                 self._fire_and_forget_sfx(self.sfx_controller.closing_gemini_video_sfx())
            else:
                 self._fire_and_forget_sfx(self.sfx_controller.closing_gemini_audio_sfx())

            if hasattr(self.video_app, 'stop_capture'):
                await self.video_app.stop_capture() 
            elif hasattr(self.video_app, 'release'):
                 self.video_app.release()
            
            while not self.out_queue.empty():
                try: self.out_queue.get_nowait()
                except: pass
    
    def getWebSocketState(self):
        return self.gemini_client.is_connected()
    
    def stop_session(self):
        print("[SessionController stop_session] Requesting immediate stop")
        if self.loop is None: return

        # Para captura de input imediatamente
        self.loop.call_soon_threadsafe(self.start_audio_event.clear)
        self.loop.call_soon_threadsafe(self.start_video_event.clear)

        # INTERRUPTION (BARGE-IN): Clears any audio the AI sent but hasn't played yet
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
                print(f"[SessionController] Error cancelling: {e}")
            finally:
                self.session_task = None
        
        # Redundancy: Ensure queue is empty at the end
        if hasattr(self.audio_app, 'drain_audio_queue'):
             self.audio_app.drain_audio_queue(self.audio_in_queue)
        
    def handle_audio_live_connect(self):
        if self.loop is None: return

        if self.session_task and not self.session_task.done():
            self.stop_session()
        else:
            self.start_audio_event.clear()
            self.start_video_event.clear()
            asyncio.run_coroutine_threadsafe(self._orchestrate_audio_start(), self.loop)

    def handle_video_live_connect(self):
        if self.loop is None: return

        if self.session_task and not self.session_task.done():
            self.stop_session()
        else:
            self.start_audio_event.clear()
            self.start_video_event.clear()
            asyncio.run_coroutine_threadsafe(self._orchestrate_video_start(), self.loop)

    def start_sending_audio_only(self):
        if hasattr(self.audio_app, 'reset_buffer'):
            self.audio_app.reset_playback_state()
        self.loop.call_soon_threadsafe(self.start_audio_event.set)

    def start_sending_video(self):
        self.loop.call_soon_threadsafe(self.start_video_event.set)

    def stop_sending_audio(self):
        self.loop.call_soon_threadsafe(self.start_audio_event.clear)

    def stop_sending_video(self):
        self.loop.call_soon_threadsafe(self.start_video_event.clear)