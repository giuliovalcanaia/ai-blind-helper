import asyncio

class TimeController:
    def __init__(self, clock_app, date_app, audio_app, audio_in_queue, loop):
        self.clock_app = clock_app
        self.date_app = date_app
        self.audio_app = audio_app
        self.audio_in_queue = audio_in_queue
        self.loop = loop
    
    async def play_current_time(self):
        path = await asyncio.to_thread(self.clock_app.get_current_time_audio_path)
        if path:
            print(path)
            asyncio.create_task(self.audio_app.play_file(
                path, self.audio_in_queue, self.loop))

    async def play_current_date(self):
        # Agora chamamos o método novo (que retorna lista) e rodamos na thread
        paths = await asyncio.to_thread(self.date_app.get_current_date_audio_paths)

        if paths:
            print(f"[Sistema] Reproduzindo data: {len(paths)} arquivos.")
            for path in paths:
                # O 'await' aqui é crucial para garantir a ordem de inserção na fila
                # ou o início da task de reprodução na ordem correta
                await self.audio_app.play_file(path, self.audio_in_queue, self.loop)

                # Opcional: Um pequeno delay entre os áudios para não ficar encavalado
                # await asyncio.sleep(0.1)
        else:
            print("[Sistema] Nenhum áudio de data encontrado.")
            
    def handle_time_request(self):
        if self.loop is None:
            return
        asyncio.run_coroutine_threadsafe(self.play_current_time(), self.loop)

    def handle_date_request(self):
        if self.loop is None:
            return
        asyncio.run_coroutine_threadsafe(self.play_current_date(), self.loop)