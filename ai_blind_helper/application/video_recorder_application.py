import asyncio
from typing import Optional
import time

class VideoRecorderApplication:
    def __init__(self, mode: str, camera_source, screen_source):
        print(f"[VideoRecorderApplication __init__] Initializing video application in mode: {mode}")
        self.video_source: Optional[any] = None
        
        if mode == "camera":
            self.video_source = camera_source
        elif mode == "screen":
            self.video_source = screen_source
        else:
            print(f"[VideoRecorderApplication __init__] Error: Unknown mode '{mode}'")

    async def task_capture_video(self, out_queue: asyncio.Queue, control_event: asyncio.Event):
        print("[VideoRecorderApplication task_capture_video] Starting continuous capture task")
        
        if not self.video_source:
            print("[VideoRecorderApplication task_capture_video] Critical error: Video source not detected")
            return

        if hasattr(self.video_source, 'open'):
            print("[VideoRecorderApplication task_capture_video] Requesting video hardware open...")
            await asyncio.to_thread(self.video_source.open)
        
        
        TARGET_FPS = 2 
        FRAME_DELAY = 1.0 / TARGET_FPS

        try:
            while True:
                if not control_event.is_set():
                    print("[VideoRecorderApplication task_capture_video] Capture on hold (control_event locked)")
                    await control_event.wait()
                    print("[VideoRecorderApplication task_capture_video] Resuming video capture")

                start_time = time.time()

                frame_data = await asyncio.to_thread(self.video_source.get_frame)

                if frame_data is None:
                    print("[VideoRecorderApplication task_capture_video] Warning: Empty frame received (check connection)")
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
            print("[VideoRecorderApplication task_capture_video] Video task cancelled by system")
        except Exception as e:
            print(f"[VideoRecorderApplication task_capture_video] Unexpected error: {e}")

    async def get_snapshot(self) -> Optional[dict]:
        print("[VideoRecorderApplication get_snapshot] Requesting single frame capture (Snapshot)")
        if not self.video_source:
            print("[VideoRecorderApplication get_snapshot] Error: No video source configured for snapshot")
            return None

        try:
            frame = await asyncio.to_thread(self.video_source.get_frame)
            if frame:
                print("[VideoRecorderApplication get_snapshot] Snapshot captured successfully")
            return frame
        except Exception as e:
            print(f"[VideoRecorderApplication get_snapshot] Failed to capture snapshot: {e}")
            return None

    def release(self):
        print("[VideoRecorderApplication release] Releasing video hardware resources")
        if self.video_source:
            self.video_source.release()
            print("[VideoRecorderApplication release] Hardware liberado com sucesso")