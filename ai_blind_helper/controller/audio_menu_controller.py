import asyncio
from event import *

class AudioMenuController:
    def __init__(self, audio_app, audio_in_queue, state_provider, menu_app, event_bus: EventBus):
        self.audio_app = audio_app
        self.audio_in_queue = audio_in_queue
        self.state_provider = state_provider
        self.menu_app = menu_app
        
        event_bus.subscribe(
            MENU_SELECT_AUDIO_LIVE,
            self.play_menu_websocket_audio
        )
        
        event_bus.subscribe(
            MENU_SELECT_VIDEO_LIVE,
            self.play_menu_websocket_video
        )
        
        event_bus.subscribe(
            MENU_SELECT_DESCRIBE,
            self.play_menu_describe
        )
        
        event_bus.subscribe(
            MENU_SELECT_TRANSCRIBE,
            self.play_menu_transcribe
        )
        
        event_bus.subscribe(
            MENU_SELECT_CHANGE_LANGUAGE,
            self.play_menu_change_language
        )
        
        event_bus.subscribe(
            MENU_SELECT_EXIT,
            self.play_menu_exit
        )

    @property
    def loop(self):
        return self.state_provider.loop

    async def _play_menu_path(self, path):
        """Internal helper to play menu sounds."""
        if path:
            print(f"[Menu] Playing menu icon sound: {path}")
            await self.audio_app.play_file(path, self.audio_in_queue, self.loop)

    def play_menu_change_language(self):
        """Plays audio: change-language.wav"""
        if self.loop is None:
            return
        path = self.menu_app.get_change_language_audio_path()
        print(f"Play menu change language: {path}")
        asyncio.run_coroutine_threadsafe(self._play_menu_path(path), self.loop)

    def play_menu_describe(self):
        """Plays audio: describe.wav (When focusing on describe option)"""
        path = self.menu_app.get_describe_audio_path()
        if self.loop is None: return
        print(f"Play menu describe: {path}")
        asyncio.run_coroutine_threadsafe(self._play_menu_path(path), self.loop)

    def play_menu_exit(self):
        """Plays audio: exit.wav (When focusing on exit option)"""
        if self.loop is None:
            return
        path = self.menu_app.get_exit_audio_path()
        print(f"Play menu exit: {path}")
        asyncio.run_coroutine_threadsafe(self._play_menu_path(path), self.loop)

    def play_menu_transcribe(self):
        """Plays audio: transcribe.wav (When focusing on transcribe option)"""
        if self.loop is None:
            return
        path = self.menu_app.get_transcribe_audio_path()
        print(f"Play menu transcribe: {path}")
        asyncio.run_coroutine_threadsafe(self._play_menu_path(path), self.loop)

    def play_menu_websocket_audio(self):
        """Plays audio: websocket.wav (When focusing on connection option)"""
        if self.loop is None:
            return
        path = self.menu_app.get_websocket_audio_path()
        print(f"Play menu Websocket Audio")
        asyncio.run_coroutine_threadsafe(self._play_menu_path(path), self.loop)

    def play_menu_websocket_video(self):
        """Plays audio: websocket.wav (When focusing on connection option)"""
        if self.loop is None:
            return
        path = self.menu_app.get_websocket_video_path()
        print(f"Play menu Websocket Video")
        asyncio.run_coroutine_threadsafe(self._play_menu_path(path), self.loop)

    def play_language_changed(self):
        path = self.menu_app.get_language_changed_path()
        print(f"[AudioMenuController] Play Language Changed with path {path}")
        asyncio.run_coroutine_threadsafe(self._play_menu_path(path), self.loop)
