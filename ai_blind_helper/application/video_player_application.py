import asyncio
from typing import Optional
from manager import IVideoSource, CameraSource, ScreenSource
import time

class VideoPlayerApplication:
    def __init__(self, mode: str):
        self.video_source: Optional[IVideoSource] = None
        if mode == "camera":
            self.video_source = CameraSource()
        elif mode == "screen":
            self.video_source = ScreenSource()
        else:
            print(f" -> [VideoApp] Modo desconhecido: {mode}")

    async def task_capture_video(self, out_queue: asyncio.Queue):
        """Captura frames e joga na fila de saída (para o Gemini)"""
        if not self.video_source: 
            return
            
        print(" -> [VideoApp] Captura de Vídeo Iniciada.")
        
        # CONFIGURAÇÃO DE FPS
        TARGET_FPS = 2  # 2 frames por segundo é excelente para estabilidade
        FRAME_DELAY = 1.0 / TARGET_FPS

        while True:
            start_time = time.time()

            # 1. Captura (Pesado - roda em Thread)
            frame_data = await asyncio.to_thread(self.video_source.get_frame)
            if frame_data is None: 
                break

            # 2. Gerenciamento de Fila (Drop frame se estiver acumulando)
            # Se a fila tiver mais de 1 item, limpa tudo para mandar o mais recente
            while not out_queue.empty():
                try:
                    out_queue.get_nowait()
                    out_queue.task_done()
                except asyncio.QueueEmpty:
                    break

            await out_queue.put(frame_data)

            # 3. Controle de Taxa (Sleep inteligente)
            elapsed = time.time() - start_time
            sleep_time = max(0, FRAME_DELAY - elapsed)
            
            # Pausa real para liberar a rede para o Ping/Pong do websocket
            await asyncio.sleep(sleep_time) 

    def release(self):
        if self.video_source:
            self.video_source.release()