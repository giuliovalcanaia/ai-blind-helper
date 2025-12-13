import time
import evdev
import threading
# --- Mapeamento Auxiliar (Opcional, apenas para debug visual) ---
def get_key_name(code):
    return evdev.ecodes.KEY.get(code, f"UNK_{code}")

class KeyboardManager:
    """
    Responsabilidade: 
    - Ler o hardware (/dev/input/...)
    - Calcular duração de pressionamento
    - Gerenciar Thread de leitura
    - Chamar os callbacks registrados
    """
    def __init__(self, device_path):
        self.device_path = device_path
        self.device = None
        self.stop_event = threading.Event()
        self.listener_thread = None
        
        # Buffer para calcular duração: { key_code: timestamp_start }
        self.active_keys = {}
        
        # Registro de callbacks: { key_code: function_callback }
        self.callbacks = {}

    def register_key(self, key_code, callback):
        """
        A Application usa isso para dizer quais teclas quer ouvir.
        O callback deve aceitar: (event_type, duration)
        """
        self.callbacks[key_code] = callback
        print(f"[Manager] Tecla {get_key_name(key_code)} registrada.")

    def start(self):
        """Inicia a escuta em background."""
        try:
            self.device = evdev.InputDevice(self.device_path)
            self.listener_thread = threading.Thread(target=self._loop, daemon=True)
            self.listener_thread.start()
            print(f"[Manager] Escutando device: {self.device.name}")
        except FileNotFoundError:
            print(f"[Manager] ERRO: Device {self.device_path} não encontrado.")
        except Exception as e:
            print(f"[Manager] ERRO ao iniciar: {e}")

    def stop(self):
        self.stop_event.set()

    def _loop(self):
        """Loop interno de leitura do Kernel."""
        print("[Manager] Loop iniciado.")
        
        # O read_loop bloqueia, então usamos um select ou checagem simples.
        # Como é daemon thread, se o programa principal morrer, isso morre junto.
        try:
            for event in self.device.read_loop():
                if self.stop_event.is_set():
                    break
                
                if event.type == evdev.ecodes.EV_KEY:
                    self._process_event(event)
        except Exception as e:
            print(f"[Manager] Loop interrompido: {e}")

    def _process_event(self, event):
        # Se a tecla não foi registrada pela App, ignoramos
        if event.code not in self.callbacks:
            return

        callback = self.callbacks[event.code]

        # 1. PRESS (Desceu a tecla)
        if event.value == 1: 
            self.active_keys[event.code] = time.time()
            # Notifica a App que foi pressionado (duração 0)
            callback(event_type='PRESS', duration=0.0)

        # 0. RELEASE (Soltou a tecla)
        elif event.value == 0:
            start_time = self.active_keys.pop(event.code, None)
            duration = 0.0
            if start_time:
                duration = time.time() - start_time
            
            # Notifica a App que foi solto com a duração calculada
            callback(event_type='RELEASE', duration=duration)