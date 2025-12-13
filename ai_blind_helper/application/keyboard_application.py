import evdev
from manager import KeyboardManager
from config import Config

class KeyboardApplication:
    """
    Responsabilidade:
    - Conectar com o Controller
    - Definir QUAIS teclas fazem O QUE
    - Tratar a lógica (se deve agir no press ou no release)
    """
    def __init__(self, controller, device_path):
        self.controller = controller
        
        # Instancia o manager
        self.manager = KeyboardManager(device_path)
        
        # --- AQUI VOCÊ INICIA AS KEYS QUE SERÃO UTILIZADAS ---
        self._setup_bindings()
        
        
        # Variáveis para controle do hold e lock de audio e video
        self.audio_is_locked = False
        self.audio_pressed = False
        self.video_is_locked = False
        self.video_pressed = False


    def start(self):
        self.manager.start()

    def stop(self):
        self.manager.stop()

    def _setup_bindings(self):
        """Registra as teclas no manager apontando para funções locais."""
        
        # Exemplo 1: Tecla W (Ação imediata ao pressionar)
        self.manager.register_key(evdev.ecodes.KEY_W, self.on_key_w)
        
        # Exemplo 2: Tecla Q (Sair)
        self.manager.register_key(evdev.ecodes.KEY_Q, self.on_key_q)
        
        # Exemplo 3: Tecla T (Ação baseada no tempo ao soltar)
        self.manager.register_key(evdev.ecodes.KEY_T, self.on_key_t)
        
        # Exemplo 4: Tecla A (Ação baseada em hold / lock)
        self.manager.register_key(evdev.ecodes.KEY_A, self.on_key_a)

        # Exemplo 5: Tecla V (Ação baseada em hold / lock)
        self.manager.register_key(evdev.ecodes.KEY_V, self.on_key_v)

    # --- Tratamento dos Eventos ---

    def on_key_w(self, event_type, duration):
        # Lógica: Quero que aconteça assim que eu aperto (PRESS)
        if event_type == 'PRESS':
            print(">> [App] 'W' Pressionado. Iniciando toggle_connect...")
            self.controller.handle_toggle_connect()

    def on_key_t(self, event_type, duration):
        # Lógica: Quero que aconteça quando solto (RELEASE) e preciso do tempo
        if event_type == 'RELEASE':
            print(f">> [App] 'T' Solto após {duration:.2f}s. Enviando tempo...")
            self.controller.handle_time_request(duration)

    def on_key_q(self, event_type, duration):
        # Lógica: Quero que aconteça assim que eu aperto (PRESS)
        if event_type == 'PRESS':
            self.controller.handle_quit()
            
    def on_key_a(self, event_type, duration):
        if event_type == 'PRESS':
            if not self.audio_pressed:
                print("Audio iniciado com tecla A, considerando a princípio como HOLD")
                self.audio_pressed = True
                self.audio_is_locked = False
                self.controller.start_sending_audio_only()
        elif event_type == 'RELEASE':
            if (self.audio_is_locked):
                self.controller.stop_sending_audio()
                print("Audio finalizado com tecla A UNLOCK")
                self.audio_pressed = False
            elif duration < Config.LOCK_THRESHOLD_MS_AUDIO:
                print("Modo Lock ativado")
                self.audio_is_locked = True
            else:
                print("Modo hold funcionou e foi enviado")
                self.controller.stop_sending_audio() 
        
    def on_key_v(self, event_type, duration):
        if event_type == 'PRESS':
            if not self.video_pressed:
                print("Video iniciado com tecla V, considerando a princípio como HOLD")
                self.video_pressed = True
                self.video_is_locked = False
                self.controller.start_sending_audio_video()
        elif event_type == 'RELEASE':
            if (self.video_is_locked):
                if (self.audio_is_locked() or self.audio_pressed):
                    self.controller.stop_sending_video()
                else:
                    self.controller.stop_all_sending()
                print("Video finalizado com tecla V UNLOCK")
                self.video_pressed = False
            elif duration < Config.LOCK_THRESHOLD_MS_VIDEO:
                print("Modo Lock ativado")
                self.video_is_locked = True
            else:
                print("Modo hold funcionou e foi enviado")
                if (self.audio_is_locked or self.audio_pressed):
                    self.controller.stop_sending_video()
                else:
                    self.controller.stop_all_sending()