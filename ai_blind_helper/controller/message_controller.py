class MessageController:
    
    def __init__(self, msg_app, audio_app, audio_in_queue, loop):
            self.msg_app = msg_app
            self.audio_app = audio_app
            self.audio_in_queue = audio_in_queue
            self.loop = loop
    
    async def play_current_power_on_message(self):
        # O método get_current_welcome_message_path é rápido (só strings),
        # pode chamar direto sem thread ou await.
        path = self.msg_app.get_current_welcome_message_path()
        if path:
            print(f"[Sistema] Reproduzindo Power On: {path}")
            # Toca o arquivo diretamente. NÃO use 'for', pois path é uma string única.
            await self.audio_app.play_file(path, self.audio_in_queue, self.loop)
        else:
            print("[Sistema] Nenhum áudio de power on encontrado.")