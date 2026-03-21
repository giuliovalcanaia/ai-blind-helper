import asyncio
import os
import time
import base64
import traceback

class LoopController:

    def __init__(self, audio_app, loop, app_running, msg_app, audio_in_queue, keyboard_app, state_provider):
        print("[LoopController __init__] Initializing main loop controller")
        self.audio_app = audio_app
        self.loop = loop
        self.app_running = app_running
        self.msg_app = msg_app
        self.audio_in_queue = audio_in_queue
        self.keyboard_app = keyboard_app
        self.state_provider = state_provider

    def run(self):
        print("[LoopController run] Attempting to start asyncio event loop")
        try:
            asyncio.run(self.start_main_loop())
        except KeyboardInterrupt:
            print("[LoopController run] Hardware interrupt detected (CTRL+C)")
    
    async def start_main_loop(self):
        print("[LoopController start_main_loop] Setting up loop and starting services")
        running_loop = asyncio.get_running_loop()
        self.loop = running_loop
        self.state_provider.loop = running_loop
        
        print("[LoopController start_main_loop] Activating keyboard monitor")
        self.keyboard_app.start()

        print("[LoopController start_main_loop] Creating audio playback task")
        self.audio_playback_task = asyncio.create_task(
            self.audio_app.task_play_audio(self.audio_in_queue)
        )

        print("[LoopController start_main_loop] Requesting startup message")
        await asyncio.create_task(self.play_current_power_on_message())

        print("\n" + "="*45)
        print("      SISTEMA AI-BLIND-HELPER ONLINE      ")
        print("="*45)
        print("-" * 45)
        print("[<] [ENTER] [>]")
        print("  [A] AUDIO")
        print("  [T] TEMPO") 
        print("="*45 + "\n")

        try:
            print("[LoopController start_main_loop] Entering active wait loop")
            while self.app_running:
                await asyncio.sleep(0.5)
            print("[LoopController start_main_loop] app_running condition ended")

        except asyncio.CancelledError:
            print("[LoopController start_main_loop] Task cancelled by system")

        finally:
            print("[LoopController start_main_loop] Starting shutdown and cleanup protocol")
            if self.audio_playback_task:
                self.audio_playback_task.cancel()
                print("[LoopController start_main_loop] Audio task cancelled")


    async def play_current_power_on_message(self):
            print("[LoopController play_current_power_on_message] Fetching welcome audio path")
            path = self.msg_app.get_current_welcome_message_path()
            
            if path:
                print(f"[LoopController play_current_power_on_message] Playing file: {path}")
                await self.audio_app.play_file(path, self.audio_in_queue, self.loop)
            else:
                print("[LoopController play_current_power_on_message] Warning: No startup audio available")

    def stop_running(self):
        self.app_running = False