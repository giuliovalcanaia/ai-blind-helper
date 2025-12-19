import evdev
import asyncio
from manager import KeyboardManager
from config import Config

class KeyboardApplication:
    def __init__(self, keyboard_manager):
        print(f"[KeyboardApplication __init__] Inicializando aplicação de teclado com gerenciador: {keyboard_manager}")
        self.keyboard_manager = keyboard_manager
        
    def start(self):
        print("[KeyboardApplication start] Solicitando início do monitoramento de hardware via keyboard_manager")
        self.keyboard_manager.start()
        print("[KeyboardApplication start] Monitoramento de hardware iniciado")
        
    def stop(self):
        print("[KeyboardApplication stop] Solicitando parada do monitoramento de hardware")
        self.keyboard_manager.stop()
        print("[KeyboardApplication stop] Monitoramento de hardware encerrado")
        
    def register_key(self, key_code, callback):
        print(f"[KeyboardApplication register_key] Vinculando código de tecla {key_code} ao callback fornecido")
        self.keyboard_manager.register_key(key_code, callback)
        print(f"[KeyboardApplication register_key] Registro da tecla {key_code} concluído")
