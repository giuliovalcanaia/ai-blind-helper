import asyncio
import base64
import time
import os
import traceback

class DescritpionController:
    
    def __init__(self, video_app, description_app, state_provider, gemini_client):
        print(f"[DescritpionController __init__] Inicializando controlador de descrição")
        self.video_app = video_app
        self.description_app = description_app
        self.gemini_client = gemini_client
        self.state_provider = state_provider
        
    @property
    def loop(self):
        return self.state_provider.loop
    
    def handle_description_request(self):
        print("[DescritpionController handle_description_request] Tecla 'D' detectada, iniciando processo de descrição")
        
        if self.loop is None:
            print("[DescritpionController handle_description_request] Erro: Loop de eventos não definido")
            return

        if not self.gemini_client.is_connected:
            print("[DescritpionController handle_description_request] Aviso: Cliente Gemini não está conectado")
            return

        print("[DescritpionController handle_description_request] Disparando tarefa assíncrona _send_description_task")
        asyncio.run_coroutine_threadsafe(
            self._send_description_task(), self.loop)

    async def _send_description_task(self):
        print("[DescritpionController _send_description_task] Iniciando captura de snapshot")
        frame_data = await self.video_app.get_snapshot()

        if frame_data:
            try:
                os.makedirs("capturas", exist_ok=True)
                filename = f"capturas/snapshot_{int(time.time())}.jpg"
                b64_string = frame_data["data"]
                image_bytes = base64.b64decode(b64_string)
                
                with open(filename, "wb") as f:
                    f.write(image_bytes)
                print(f"[DescritpionController _send_description_task] Imagem salva localmente em: {filename}")
            except Exception as e:
                print(f"[DescritpionController _send_description_task] Erro ao salvar imagem: {e}")

            print("[DescritpionController _send_description_task] Obtendo prompt e enviando payload para IA")
            prompt_text = self.description_app.get_prompt()

            try:
                response_text = self.gemini_client.describe_surroundings(
                    prompt=prompt_text,
                    image_part_data=frame_data
                )
                print(f"[DescritpionController _send_description_task] Resposta recebida da IA: {response_text[:50]}...")
                print("\n\n>>> [Gemini Response] <<<")
                print(response_text)
                print(">>> ------------------- <<<")
            except Exception as e:
                print(f"[DescritpionController _send_description_task] Erro ao gerar texto via Gemini: {e}")
                traceback.print_exc()
        else:
            print("[DescritpionController _send_description_task] Erro: Falha ao capturar frame (Câmera ocupada ou fechada)")