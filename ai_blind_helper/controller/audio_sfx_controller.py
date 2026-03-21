import asyncio
from event import (EventBus, SFX_AUDIO_BUTTON_PRESS, SFX_AUDIO_BUTTON_RELEASE, SFX_HOLD_BUTTON_PRESS)

class AudioSFXController:

    def __init__(self, audio_app, audio_in_queue, state_provider, msg_app, sfx_app, event_bus: EventBus):
        self.audio_app = audio_app
        self.audio_in_queue = audio_in_queue
        self.state_provider = state_provider
        self.msg_app = msg_app
        self.sfx_app = sfx_app
        
        event_bus.subscribe(
            SFX_AUDIO_BUTTON_PRESS,
            self.audio_button_press
        )
        
        event_bus.subscribe(
            SFX_AUDIO_BUTTON_RELEASE,
            self.audio_button_release
        )
        
        event_bus.subscribe(
            SFX_HOLD_BUTTON_PRESS,
            self.hold_button_press_sfx
        )
        
    @property
    def loop(self):
        return self.state_provider.loop
    
    
    async def play_file_by_path(self, path):

        if path: 
            print(f"[System] Playing: {path}")
            # Play the file directly. DO NOT use 'for', as path is a single string.
            await self.audio_app.play_file(path, self.audio_in_queue, self.loop)
        else:
            print(f"[System] No audio found: {path}") 

    async def initiating_gemini_audio(self):
        """Plays the 'initiating connection' sound."""
        path = self.msg_app.get_initiating_gemini()
        await self.play_file_by_path(path)

    async def closing_gemini_audio(self):
        """Plays the 'closing connection' sound."""
        path = self.msg_app.get_closing_gemini()  
        await self.play_file_by_path(path)

    async def initiating_gemini_video(self):
        """Plays the 'initiating connection' sound for video."""
        path = self.msg_app.get_initiating_gemini_video()
        await self.play_file_by_path(path)

    async def closing_gemini_video(self):
        """Plays the 'closing connection' sound for video."""
        path = self.msg_app.get_closing_gemini_video()  
        await self.play_file_by_path(path) 

    def audio_button_press(self):
        """Called by the keyboard. Schedules the task on the main loop."""
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self._task_audio_button_press(), self.loop
            )
            
    def audio_button_release(self):
        """Called by the keyboard. Schedules the task on the main loop."""
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self._task_audio_button_release(), self.loop
            )
            
    async def _task_audio_button_press(self):
        """
        Preserves the AI audio, plays the button SFX, and then resumes speech.
        """
        print("[AudioSFXController] Pausing AI audio to play beep...")

        # 1. Create a temporary list to save the chunks that were in the queue
        saved_chunks = []
        
        # 2. Drain the current queue by moving items into our list
        while not self.audio_in_queue.empty():
            try:
                # Get the chunk without waiting (nowait)
                chunk = self.audio_in_queue.get_nowait()
                saved_chunks.append(chunk)
            except asyncio.QueueEmpty:
                break

        # 3. Play the button sound (beep)
        # This will play while the AI queue is empty
        path = self.sfx_app.get_audio_button_press()
        if path:
            await self.play_file_by_path(path)

        # 4. Put the saved audio back into the queue in original order
        # Once the beep finishes, the AI will continue speaking from where it left off
        for chunk in saved_chunks:
            await self.audio_in_queue.put(chunk)
            
        print(f"[AudioSFXController] Resuming {len(saved_chunks)} AI audio packets.") 

    async def _task_audio_button_release(self):
        """
        Preserves the AI audio, plays the button SFX, and then resumes speech.
        """
        print("[AudioSFXController] Pausing AI audio to play beep...")

        # 1. Create a temporary list to save the chunks that were in the queue
        saved_chunks = []
        
        # 2. Drain the current queue by moving items into our list
        while not self.audio_in_queue.empty():
            try:
                # Get the chunk without waiting (nowait)
                chunk = self.audio_in_queue.get_nowait()
                saved_chunks.append(chunk)
            except asyncio.QueueEmpty:
                break

        # 3. Play the button sound (beep)
        # This will play while the AI queue is empty
        path = self.sfx_app.get_audio_button_release()
        if path:
            await self.play_file_by_path(path)

        # 4. Put the saved audio back into the queue in original order
        # Once the beep finishes, the AI will continue speaking from where it left off
        for chunk in saved_chunks:
            await self.audio_in_queue.put(chunk)
            
        print(f"[AudioSFXController] Resuming {len(saved_chunks)} AI audio packets.") 

        
    async def initiating_gemini_audio_sfx(self):
        path = self.sfx_app.get_open_websocket()
        await self.play_file_by_path(path)
        
        
    async def closing_gemini_audio_sfx(self):
        path = self.sfx_app.get_close_websocket()
        await self.play_file_by_path(path)
        
    def hold_button_press_sfx(self): # Method the keyboard will call
        """Called by the keyboard timer. Schedules the task on the main loop."""
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.hold_button_audio(), self.loop
            )

    async def hold_button_audio(self): # What actually plays
        path = self.sfx_app.get_hold_button()
        await self.play_file_by_path(path) 