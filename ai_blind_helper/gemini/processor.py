class GeminiResponseProcessor:
    """Processa o fluxo de entrada do Gemini (Áudio vs Texto)"""
    def __init__(self, audio_queue: asyncio.Queue):
        self.audio_queue = audio_queue

    async def process_turn(self, turn_generator):
        async for response in turn_generator:
            if data := response.data:
                self.audio_queue.put_nowait(data)
                continue
            if text := response.text:
                print(text, end="")