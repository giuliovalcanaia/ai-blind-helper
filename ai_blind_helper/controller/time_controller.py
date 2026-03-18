import asyncio
from event import *

class TimeController:
    def __init__(self, clock_app, date_app, audio_app, audio_in_queue, state_provider, event_bus: EventBus):
        print("[TimeController __init__] Initializing time and date controller")
        self.clock_app = clock_app
        self.date_app = date_app
        self.audio_app = audio_app
        self.audio_in_queue = audio_in_queue
        self.state_provider = state_provider
        
        event_bus.subscribe(
            TIME_REQUEST,
            self.handle_time_request
        )
        
        event_bus.subscribe(
            DATE_REQUEST,
            self.handle_date_request
        )
        
    @property
    def loop(self):
        return self.state_provider.loop
    
    async def play_current_time(self):
        print("[TimeController play_current_time] Requesting current time audio path")
        path = await asyncio.to_thread(self.clock_app.get_current_time_audio_path)
        
        if path:
            print(f"[TimeController play_current_time] Playing audio: {path}")
            asyncio.create_task(self.audio_app.play_file(
                path, self.audio_in_queue, self.loop))
        else:
            print("[TimeController play_current_time] Error: Current time audio path not found")

    async def play_current_date(self):
        print("[TimeController play_current_date] Requesting current date audio paths")
        paths = await asyncio.to_thread(self.date_app.get_current_date_audio_paths)

        if paths:
            print(f"[TimeController play_current_date] Starting playback of {len(paths)} date audio files")
            for path in paths:
                await self.audio_app.play_file(path, self.audio_in_queue, self.loop)
            print("[TimeController play_current_date] All date files have been queued for playback")
        else:
            print("[TimeController play_current_date] Error: No date audio found")
            
    def handle_time_request(self):
        print("[TimeController handle_time_request] Time request detected")
        if self.loop is None:
            print("[TimeController handle_time_request] Error: Event loop not available")
            return
        asyncio.run_coroutine_threadsafe(self.play_current_time(), self.loop)

    def handle_date_request(self):
        print("[TimeController handle_date_request] Date request detected")
        if self.loop is None:
            print("[TimeController handle_date_request] Error: Event loop not available")
            return
        asyncio.run_coroutine_threadsafe(self.play_current_date(), self.loop)