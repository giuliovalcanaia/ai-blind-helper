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
        """
        Preserva o áudio da IA, toca o SFX do botão e retoma a fala.
        """
        print("[AudioSFXController] Pausando áudio da IA para tocar o bip...")

        # 1. Criar uma lista temporária para salvar os chunks que estavam na fila
        saved_chunks = []
        
        # 2. Esvaziar a fila atual movendo os itens para a nossa lista
        while not self.audio_in_queue.empty():
            try:
                # Pegamos o chunk sem esperar (nowait)
                chunk = self.audio_in_queue.get_nowait()
                saved_chunks.append(chunk)
            except asyncio.QueueEmpty:
                break

        # 3. Tocar o som do botão (o bip)
        # Isso será reproduzido enquanto a fila da IA está vazia
        path = self.sfx_app.get_audio_button_press()
        if path:
            await self.play_file_by_path(path)

        # 4. Devolver os áudios salvos para a fila na ordem original
        # Assim que o bip terminar, a IA continuará falando de onde parou
        for chunk in saved_chunks:
            await self.audio_in_queue.put(chunk)
            
        print(f"[AudioSFXController] Retomando {len(saved_chunks)} pacotes de áudio da IA.") 

    async def _task_audio_button_release(self):
        """
        Preserva o áudio da IA, toca o SFX do botão e retoma a fala.
        """
        print("[AudioSFXController] Pausando áudio da IA para tocar o bip...")

        # 1. Criar uma lista temporária para salvar os chunks que estavam na fila
        saved_chunks = []
        
        # 2. Esvaziar a fila atual movendo os itens para a nossa lista
        while not self.audio_in_queue.empty():
            try:
                # Pegamos o chunk sem esperar (nowait)
                chunk = self.audio_in_queue.get_nowait()
                saved_chunks.append(chunk)
            except asyncio.QueueEmpty:
                break

        # 3. Tocar o som do botão (o bip)
        # Isso será reproduzido enquanto a fila da IA está vazia
        path = self.sfx_app.get_audio_button_release()
        if path:
            await self.play_file_by_path(path)

        # 4. Devolver os áudios salvos para a fila na ordem original
        # Assim que o bip terminar, a IA continuará falando de onde parou
        for chunk in saved_chunks:
            await self.audio_in_queue.put(chunk)
            
        print(f"[AudioSFXController] Retomando {len(saved_chunks)} pacotes de áudio da IA.") 

        
    async def initiating_gemini_audio_sfx(self):
        path = self.sfx_app.get_open_websocket()
        await self.play_file_by_path(path)
        
        
    async def closing_gemini_audio_sfx(self):
        path = self.sfx_app.get_close_websocket()
        await self.play_file_by_path(path)