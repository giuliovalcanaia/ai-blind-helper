import asyncio
import traceback
from google import genai
from config import Config

class LiveClientApplication:
    def __init__(self):
        self.client = genai.Client(
            http_options={"api_version": "v1beta"},
            api_key=Config.API_KEY,
        )
        # 1. Estado inicial
        self._is_connected = False

    # 2. O getter booleano que você pediu
    @property
    def is_connected(self) -> bool:
        return self._is_connected

    async def start_session(self, input_queue: asyncio.Queue, output_queue: asyncio.Queue):
        try:
            print(">>> [Client] Conectando ao Gemini...")
            async with (
                self.client.aio.live.connect(model=Config.MODEL, config=Config.LIVE_CONFIG) as session,
                asyncio.TaskGroup() as tg
            ):
                # 3. Conexão confirmada
                self._is_connected = True
                print(">>> [Client] Conectado! Sessão iniciada.")
                
                tg.create_task(self._sender(session, input_queue))
                tg.create_task(self._receiver(session, output_queue))
                
        except asyncio.CancelledError:
            print("\n<<< [Client] Sessão cancelada pelo usuário.")
            raise
        except Exception as e:
            print(f"\n!!! [Client] Erro na sessão: {e}")
            traceback.print_exc()
        finally:
            # 4. Garante que fique False ao sair (seja por erro, cancelamento ou fim)
            self._is_connected = False
            print("<<< [Client] Sessão encerrada.") 

    async def _sender(self, session, input_queue: asyncio.Queue):
        """Lê da fila de entrada e manda para o Gemini"""
        while True:
            # Pega dados gerados pela Câmera/Microfone na Main App
            msg = await input_queue.get()
            await session.send(input=msg)
            input_queue.task_done()

    async def _receiver(self, session, output_queue: asyncio.Queue):
        """Recebe do Gemini e manda para a fila de saída"""
        while True: # <--- 1. Mantém o receiver vivo para sempre
            try:
                # 2. Aguarda/Inicia o próximo turno de recepção
                turn = session.receive() 
                
                # 3. Consome a resposta atual até o fim
                async for response in turn:
                    if data := response.data:
                        output_queue.put_nowait(data)
                    if text := response.text:
                        print(text, end="", flush=True)
                
                # 4. (Opcional) Debug para saber que o turno acabou
                # print("\n[Client] Turno finalizado, aguardando próximo...")

            except Exception as e:
                print(f"\n!!! [Receiver] Erro: {e}")
                # Importante: não deixe o loop quebrar totalmente se for um erro recuperável
                # Se for erro de conexão, talvez queira dar um 'break' ou reconectar
                traceback.print_exc()
                break 