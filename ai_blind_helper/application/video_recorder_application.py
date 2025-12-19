import asyncio
from typing import Optional
import time

class VideoRecorderApplication:
    def __init__(self, mode: str, camera_source, screen_source):
        print(f"[VideoRecorderApplication __init__] Inicializando aplicação de vídeo no modo: {mode}")
        self.video_source: Optional[any] = None
        
        if mode == "camera":
            self.video_source = camera_source
        elif mode == "screen":
            self.video_source = screen_source
        else:
            print(f"[VideoRecorderApplication __init__] Erro: Modo desconhecido '{mode}'")

    async def task_capture_video(self, out_queue: asyncio.Queue, control_event: asyncio.Event):
        print("[VideoRecorderApplication task_capture_video] Iniciando tarefa de captura contínua")
        
        if not self.video_source:
            print("[VideoRecorderApplication task_capture_video] Erro crítico: Fonte de vídeo não detectada")
            return

        if hasattr(self.video_source, 'open'):
            print("[VideoRecorderApplication task_capture_video] Solicitando abertura do hardware de vídeo...")
            await asyncio.to_thread(self.video_source.open)
        
        
        TARGET_FPS = 2 
        FRAME_DELAY = 1.0 / TARGET_FPS

        try:
            while True:
                if not control_event.is_set():
                    print("[VideoRecorderApplication task_capture_video] Captura em espera (control_event bloqueado)")
                    await control_event.wait()
                    print("[VideoRecorderApplication task_capture_video] Retomando captura de vídeo")

                start_time = time.time()

                frame_data = await asyncio.to_thread(self.video_source.get_frame)

                if frame_data is None:
                    print("[VideoRecorderApplication task_capture_video] Aviso: Frame vazio recebido (verificar conexão)")
                    break

                while not out_queue.empty():
                    try:
                        out_queue.get_nowait()
                        out_queue.task_done()
                    except asyncio.QueueEmpty:
                        break

                await out_queue.put(frame_data)

                elapsed = time.time() - start_time
                sleep_time = max(0, FRAME_DELAY - elapsed)
                await asyncio.sleep(sleep_time)

        except asyncio.CancelledError:
            print("[VideoRecorderApplication task_capture_video] Tarefa de vídeo cancelada pelo sistema")
        except Exception as e:
            print(f"[VideoRecorderApplication task_capture_video] Erro imprevisto: {e}")

    async def get_snapshot(self) -> Optional[dict]:
        print("[VideoRecorderApplication get_snapshot] Solicitando captura de frame único (Snapshot)")
        if not self.video_source:
            print("[VideoRecorderApplication get_snapshot] Erro: Nenhuma fonte de vídeo configurada para snapshot")
            return None

        try:
            frame = await asyncio.to_thread(self.video_source.get_frame)
            if frame:
                print("[VideoRecorderApplication get_snapshot] Snapshot capturado com sucesso")
            return frame
        except Exception as e:
            print(f"[VideoRecorderApplication get_snapshot] Falha ao capturar snapshot: {e}")
            return None

    def release(self):
        print("[VideoRecorderApplication release] Liberando recursos de hardware de vídeo")
        if self.video_source:
            self.video_source.release()
            print("[VideoRecorderApplication release] Hardware liberado com sucesso")