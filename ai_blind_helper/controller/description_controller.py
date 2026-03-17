import asyncio
import base64
import time
import os
import traceback
from google.genai import types
from event import (EventBus, DESCRIPTION_REQUEST)

class DescritpionController:
    
    def __init__(self, video_app, description_app, state_provider, gemini_client, audio_in_queue, event_bus: EventBus):
        print(f"[DescritpionController __init__] Inicializando controlador de descrição")
        self.video_app = video_app
        self.description_app = description_app
        self.gemini_client = gemini_client
        self.state_provider = state_provider
        
        print("[DescritpionController __init__] Inicializando variáveis de estado e filas")
        self.input_queue = None
        self.session_task = None
        self.audio_in_queue = audio_in_queue

        print("[DescritpionController __init__] Inicialização concluída com sucesso")
        
        event_bus.subscribe(
            DESCRIPTION_REQUEST,
            self.handle_description_request
        )
        
    @property
    def loop(self):
        loop = self.state_provider.loop
        print(f"[DescritpionController loop] Obtendo loop: {loop}")
        return loop
    
    def handle_description_request(self):
        print("[DescritpionController handle_description_request] Tecla 'D' pressionada - Requisição de descrição iniciada")
        
        if self.loop is None:
            print("[DescritpionController handle_description_request] ERRO: Loop de eventos não definido. Abortando ação.")
            return

        print("[DescritpionController handle_description_request] Loop ok, disparando _send_description_task")
        
        try:
            asyncio.run_coroutine_threadsafe(
                self._send_description_task(), self.loop)
            print("[DescritpionController handle_description_request] Tarefa enviada com sucesso ao loop")
        except Exception as e:
            print(f"[DescritpionController handle_description_request] FALHA ao agendar tarefa: {e}")

    async def _ensure_session_active(self):
        print("[DescritpionController _ensure_session_active] Verificando estado da sessão com Gemini")
        
        if self.gemini_client.is_connected:
            print("[DescritpionController _ensure_session_active] Sessão já está ativa. Nenhuma ação necessária.")
            return False
        
        print("[DescritpionController _ensure_session_active] Sessão não encontrada. Criando nova sessão...")
        try:
            await self.handle_connection()
            print("[DescritpionController _ensure_session_active] Sessão criada com sucesso!")
            return True
        except Exception as e:
            print(f"[DescritpionController _ensure_session_active] ERRO ao iniciar sessão: {e}")
            traceback.print_exc()
            return False

    async def _send_description_task(self):
        print("[DescritpionController _send_description_task] Início da tarefa de descrição")
        
        created_new_session = await self._ensure_session_active()
        
        print("[DescritpionController _send_description_task] Solicitando snapshot ao módulo de vídeo")
        frame_data = await self.video_app.get_snapshot()
        
        if not frame_data:
            print("[DescritpionController _send_description_task] ERRO: Falha ao capturar frame (Camera indisponível)")
            return
        
        print("[DescritpionController _send_description_task] Frame recebido. Decodificando...")
        
        try:
            # Decodificação e salvamento local (mantido para debug)
            os.makedirs("capturas", exist_ok=True)
            filename = f"capturas/snapshot_{int(time.time())}.jpg"
            b64_string = frame_data["data"]
            image_bytes = base64.b64decode(b64_string)
            
            with open(filename, "wb") as f:
                f.write(image_bytes)
            print(f"[DescritpionController _send_description_task] Imagem salva em: {filename}")
            
            target_queue = self.input_queue if created_new_session else self.gemini_client.input_queue

            if target_queue:
                # 1. Enviar a Imagem (Como RealtimeInput / Media Chunk)
                print("[DescritpionController] Enviando imagem para a fila...")
                image_payload = {
                    "data": image_bytes,
                    "mime_type": "image/jpeg"
                }
                await target_queue.put(image_payload)

                # 2. Enviar o Texto (Prompt)
                # O Live API aceita strings de texto diretamente para input de usuário
                prompt_text = self.description_app.get_prompt()
                print(f"[DescritpionController] Enviando prompt: {prompt_text}")
                await target_queue.put(prompt_text)
                
                print("[DescritpionController] Payload (Imagem + Texto) enviado com sucesso!")
            else:
                print("[DescritpionController] ERRO: Nenhuma fila disponível para envio!")

        except Exception as e:
            print(f"[DescritpionController _send_description_task] FALHA no processo: {e}")
            traceback.print_exc()

        print("[DescritpionController _send_description_task] Tarefa finalizada")

    async def handle_connection(self):
        print("[DescritpionController handle_connection] Iniciando preparação de sessão com Gemini...")

        if self.gemini_client.is_connected:
            print("[DescritpionController handle_connection] Sessão já ativa. Nada a fazer.")
            return False
        
        print("[DescritpionController handle_connection] Criando fila interna para comunicação")
        self.input_queue = asyncio.Queue()
        
        print("[DescritpionController handle_connection] Abrindo sessão com Gemini...")
        try:
            self.session_task = asyncio.create_task(
                self.gemini_client.start_session(
                    input_queue=self.input_queue,
                    output_queue=self.audio_in_queue
                )
            )
            print("[DescritpionController handle_connection] Sessão inicializada e task registrada")
        except Exception as e:
            print(f"[DescritpionController handle_connection] ERRO ao iniciar sessão: {e}")
            traceback.print_exc()

        return True

    def _close_session(self):
        print("[DescritpionController _close_session] Solicitando encerramento de sessão")

        if not self.session_task:
            print("[DescritpionController _close_session] Nenhuma sessão ativa para encerrar")
            return
        
        try:
            print("[DescritpionController _close_session] Cancelando task e limpando filas")
            self.session_task.cancel()
            self.session_task = None
            self.input_queue = None
            print("[DescritpionController _close_session] Sessão encerrada com sucesso")
        except Exception as e:
            print(f"[DescritpionController _close_session] ERRO ao encerrar sessão: {e}")
            traceback.print_exc()
