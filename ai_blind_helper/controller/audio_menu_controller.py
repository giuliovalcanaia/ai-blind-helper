import asyncio

class AudioMenuController:
    def __init__(self, audio_app, audio_in_queue, state_provider, menu_app):
        self.audio_app = audio_app
        self.audio_in_queue = audio_in_queue
        self.state_provider = state_provider
        self.menu_app = menu_app
    
    @property
    def loop(self):
        return self.state_provider.loop
    
    async def _play_menu_path(self, path):
        """Helper interno para tocar sons do menu"""
        if path:
            # Opcional: Se quiser que o som do menu corte o anterior imediatame
            # if hasattr(self.audio_app, 'stop'):
            #     await self.audio_app.stop()
            
            print(f"[Menu] Reproduzindo ícone sonoro: {path}")
            await self.audio_app.play_file(path, self.audio_in_queue, self.loop)

    def play_menu_change_language(self):
        """Toca o áudio: change-language.wav"""
        if self.loop is None: return
        path = self.menu_app.get_change_language_audio_path()
        print(f"Play menu change language: {path}")
        asyncio.run_coroutine_threadsafe(self._play_menu_path(path), self.loop)

    def play_menu_describe(self):
        """Toca o áudio: describe.wav (Ao focar na opção de descrever)"""
        path = self.menu_app.get_describe_audio_path()
        if self.loop is None: return
        print(f"Play menu describe: {path}")
        asyncio.run_coroutine_threadsafe(self._play_menu_path(path), self.loop)

    def play_menu_exit(self):
        """Toca o áudio: exit.wav (Ao focar na opção de sair)"""
        if self.loop is None: return
        path = self.menu_app.get_exit_audio_path()
        print(f"Play menu exit: {path}")
        asyncio.run_coroutine_threadsafe(self._play_menu_path(path), self.loop)

    def play_menu_transcribe(self):
        """Toca o áudio: transcribe.wav (Ao focar na opção de ler texto)"""
        if self.loop is None: return
        path = self.menu_app.get_transcribe_audio_path()
        print(f"Play menu transcribe: {path}")
        asyncio.run_coroutine_threadsafe(self._play_menu_path(path), self.loop)

    def play_menu_websocket_audio(self):
        """Toca o áudio: websocket.wav (Ao focar na opção de conexão)"""
        if self.loop is None: return
        path = self.menu_app.get_websocket_audio_path()
        print(f"Play menu Websocket Audio")
        asyncio.run_coroutine_threadsafe(self._play_menu_path(path), self.loop)

    def play_menu_websocket_video(self):
        """Toca o áudio: websocket.wav (Ao focar na opção de conexão)"""
        if self.loop is None: return
        path = self.menu_app.get_websocket_audio_path()
        print(f"Play menu Websocket Video")
        asyncio.run_coroutine_threadsafe(self._play_menu_path(path), self.loop)
