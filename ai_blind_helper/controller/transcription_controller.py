import asyncio
import base64
import os
import time
import traceback
from application import TextToSpeechApplication, TranscriptionApplication
from event import (EventBus, TRANSCRIPTION_REQUEST)

class TranscriptionController:
    
    def __init__(self, video_app, gemini_client, transcription: TranscriptionApplication, state_provider, tts_app: TextToSpeechApplication, event_bus: EventBus):
        print("[TranscriptionController __init__] Inicializando controlador de transcrição")
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
        print("[TranscriptionController handle_transcription_request] Tecla 'R' detectada, iniciando processo de transcrição")
        
        if self.loop is None:
            print("[TranscriptionController handle_transcription_request] Erro: Loop de eventos não definido")
            return

        # if not self.gemini_client.is_connected:
        #     print("[TranscriptionController handle_transcription_request] Aviso: Cliente Gemini não está conectado")
        #     return

        print("[TranscriptionController handle_transcription_request] Disparando tarefa assíncrona _send_transcription_task")
        asyncio.run_coroutine_threadsafe(
            self._send_transcription_task(), self.loop)

    async def _send_transcription_task(self):
        print("[TranscriptionController _send_transcription_task] Iniciando captura de snapshot para transcrição")
        frame_data = await self.video_app.get_snapshot()

        if frame_data:
            try:
                os.makedirs("capturas", exist_ok=True)
                filename = f"capturas/snapshot_{int(time.time())}.jpg"
                b64_string = frame_data["data"]
                image_bytes = base64.b64decode(b64_string)
                
                with open(filename, "wb") as f:
                    f.write(image_bytes)
                print(f"[TranscriptionController _send_transcription_task] Imagem salva localmente em: {filename}")
            except Exception as e:
                print(f"[TranscriptionController _send_transcription_task] Erro ao salvar imagem: {e}")

            print("[TranscriptionController _send_transcription_task] Obtendo prompt e enviando payload para IA")
            prompt_text = self.transcription_app.get_prompt()

            try:
                response_text = self.gemini_client.generate_text_by_imagem_text(
                    prompt=prompt_text,
                    image_part_data=frame_data
                )
                print(f"[TranscriptionController _send_transcription_task] Resposta recebida da IA")
                print("\n\n>>> [Gemini Response] <<<")
                print(response_text)
                print(">>> ------------------- <<<")
                await self.tts_app.run_tts(response_text)
            except Exception as e:
                print(f"[TranscriptionController _send_transcription_task] Erro ao gerar texto via Gemini: {e}")
                traceback.print_exc()
        else:
            print("[TranscriptionController _send_transcription_task] Erro: Falha ao capturar frame (Câmera ocupada ou fechada)")