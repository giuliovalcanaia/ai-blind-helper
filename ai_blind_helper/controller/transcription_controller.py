import asyncio
import base64
import os
import time
import traceback
from application import TextToSpeechApplication, TranscriptionApplication
from event import (EventBus, TRANSCRIPTION_REQUEST)

class TranscriptionController:
    
    def __init__(self, video_app, gemini_client, transcription: TranscriptionApplication, state_provider, tts_app: TextToSpeechApplication, event_bus: EventBus):
        print("[TranscriptionController __init__] Initializing transcription controller")
        self.gemini_client = gemini_client
        self.video_app = video_app
        self.transcription_app = transcription
        self.state_provider = state_provider
        self.tts_app = tts_app
        
        event_bus.subscribe(
            TRANSCRIPTION_REQUEST,
            self.handle_transcription_request
        )

    @property
    def loop(self):
        return self.state_provider.loop
    
    def handle_transcription_request(self):
        print("[TranscriptionController handle_transcription_request] Key 'R' detected, starting transcription process")
        
        if self.loop is None:
            print("[TranscriptionController handle_transcription_request] Error: Event loop not defined")
            return

        # if not self.gemini_client.is_connected:
        #     print("[TranscriptionController handle_transcription_request] Warning: Gemini client is not connected")
        #     return

        print("[TranscriptionController handle_transcription_request] Triggering asynchronous task _send_transcription_task")
        asyncio.run_coroutine_threadsafe(
            self._send_transcription_task(), self.loop)

    async def _send_transcription_task(self):
        print("[TranscriptionController _send_transcription_task] Starting snapshot capture for transcription")
        frame_data = await self.video_app.get_snapshot()

        if frame_data:
            try:
                os.makedirs("capturas", exist_ok=True)
                filename = f"capturas/snapshot_{int(time.time())}.jpg"
                b64_string = frame_data["data"]
                image_bytes = base64.b64decode(b64_string)
                
                with open(filename, "wb") as f:
                    f.write(image_bytes)
                print(f"[TranscriptionController _send_transcription_task] Image saved locally at: {filename}")
            except Exception as e:
                print(f"[TranscriptionController _send_transcription_task] Error saving image: {e}")

            print("[TranscriptionController _send_transcription_task] Getting prompt and sending payload to AI")
            prompt_text = self.transcription_app.get_prompt()

            try:
                response_text = self.gemini_client.generate_text_by_imagem_text(
                    prompt=prompt_text,
                    image_part_data=frame_data
                )
                print(f"[TranscriptionController _send_transcription_task] Response received from AI")
                print("\n\n>>> [Gemini Response] <<<")
                print(response_text)
                print(">>> ------------------- <<<")
                await self.tts_app.run_tts(response_text)
            except Exception as e:
                print(f"[TranscriptionController _send_transcription_task] Error generating text via Gemini: {e}")
                traceback.print_exc()
        else:
            print("[TranscriptionController _send_transcription_task] Error: Failed to capture frame (Camera busy or closed)")