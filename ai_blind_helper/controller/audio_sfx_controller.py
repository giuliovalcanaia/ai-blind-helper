import asyncio

class AudioSFXController:

    def __init__(self, audio_app, audio_in_queue, state_provider, msg_app, sfx_app):
        self.audio_app = audio_app
        self.audio_in_queue = audio_in_queue
        self.state_provider = state_provider
        self.msg_app = msg_app
        self.sfx_app = sfx_app
        
    @property
    def loop(self):
        return self.state_provider.loop
    
    
    async def play_file_by_path(self, path):

        if path: 
            print(f"[Sistema] Reproduzindo: {path}")
            # Toca o arquivo diretamente. NÃO use 'for', pois path é uma string única.
            await self.audio_app.play_file(path, self.audio_in_queue, self.loop)
        else:
            print(f"[Sistema] Nenhum áudio encontrado: {path}") 

    async def initiating_gemini_audio(self):
        """Toca o som de 'iniciando conexão'."""
        path = self.msg_app.get_initiating_gemini()
        await self.play_file_by_path(path)

    async def closing_gemini_audio(self):
        """Toca o som de 'encerrando conexão'."""
        path = self.msg_app.get_closing_gemini()  
        await self.play_file_by_path(path)

    async def initiating_gemini_video(self):
        """Toca o som de 'iniciando conexão'."""
        path = self.msg_app.get_initiating_gemini_video()
        await self.play_file_by_path(path)

    async def closing_gemini_video(self):
        """Toca o som de 'encerrando conexão'."""
        path = self.msg_app.get_closing_gemini_video()  
        await self.play_file_by_path(path) 

    def audio_button_press(self):
        """Chamado pelo teclado. Agenda a tarefa no loop principal."""
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self._task_audio_button_press(), self.loop
            )
            
    def audio_button_release(self):
        """Chamado pelo teclado. Agenda a tarefa no loop principal."""
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self._task_audio_button_release(), self.loop
            )

    async def _task_audio_button_press(self):
        path = self.sfx_app.get_audio_button_press()
        await self.play_file_by_path(path)

    async def _task_audio_button_release(self):
        path = self.sfx_app.get_audio_button_release()
        await self.play_file_by_path(path) 

        
    async def initiating_gemini_audio_sfx(self):
        path = self.sfx_app.get_open_websocket()
        await self.play_file_by_path(path)
        
        
    async def closing_gemini_audio_sfx(self):
        path = self.sfx_app.get_close_websocket()
        await self.play_file_by_path(path)