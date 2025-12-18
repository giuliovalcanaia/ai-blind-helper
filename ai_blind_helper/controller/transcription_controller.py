import asyncio
import base64
import os
import time
import traceback

class TranscriptionController:
    
    def __init__(self, video_app, gemini_client, transcription, loop):
        self.loop = loop
        self.gemini_client = gemini_client
        self.video_app = video_app
        self.transcription_app = transcription
    
    
    def handle_transcription_request(self):
        """Tecla 'R': Reconhece texto e transcreve"""
        if self.loop is None:
            return

        if not self.gemini_client.is_connected:
            print("\n[Aviso] Conecte-se ao Gemini (Tecla W) antes.")
            return

        print("\n[Comando] Tecla 'R': Solicitando descrição...")

        # Dispara a tarefa assíncrona
        asyncio.run_coroutine_threadsafe(
            self._send_transcription_task(), self.loop)

    async def _send_transcription_task(self):
        """Lógica de envio do prompt + snapshot"""

        # 1. Pega o frame da VideoApp existente, já retorna em BLOB/Dict
        # ASSUMIMOS que `frame_data` é um dicionário:
        # {"data": "base64_blob_aqui", "mime_type": "image/jpeg"}
        frame_data = await self.video_app.get_snapshot()

        if frame_data:
            try:
                os.makedirs("capturas", exist_ok=True)
                filename = f"capturas/snapshot_{int(time.time())}.jpg"
                b64_string = frame_data["data"]
                image_bytes = base64.b64decode(b64_string)
                with open(filename, "wb") as f:
                    f.write(image_bytes)
                print(f"[System] Imagem salva localmente em: {filename}")
            except Exception as e:
                print(f"[Erro] Falha ao salvar imagem: {e}")
            # -------------------------------------

            print("[System] Frame capturado. Enviando payload formatado para IA...")

            prompt_text = self.transcription_app.get_prompt()

            # --- CORREÇÃO AQUI ---
            # Passando o dicionário completo `frame_data` (que tem 'data' e 'mime_type')
            try:
                response_text = self.txt_client_app.generate_text_by_imagem_text(
                    prompt=prompt_text,
                    image_part_data=frame_data  # Usando o nome do parâmetro da classe
                )
                print("\n\n>>> [Gemini Response] <<<")
                print(response_text)
                print(">>> ------------------- <<<")
                # Você pode adicionar a resposta para a fila de áudio se for um TTS, por exemplo
            except Exception as e:
                print(f"\n!!! [Gemini Error] Falha ao gerar texto: {e}")
                traceback.print_exc()

        else:
            print(
                "[Erro] Não foi possível capturar o frame (Câmera ocupada ou fechada).")