import asyncio
import os
import time
import base64
import traceback

class LoopController:

    def __init__(self, audio_app, loop, app_running, msg_app, audio_in_queue, keyboard_app):
        self.audio_app = audio_app
        self.loop = loop
        self.app_running = app_running
        self.msg_app = msg_app
        self.audio_in_queue = audio_in_queue
        self.keyboard_app = keyboard_app

    # --- PONTO DE ENTRADA ---
    def run(self):
        
        try:
            asyncio.run(self.start_main_loop())
        except KeyboardInterrupt:
            print("\n[Sistema] Interrupção detectada (CTRL+C).")
        # finally:
        #     self.cleanup()
    
    async def start_main_loop(self):
        self.loop = asyncio.get_running_loop()
        print("[Sistema] Iniciando monitor de teclado...")
        self.keyboard_app.start()

        self.audio_playback_task = asyncio.create_task(
            self.audio_app.task_play_audio(self.audio_in_queue)
        )

        await asyncio.create_task(self.play_current_power_on_message())

        # --- MENU VISUAL ATUALIZADO ---
        print("\n" + "="*45)
        print("      SISTEMA AI-BLIND-HELPER ONLINE      ")
        print("="*45)
        print(" [NAVEGAÇÃO MENU ROLÁVEL]")
        print("  < Esq >    : Navegar Anterior/Próximo")
        print("  [ENTER]    : Confirmar Opção Selecionada")
        print("-" * 45)
        print(" [ATALHOS GLOBAIS]")
        print("  [T]        : Data / Hora")
        print("  [A]        : Hold Áudio (Trava com duplo toque)")
        print("  [V]        : Hold Vídeo (Trava com duplo toque)")
        print("="*45 + "\n")

        try:
            while self.app_running:
                await asyncio.sleep(0.5)
            print("[Sistema] Loop encerrado.")

        except asyncio.CancelledError:
            print("\n[Sistema] Loop interrompido pelo Sistema (Ctrl+C).")

        finally:
            print("\n[Sistema] Iniciando protocolo de desconexão...")
            await self._stop_session_task()
            if self.audio_playback_task:
                self.audio_playback_task.cancel()


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