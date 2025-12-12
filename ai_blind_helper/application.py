import asyncio
import traceback
from typing import Optional

# Imports dos nossos módulos
from config import Config
from audio_service import AudioService
from gemini_client import GeminiClient
from video_sources import IVideoSource, CameraSource, ScreenSource


class Application:
    def __init__(self, video_mode: str):
        self.video_mode = video_mode
        self.audio_service = AudioService()
        self.gemini_client = GeminiClient()

        self.audio_in_queue = asyncio.Queue()
        self.out_queue = asyncio.Queue(maxsize=5)

        self.video_source: Optional[IVideoSource] = None
        if video_mode == "camera":
            self.video_source = CameraSource()
        elif video_mode == "screen":
            self.video_source = ScreenSource()

    async def task_capture_video(self):
        if not self.video_source:
            return
        while True:
            frame_data = await asyncio.to_thread(self.video_source.get_frame)
            if frame_data is None:
                break
            await self.out_queue.put(frame_data)
            await asyncio.sleep(1.0)

    async def task_capture_audio(self):
        self.audio_service.start_input_stream()
        while True:
            data = await asyncio.to_thread(self.audio_service.read_chunk)
            await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})

    async def task_play_audio(self):
        self.audio_service.start_output_stream()
        while True:
            bytestream = await self.audio_in_queue.get()
            await asyncio.to_thread(self.audio_service.write_chunk, bytestream)

    async def task_send_text(self, session):
        while True:
            text = await asyncio.to_thread(input, "message > ")
            if text.lower() == "q":
                raise asyncio.CancelledError("User requested exit")
            await session.send(input=text or ".", end_of_turn=True)

    async def task_sender_worker(self, session):
        while True:
            msg = await self.out_queue.get()
            await session.send(input=msg)

    async def task_receiver_worker(self, session):
        while True:
            turn = session.receive()
            async for response in turn:
                if data := response.data:
                    self.audio_in_queue.put_nowait(data)
                if text := response.text:
                    print(text, end="", flush=True)
            while not self.audio_in_queue.empty():
                self.audio_in_queue.get_nowait()

    async def start(self):
        try:
            async with (
                self.gemini_client.connect() as session,
                asyncio.TaskGroup() as tg
            ):
                tg.create_task(self.task_send_text(session))
                tg.create_task(self.task_sender_worker(session))
                tg.create_task(self.task_capture_audio())
                tg.create_task(self.task_capture_video())
                tg.create_task(self.task_receiver_worker(session))
                tg.create_task(self.task_play_audio())

        except asyncio.CancelledError:
            print("\nEncerrando aplicação...")
        except ExceptionGroup as EG:
            traceback.print_exception(EG)
        finally:
            self.cleanup()

    def cleanup(self):
        print("Limpando recursos...")
        self.audio_service.close()
        if self.video_source:
            self.video_source.release()
