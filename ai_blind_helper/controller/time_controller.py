import asyncio
from event import EventBus

class TimeController:
    def __init__(self, clock_app, date_app, audio_app, audio_in_queue, state_provider, event_bus):
        print("[TimeController __init__] Inicializando controlador de tempo e data")
        self.clock_app = clock_app
        self.date_app = date_app
        self.audio_app = audio_app
        self.audio_in_queue = audio_in_queue
        self.state_provider = state_provider
        
    @property
    def loop(self):
        return self.state_provider.loop
    
    async def play_current_time(self):
        print("[TimeController play_current_time] Solicitando caminho do áudio de hora atual")
        path = await asyncio.to_thread(self.clock_app.get_current_time_audio_path)
        
        if path:
            print(f"[TimeController play_current_time] Reproduzindo áudio: {path}")
            asyncio.create_task(self.audio_app.play_file(
                path, self.audio_in_queue, self.loop))
        else:
            print("[TimeController play_current_time] Erro: Caminho de áudio da hora não encontrado")

    async def play_current_date(self):
        print("[TimeController play_current_date] Solicitando caminhos dos áudios de data atual")
        paths = await asyncio.to_thread(self.date_app.get_current_date_audio_paths)

        if paths:
            print(f"[TimeController play_current_date] Iniciando reprodução de {len(paths)} arquivos de data")
            for path in paths:
                await self.audio_app.play_file(path, self.audio_in_queue, self.loop)
            print("[TimeController play_current_date] Todos os arquivos de data foram enviados para reprodução")
        else:
            print("[TimeController play_current_date] Erro: Nenhum áudio de data encontrado")
            
    def handle_time_request(self):
        print("[TimeController handle_time_request] Requisição de hora detectada")
        if self.loop is None:
            print("[TimeController handle_time_request] Erro: Loop de eventos não disponível")
            return
        asyncio.run_coroutine_threadsafe(self.play_current_time(), self.loop)

    def handle_date_request(self):
        print("[TimeController handle_date_request] Requisição de data detectada")
        if self.loop is None:
            print("[TimeController handle_date_request] Erro: Loop de eventos não disponível")
            return
        asyncio.run_coroutine_threadsafe(self.play_current_date(), self.loop)