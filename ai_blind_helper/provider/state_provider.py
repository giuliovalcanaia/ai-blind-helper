import asyncio

class StateProvider:
    def __init__(self):
        self.audio_in_queue = asyncio.Queue()
        self.out_queue = asyncio.Queue(maxsize=5)
        self.start_audio_event = asyncio.Event()
        self.start_video_event = asyncio.Event()
        self.loop = None  # Will be filled in run()
        self.app_running = True
        self.session_task = None