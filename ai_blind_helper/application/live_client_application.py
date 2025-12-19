import asyncio
import time
import traceback
from google import genai
from config import Config

class LiveClientApplication:
    def __init__(self, audio_in_queue):
        print("[LiveClientApplication __init__] Inicializando cliente Gemini Live")
        self.client = genai.Client(
            http_options={"api_version": "v1beta"},
            api_key=Config.API_KEY,
        )
        self._is_connected = False

        self.audio_in_queue = audio_in_queue

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    async def start_session(self, input_queue: asyncio.Queue, output_queue: asyncio.Queue):
        print("[LiveClientApplication start_session] Tentando estabelecer conexão WebSocket com Gemini")
        try:
            async with (
                self.client.aio.live.connect(model=Config.MODEL, config=Config.LIVE_CONFIG) as session,
                asyncio.TaskGroup() as tg
            ):
                self._is_connected = True
                print("[LiveClientApplication start_session] Conexão estabelecida com sucesso. Iniciando Workers")

                tg.create_task(self._sender(session, input_queue))
                tg.create_task(self._receiver(session, output_queue))

        except asyncio.CancelledError:
            print("[LiveClientApplication start_session] Sessão cancelada via sistema/usuário")
            raise
        except Exception as e:
            print(f"[LiveClientApplication start_session] Erro crítico na sessão: {e}")
            traceback.print_exc()
        finally:
            self._is_connected = False
            print("[LiveClientApplication start_session] Sessão encerrada e estado de conexão resetado")

    async def _sender(self, session, input_queue: asyncio.Queue):
        print("[LiveClientApplication _sender] Worker de envio iniciado")
        while True:
            msg = await input_queue.get()
            
            try:
                await session.send(input=msg)
                input_queue.task_done()
            except Exception as e:
                print(f"[LiveClientApplication _sender] Erro ao enviar dados para a API: {e}")
                break

    async def _receiver(self, session, output_queue: asyncio.Queue):
        print("[LiveClientApplication _receiver] Worker de recepção iniciado")
        while True:
            try:
                turn = session.receive()

                async for response in turn:
                    if data := response.data:
                        output_queue.put_nowait(data)
                    if text := response.text:
                        print(text, end="", flush=True)
                
                # If you interrupt the model, it sends a turn_complete.
                # For interruptions to work, we need to stop playback.
                # So empty out the audio queue because it may have loaded
                # much more audio than has played yet.
                while not self.audio_in_queue.empty():
                    self.audio_in_queue.get_nowait()

            except Exception as e:
                print(f"[LiveClientApplication _receiver] Erro durante a recepção de dados: {e}")
                traceback.print_exc()
                break