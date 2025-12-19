import evdev
from config import Config

class KeyboardInterface:

    KEY_MENU_BACK = evdev.ecodes.KEY_LEFT
    KEY_MENU_FORWARD = evdev.ecodes.KEY_RIGHT
    KEY_MENU_CONFIRM = evdev.ecodes.KEY_ENTER

    def __init__(self, loop_controller, keyboard_controller, session_controller, language_controller, time_controller, transcription_controller, description_controller, audio_controller):
        print("[KeyboardInterface __init__] Inicializando interface de teclado e mapeando dependências")
        self.keyboard_controller = keyboard_controller
        self.language_controller = language_controller
        self.session_controller = session_controller
        self.loop_controller = loop_controller
        self.time_controller = time_controller
        self.transcription_controller = transcription_controller
        self.description_controller = description_controller
        self.audio_controller = audio_controller

        self.menu_index = 0
        self.menu_active = True 

        self._setup_menu_structure()

        self.audio_is_locked = False
        self.audio_pressed = False
        self.video_is_locked = False
        self.video_pressed = False

        self._setup_bindings()

    def run(self):
        print("[KeyboardInterface run] Repassando execução para o LoopController")
        self.loop_controller.run()

    def _setup_menu_structure(self):
        print("[KeyboardInterface _setup_menu_structure] Configurando estrutura do menu rolável")
        self.menu_actions = {
            'w': {
                'description': "Conectar / Desconectar Audio Live",
                'callback': self.audio_live_connect
            },
            'v': {
                'description': "Conectar / Desconectar Video Live",
                'callback': self.video_live_connect
            },
            'd': {
                'description': "Descrever Ambiente",
                'callback': self.on_key_d
            },
            'r': {
                'description': "Ler / Transcrever",
                'callback': self.on_key_r
            },
            'q': {
                'description': "Sair do Sistema",
                'callback': self.on_key_q
            },
            'p': {
                'description': "Mudar idioma",
                'callback': self.change_language
            }
        }
        self.menu_order = ['w', 'v', 'd', 'r', 'q', 'p']

    def start(self):
        print("[KeyboardInterface start] Iniciando KeyboardController")
        self.keyboard_controller.start()

    def stop(self):
        print("[KeyboardInterface stop] Parando KeyboardController")
        self.keyboard_controller.stop()

    def _setup_bindings(self):
        print("[KeyboardInterface _setup_bindings] Registrando atalhos de teclado físicos")
        self.keyboard_controller.register_key(self.KEY_MENU_BACK, self.on_menu_back)
        self.keyboard_controller.register_key(self.KEY_MENU_FORWARD, self.on_menu_forward)
        self.keyboard_controller.register_key(self.KEY_MENU_CONFIRM, self.on_menu_confirm)

        self.keyboard_controller.register_key(evdev.ecodes.KEY_Q, self.on_key_q)
        self.keyboard_controller.register_key(evdev.ecodes.KEY_T, self.on_key_t)
        self.keyboard_controller.register_key(evdev.ecodes.KEY_A, self.on_key_a) 

        self.keyboard_controller.register_key(evdev.ecodes.KEY_J, self.on_key_j)
        self.keyboard_controller.register_key(evdev.ecodes.KEY_K, self.on_key_k)
        self.keyboard_controller.register_key(evdev.ecodes.KEY_L, self.on_key_l)

    def _get_current_menu_item(self):
        key_char = self.menu_order[self.menu_index]
        return self.menu_actions[key_char]

    def _announce_current_selection(self):
        item = self._get_current_menu_item()
        print(f"[KeyboardInterface _announce_current_selection] Menu selecionado: {item['description']} (Tecla: {self.menu_order[self.menu_index].upper()})")

    def on_menu_forward(self, event_type, duration):
        if event_type == 'PRESS':
            print("[KeyboardInterface on_menu_forward] Navegando para frente no menu")
            self.menu_index = (self.menu_index + 1) % len(self.menu_order)
            self._announce_current_selection()

    def on_menu_back(self, event_type, duration):
        if event_type == 'PRESS':
            print("[KeyboardInterface on_menu_back] Navegando para trás no menu")
            self.menu_index = (self.menu_index - 1) % len(self.menu_order)
            self._announce_current_selection()

    def on_menu_confirm(self, event_type, duration):
        if event_type == 'PRESS':
            item = self._get_current_menu_item()
            print(f"[KeyboardInterface on_menu_confirm] Confirmando ação: {item['description']}")
            item['callback'](event_type='PRESS', duration=0.0)

    def audio_live_connect(self, event_type, duration):
        if event_type == 'PRESS':
            print("[KeyboardInterface audio_live_connect] Acionando alternância de conexão de áudio")
            self.session_controller.handle_audio_live_connect()

    def video_live_connect(self, event_type, duration):
        if event_type == 'PRESS':
            print("[KeyboardInterface video_live_connect] Acionando alternância de conexão de vídeo")
            self.session_controller.handle_video_live_connect()

    def on_key_t(self, event_type, duration):
        if event_type == 'RELEASE':
            if (duration > Config.LOCK_THRESHOLD_MS_DATE):
                print(f"[KeyboardInterface on_key_t] Long press detectado ({duration:.2f}ms). Solicitando data")
                self.time_controller.handle_date_request()
            else:
                print(f"[KeyboardInterface on_key_t] Short press detectado ({duration:.2f}ms). Solicitando horas")
                self.time_controller.handle_time_request()

    def on_key_q(self, event_type, duration):
        if event_type == 'PRESS':
            print("[KeyboardInterface on_key_q] Comando de saída disparado")
            self.handle_quit()

    def on_key_a(self, event_type, duration):
        if event_type == 'PRESS':
            if not self.audio_pressed:
                print("[KeyboardInterface on_key_a] Iniciando envio de áudio (Hold/Lock)")
                self.audio_pressed = True
                self.audio_is_locked = False
                self.session_controller.start_sending_audio_only()
        elif event_type == 'RELEASE':
            if (self.audio_is_locked):
                print("[KeyboardInterface on_key_a] Destravando áudio fixo")
                self.session_controller.stop_sending_audio()
                self.audio_pressed = False
            elif duration < Config.LOCK_THRESHOLD_MS_AUDIO:
                print("[KeyboardInterface on_key_a] Curto toque detectado: Travando áudio (Lock)")
                self.audio_is_locked = True
            else:
                print("[KeyboardInterface on_key_a] Soltura de tecla detectada: Finalizando Hold de áudio")
                self.session_controller.stop_sending_audio()
                self.audio_pressed = False

    def on_key_d(self, event_type, duration):
        if event_type == 'PRESS':
            print("[KeyboardInterface on_key_d] Solicitando descrição de ambiente")
            self.description_controller.handle_description_request()

    def on_key_r(self, event_type, duration):
        if event_type == 'PRESS':
            print("[KeyboardInterface on_key_r] Solicitando transcrição de texto")
            self.transcription_controller.handle_transcription_request()

    def on_key_j(self, event_type, duration):
        if event_type == 'PRESS':
            print("[KeyboardInterface on_key_j] Comando rewind disparado")
            self.audio_controller.handle_audio_rewind()

    def on_key_k(self, event_type, duration):
        if event_type == 'PRESS':
            print("[KeyboardInterface on_key_k] Comando pause toggle disparado")
            self.audio_controller.handle_audio_pause_toggle()

    def on_key_l(self, event_type, duration):
        if event_type == 'PRESS':
            print("[KeyboardInterface on_key_l] Comando forward disparado")
            self.audio_controller.handle_audio_forward()
            
    def change_language(self, event_type, duration):
        if event_type == 'PRESS':
            print("[KeyboardInterface change_language] Solicitando rotação de idioma")
            self.language_controller.handle_cycle_language()

    def handle_quit(self):
        print("[KeyboardInterface handle_quit] Iniciando encerramento do sistema")
        self.loop_controller.stop_running()
        self.session_controller.stop_session()