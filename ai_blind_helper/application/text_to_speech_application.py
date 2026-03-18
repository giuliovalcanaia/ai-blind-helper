import asyncio
import traceback
from google import genai
from config import Config

class TextToSpeechApplication:
    def __init__(self, audio_output_queue: asyncio.Queue):
        """
        Initializes the client for Text-to-Speech.
        :param audio_output_queue: The queue where audio chunks (bytes) should be placed for playback.
        """
        print("[TextToSpeechApplication __init__] Initializing Gemini client for TTS")
        self.client = genai.Client(api_key=Config.API_KEY)
        self.audio_output_queue = audio_output_queue

    async def run_tts(self, text: str):
        """
        Generates audio from text and puts the raw data into the output queue.
        """
        if not text:
            print("[TextToSpeechApplication run_tts] Warning: Empty text received, ignoring.")
            return

        print(f"[TextToSpeechApplication run_tts] Starting audio generation for: '{text[:50]}...'")

        try:
            # Call the API asynchronously to avoid blocking the main loop
            response = await self.client.aio.models.generate_content(
                model=Config.TTS_MODEL,
                contents=text,
                config=Config.TTS_CONFIG
            )

            # Access binary data according to the provided functional example
            # Path: candidates -> content -> parts -> inline_data -> data
            if response.candidates and response.candidates[0].content.parts:
                part = response.candidates[0].content.parts[0]
                
                if part.inline_data and part.inline_data.data:
                    audio_data = part.inline_data.data
                    size = len(audio_data)
                    
                    print(f"[TextToSpeechApplication run_tts] Audio generated successfully ({size} bytes). Sending to queue.")
                    
                    # Coloca os bytes na fila para o player consumir (ex: PyAudio ou similar)
                    self.audio_output_queue.put_nowait(audio_data)
                else:
                    print("[TextToSpeechApplication run_tts] Error: API response does not contain audio data (inline_data).")
            else:
                print("[TextToSpeechApplication run_tts] Error: Invalid response candidates structure.")

        except Exception as e:
            print(f"[TextToSpeechApplication run_tts] Critical error generating TTS: {e}")
            traceback.print_exc()