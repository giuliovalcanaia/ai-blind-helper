import asyncio
import base64
import time
import os
import traceback
from google.genai import types
from event import (EventBus, DESCRIPTION_REQUEST)

class DescritpionController:
    
    def __init__(self, video_app, description_app, state_provider, gemini_client, audio_in_queue, event_bus: EventBus):
        print(f"[DescritpionController __init__] Initializing description controller")
        self.video_app = video_app
        self.description_app = description_app
        self.gemini_client = gemini_client
        self.state_provider = state_provider
        
        print("[DescritpionController __init__] Initializing state variables and queues")
        self.input_queue = None
        self.session_task = None
        self.audio_in_queue = audio_in_queue

        print("[DescritpionController __init__] Initialization completed successfully")
        
        event_bus.subscribe(
            DESCRIPTION_REQUEST,
            self.handle_description_request
        )
        
    @property
    def loop(self):
        loop = self.state_provider.loop
        print(f"[DescritpionController loop] Getting loop: {loop}")
        return loop
    
    def handle_description_request(self):
        print("[DescritpionController handle_description_request] Key 'D' pressed - description request started")
        
        if self.loop is None:
            print("[DescritpionController handle_description_request] ERROR: Event loop not defined. Aborting action.")
            return

        print("[DescritpionController handle_description_request] Event loop ok, triggering _send_description_task")
        
        try:
            asyncio.run_coroutine_threadsafe(
                self._send_description_task(), self.loop)
            print("[DescritpionController handle_description_request] Task successfully submitted to loop")
        except Exception as e:
            print(f"[DescritpionController handle_description_request] FAILED to schedule task: {e}")

    async def _ensure_session_active(self):
        print("[DescritpionController _ensure_session_active] Checking Gemini session state")
        
        if self.gemini_client.is_connected:
            print("[DescritpionController _ensure_session_active] Session already active. No action needed.")
            return False
        
        print("[DescritpionController _ensure_session_active] Session not found. Creating new session...")
        try:
            await self.handle_connection()
            print("[DescritpionController _ensure_session_active] Session created successfully!")
            return True
        except Exception as e:
            print(f"[DescritpionController _ensure_session_active] ERROR starting session: {e}")
            traceback.print_exc()
            return False

    async def _send_description_task(self):
        print("[DescritpionController _send_description_task] Starting description task")
        
        created_new_session = await self._ensure_session_active()
        
        print("[DescritpionController _send_description_task] Requesting snapshot from video module")
        frame_data = await self.video_app.get_snapshot()
        
        if not frame_data:
            print("[DescritpionController _send_description_task] ERROR: Failed to capture frame (Camera unavailable)")
            return
        
        print("[DescritpionController _send_description_task] Frame received. Decoding...")
        
        try:
            # Decoding and local saving (kept for debugging)
            os.makedirs("capturas", exist_ok=True)
            filename = f"capturas/snapshot_{int(time.time())}.jpg"
            b64_string = frame_data["data"]
            image_bytes = base64.b64decode(b64_string)
            
            with open(filename, "wb") as f:
                f.write(image_bytes)
            print(f"[DescritpionController _send_description_task] Image saved at: {filename}")
            
            target_queue = self.input_queue if created_new_session else self.gemini_client.input_queue

            if target_queue:
                # 1. Send the image (as RealtimeInput / Media Chunk)
                print("[DescritpionController] Sending image to queue...")
                image_payload = {
                    "data": image_bytes,
                    "mime_type": "image/jpeg"
                }
                await target_queue.put(image_payload)

                # 2. Send the text (prompt)
                # The Live API accepts plain text strings directly as user input
                prompt_text = self.description_app.get_prompt()
                print(f"[DescritpionController] Sending prompt: {prompt_text}")
                await target_queue.put(prompt_text)
                
                print("[DescritpionController] Payload (Image + Text) sent successfully!")
            else:
                print("[DescritpionController] ERROR: No queue available for sending!")

        except Exception as e:
            print(f"[DescritpionController _send_description_task] FAILED during process: {e}")
            traceback.print_exc()

        print("[DescritpionController _send_description_task] Task finished")

    async def handle_connection(self):
        print("[DescritpionController handle_connection] Starting Gemini session setup...")

        if self.gemini_client.is_connected:
            print("[DescritpionController handle_connection] Session already active. Nothing to do.")
            return False
        
        print("[DescritpionController handle_connection] Creating internal queue for communication")
        self.input_queue = asyncio.Queue()
        
        print("[DescritpionController handle_connection] Opening session with Gemini...")
        try:
            self.session_task = asyncio.create_task(
                self.gemini_client.start_session(
                    input_queue=self.input_queue,
                    output_queue=self.audio_in_queue
                )
            )
            print("[DescritpionController handle_connection] Session initialized and task registered")
        except Exception as e:
                print(f"[DescritpionController handle_connection] ERROR starting session: {e}")

        return True

    def _close_session(self):
        print("[DescritpionController _close_session] Requesting session shutdown")

        if not self.session_task:
            print("[DescritpionController _close_session] No active session to close")
            return
        
        try:
            print("[DescritpionController _close_session] Canceling task and clearing queues")
            self.session_task.cancel()
            self.session_task = None
            self.input_queue = None
            print("[DescritpionController _close_session] Session closed successfully")
        except Exception as e:
            print(f"[DescritpionController _close_session] ERROR closing session: {e}")
            traceback.print_exc()
