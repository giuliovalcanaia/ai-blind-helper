class LoopController:
    def __init__(self, api_key, video_mode):
        self.gemini_client = GeminiLiveClient(api_key)
        self.audio_manager = AudioHardwareManager()
        self.video_manager = VideoCaptureManager(video_mode)
        
        self.out_queue = asyncio.Queue(maxsize=5) # Para enviar ao Gemini
        self.audio_in_queue = asyncio.Queue()     # Para reproduzir no speaker
        
        self.response_processor = GeminiResponseProcessor(self.audio_in_queue)
        self.session = None

    async def _task_send_text(self):
        """Lê input do teclado e envia texto"""
        while True:
            text = await asyncio.to_thread(input, "message > ")
            if text.lower() == "q":
                raise asyncio.CancelledError("User requested exit")
            await self.session.send(input=text or ".", end_of_turn=True)

    async def _task_video_capture(self):
        """Captura vídeo e coloca na fila de envio"""
        if self.video_manager.mode == "none":
            return
            
        await self.video_manager.setup()
        while True:
            frame_bytes = await self.video_manager.get_frame_bytes()
            if frame_bytes:
                payload = GeminiProtocolEncoder.encode_image(frame_bytes)
                await self.out_queue.put(payload)
            await asyncio.sleep(1.0) # Taxa de atualização de vídeo (1 FPS)

    async def _task_audio_capture(self):
        """Captura microfone e coloca na fila de envio"""
        await self.audio_manager.start_input_stream()
        while True:
            data = await self.audio_manager.read_chunk()
            payload = GeminiProtocolEncoder.encode_audio(data)
            await self.out_queue.put(payload)

    async def _task_sender(self):
        """Consome a fila de saída e envia para o Gemini via WebSocket"""
        while True:
            msg = await self.out_queue.get()
            await self.session.send(input=msg)

    async def _task_receiver(self):
        """Recebe dados do Gemini"""
        while True:
            turn = self.session.receive()
            await self.response_processor.process_turn(turn)
            
            # Se o modelo foi interrompido, limpar buffer de audio pendente
            while not self.audio_in_queue.empty():
                self.audio_in_queue.get_nowait()

    async def _task_audio_playback(self):
        """Toca o áudio recebido"""
        await self.audio_manager.start_output_stream()
        while True:
            bytestream = await self.audio_in_queue.get()
            await self.audio_manager.write_chunk(bytestream)

    async def run(self):
        try:
            async with self.gemini_client.connect() as session:
                self.session = session
                print("--- Conectado ao Gemini Live ---")

                async with asyncio.TaskGroup() as tg:
                    tg.create_task(self._task_send_text())
                    tg.create_task(self._task_video_capture())
                    tg.create_task(self._task_audio_capture())
                    tg.create_task(self._task_sender())
                    tg.create_task(self._task_receiver())
                    tg.create_task(self._task_audio_playback())

        except asyncio.CancelledError:
            print("\nEncerrando...")
        except ExceptionGroup as EG:
            traceback.print_exception(EG)
        finally:
            self.audio_manager.close()
            self.video_manager.release()