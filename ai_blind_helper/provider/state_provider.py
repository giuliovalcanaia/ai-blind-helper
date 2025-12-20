import asyncio

class StateProvider:
    def __init__(self):
        # Comunicação
        self.audio_in_queue = asyncio.Queue()
        self.out_queue = asyncio.Queue(maxsize=5)
        
        # Sincronização
        self.start_audio_event = asyncio.Event()
        self.start_video_event = asyncio.Event()
        
        # Controle de Ciclo de Vida
        self.loop = None  # Será preenchido no run()
        self.app_running = True
        self.session_task = None