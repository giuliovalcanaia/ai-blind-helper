import asyncio
from typing import Optional
from manager import IVideoSource, CameraSource, ScreenSource
import time


class VideoRecorderApplication:
    def __init__(self, mode: str, camera_source, screen_source):
        self.video_source: Optional[IVideoSource] = None
        if mode == "camera":
            self.video_source = camera_source
        elif mode == "screen":
            self.video_source = screen_source
        else:
            print(f" -> [VideoApp] Modo desconhecido: {mode}")

    async def task_capture_video(self, out_queue: asyncio.Queue, control_event: asyncio.Event):
        """
        Captura frames e joga na fila.
        Pausa o envio se control_event estiver false, mas mantém câmera aberta.
        """
        if not self.video_source:
            print(" -> [VideoApp] ERRO: Fonte de vídeo não detectada.")
            return

        print(" -> [VideoApp] Captura de Vídeo Iniciada (Hardware ON).")

        # CONFIGURAÇÃO DE FPS
        TARGET_FPS = 2  # 2 frames por segundo
        FRAME_DELAY = 1.0 / TARGET_FPS

        try:
            while True:
                # --- PONTO DE CONTROLE ---
                # Se o evento estiver false, trava aqui.
                # Como a câmera continua aberta, ao liberar (set),
                # a captura volta instantaneamente.
                await control_event.wait()

                start_time = time.time()

                # 1. Captura (Pesado - roda em Thread)
                # Nota: Dependendo da câmera, pode haver buffer antigo acumulado enquanto estava pausado.
                # Se notar "efeito fantasma" ao despausar, pode ser necessário ler alguns frames vazios aqui.
                frame_data = await asyncio.to_thread(self.video_source.get_frame)

                if frame_data is None:
                    print(
                        " -> [VideoApp] Frame vazio recebido (Câmera desconectada?).")
                    break

                # 2. Gerenciamento de Fila (Drop frame se estiver acumulando)
                # Fundamental para manter o vídeo "Live" e não com delay acumulado
                while not out_queue.empty():
                    try:
                        out_queue.get_nowait()
                        out_queue.task_done()
                    except asyncio.QueueEmpty:
                        break

                # Imprime o Json
                # print(frame_data)
                await out_queue.put(frame_data)

                # 3. Controle de Taxa (Sleep inteligente)
                elapsed = time.time() - start_time
                sleep_time = max(0, FRAME_DELAY - elapsed)

                # Pausa real para liberar a rede/CPU
                await asyncio.sleep(sleep_time)

        except asyncio.CancelledError:
            print(" -> [VideoApp] Tarefa de vídeo cancelada.")

    async def get_snapshot(self) -> Optional[dict]:
        """
        Retorna um único frame usando a conexão de câmera JÁ ABERTA.
        Útil para descrever o ambiente sem precisar parar/reiniciar a câmera.
        """
        if not self.video_source:
            print(" -> [VideoApp] Erro: Nenhuma fonte de vídeo configurada.")
            return None

        # Reutiliza o método get_frame da interface IVideoSource
        # Executa em thread para não bloquear o loop principal
        return await asyncio.to_thread(self.video_source.get_frame)

    def release(self):
        if self.video_source:
            self.video_source.release()
