import asyncio
import os
import time
import base64
import traceback

class LoopController:

    def __init__(self, audio_app, loop, app_running, msg_app, audio_in_queue, keyboard_app, state_provider):
        print("[LoopController __init__] Inicializando controlador de loop principal")
        self.audio_app = audio_app
        self.loop = loop
        self.app_running = app_running
        self.msg_app = msg_app
        self.audio_in_queue = audio_in_queue
        self.keyboard_app = keyboard_app
        self.state_provider = state_provider

    def run(self):
        print("[LoopController run] Tentando iniciar o loop de eventos assíncrono")
        try:
            asyncio.run(self.start_main_loop())
        except KeyboardInterrupt:
            print("[LoopController run] Interrupção detectada via hardware (CTRL+C)")
    
    async def start_main_loop(self):
        print("[LoopController start_main_loop] Configurando loop e iniciando serviços")
        running_loop = asyncio.get_running_loop()
        self.loop = running_loop
        self.state_provider.loop = running_loop
        
        print("[LoopController start_main_loop] Acionando monitor de teclado")
        self.keyboard_app.start()

        print("[LoopController start_main_loop] Criando tarefa de reprodução de áudio")
        self.audio_playback_task = asyncio.create_task(
            self.audio_app.task_play_audio(self.audio_in_queue)
        )

        print("[LoopController start_main_loop] Solicitando mensagem de inicialização")
        await asyncio.create_task(self.play_current_power_on_message())

        print("\n" + "="*45)
        print("      SISTEMA AI-BLIND-HELPER ONLINE      ")
        print("="*45)
        print("-" * 45)
        print("[<] [ENTER] [>]")
        print("  [A] AUDIO")
        print("  [T] TEMPO") 
        print("="*45 + "\n")

        try:
            print("[LoopController start_main_loop] Entrando no loop de espera ativo")
            while self.app_running:
                await asyncio.sleep(0.5)
            print("[LoopController start_main_loop] Condição app_running encerrada")

        except asyncio.CancelledError:
            print("[LoopController start_main_loop] Tarefa cancelada pelo sistema")

        finally:
            print("[LoopController start_main_loop] Iniciando protocolo de encerramento e limpeza")
            if self.audio_playback_task:
                self.audio_playback_task.cancel()
                print("[LoopController start_main_loop] Tarefa de áudio cancelada")


    async def play_current_power_on_message(self):
            print("[LoopController play_current_power_on_message] Buscando caminho do áudio de boas-vindas")
            path = self.msg_app.get_current_welcome_message_path()
            
            if path:
                print(f"[LoopController play_current_power_on_message] Reproduzindo arquivo: {path}")
                await self.audio_app.play_file(path, self.audio_in_queue, self.loop)
            else:
                print("[LoopController play_current_power_on_message] Aviso: Nenhum áudio de inicialização disponível")

    def stop_running(self):
        self.app_running = False