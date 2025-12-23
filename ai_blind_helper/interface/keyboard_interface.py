import evdev
from config import Config
import threading


class KeyboardInterface:

    KEY_MENU_BACK = evdev.ecodes.KEY_LEFT
    KEY_MENU_FORWARD = evdev.ecodes.KEY_RIGHT
    KEY_MENU_CONFIRM = evdev.ecodes.KEY_ENTER

    def __init__(self, loop_controller, keyboard_controller, session_controller, language_controller, time_controller, transcription_controller, description_controller, audio_controller, menu_controller, sfx_controller, turn_controller):
        print("[KeyboardInterface __init__] Inicializando interface de teclado e mapeando dependências")
        self.keyboard_controller = keyboard_controller
        self.language_controller = language_controller
        self.session_controller = session_controller
        self.loop_controller = loop_controller
        self.time_controller = time_controller
        self.transcription_controller = transcription_controller
        self.description_controller = description_controller
        self.audio_controller = audio_controller
        self.menu_controller = menu_controller
        self.sfx_controller = sfx_controller
        self.turn_controller = turn_controller

        self.menu_index = 0
        self.menu_active = True

        self._setup_menu_structure()

        self.audio_is_locked = False
        self.audio_pressed = False
        self.video_is_locked = False
        self.video_pressed = False

        self._setup_bindings()
        
        self.blocked = False
        self.turn_blocked = False 
        
        # Dicionário literal para rastrear os timers: { código_da_tecla: objeto_timer }
        self._hold_timers = {}
        
        # Flags para controle do menu em cada aplicação
        self.live_connected = False
        self.turn_connected = False
        
    def run(self):
        print("[KeyboardInterface run] Repassando execução para o LoopController")
        self.loop_controller.run()

    def _setup_menu_structure(self):
        print(
            "[KeyboardInterface _setup_menu_structure] Configurando estrutura do menu rolável")
        self.menu_actions = {
            'w': {
                'description': "Conectar / Desconectar Gemini Audio",
                'callback': self.audio_live_connect,
                'on_select': lambda: self.menu_controller.play_menu_websocket_audio(),
                'block': True
            },
            'v': {
                'description': "Conectar / Desconectar Gemini Video",
                'callback': self.video_live_connect,
                'on_select': lambda: self.menu_controller.play_menu_websocket_video(),
                'block': True
            },
            'd': {
                'description': "Descrever Ambiente",
                'callback': self.on_key_d,
                'on_select': lambda: self.menu_controller.play_menu_describe(),
                'block': True
            },
            'r': {
                'description': "Ler / Transcrever",
                'callback': self.on_key_r,
                'on_select': lambda: self.menu_controller.play_menu_transcribe(),
                'block': True
            },
            'q': {
                'description': "Sair do Sistema",
                'callback': self.on_key_q,
                'on_select': lambda: self.menu_controller.play_menu_exit(),
                'block': False
            },
            'p': {
                'description': "Mudar idioma",
                'callback': self.change_language,
                'on_select': lambda: self.menu_controller.play_menu_change_language(),
                'block': False
            },
            't': {
                'description': "Conectar Gemini de Turnos",
                'callback': self.audio_turn_connect,
                'on_select': lambda: self.menu_controller.play_menu_websocket_turn(),
                'block': True
            }
        }
        self.menu_order = ['w', 'v', 't', 'p']

    def start(self):
        print("[KeyboardInterface start] Iniciando KeyboardController")
        self.keyboard_controller.start()

    def stop(self):
        print("[KeyboardInterface stop] Parando KeyboardController")
        self.keyboard_controller.stop()

    def _setup_bindings(self):
        print(
            "[KeyboardInterface _setup_bindings] Registrando atalhos de teclado físicos")
        self.keyboard_controller.register_key(
            self.KEY_MENU_BACK, self.on_menu_back)
        self.keyboard_controller.register_key(
            self.KEY_MENU_FORWARD, self.on_menu_forward)
        self.keyboard_controller.register_key(
            self.KEY_MENU_CONFIRM, self.on_menu_confirm)

        self.keyboard_controller.register_key(
            evdev.ecodes.KEY_Q, self.on_key_q)
        self.keyboard_controller.register_key(
            evdev.ecodes.KEY_T, self.on_key_t)
        self.keyboard_controller.register_key(
            evdev.ecodes.KEY_A, self.on_key_a)

        # self.keyboard_controller.register_key(evdev.ecodes.KEY_J, self.on_key_j)
        # self.keyboard_controller.register_key(evdev.ecodes.KEY_K, self.on_key_k)
        # self.keyboard_controller.register_key(evdev.ecodes.KEY_L, self.on_key_l)

    def _get_current_menu_item(self):
        key_char = self.menu_order[self.menu_index]
        return self.menu_actions[key_char]

    def _announce_current_selection(self):
        """
        Feedback visual/auditivo ao navegar.
        Puxa o runnable de audio do dicionário e executa.
        """
        # 1. Pega o item atual baseando-se no index
        item = self._get_current_menu_item()
        # 2. Feedback Visual (Log)
        msg = f">> [MENU] Selecionado: {item['description']} (Tecla virtual: {
            self.menu_order[self.menu_index].upper()})"
        print(msg)
        # 3. Feedback Auditivo (Executa o runnable configurado)
        if 'on_select' in item and callable(item['on_select']):
            try:
                # Aqui ele "puxa o runnable e roda"
                item['on_select']()
            except Exception as e:
                print(f"Erro ao executar audio do menu: {e}")

    def on_menu_forward(self, event_type, duration):
        if not self.blocked:
            if event_type == 'PRESS':
                print("[KeyboardInterface on_menu_forward] Navegando para frente no menu")
                self.menu_index = (self.menu_index + 1) % len(self.menu_order)
                self._announce_current_selection()
                
        else:
            print("[KeyboardInterface on_menu_forward] Menu bloqueado")

    def on_menu_back(self, event_type, duration):
        if not self.blocked:
            if event_type == 'PRESS':
                print("[KeyboardInterface on_menu_back] Navegando para trás no menu")
                self.menu_index = (self.menu_index - 1) % len(self.menu_order)
                self._announce_current_selection()
        else:
            print("[KeyboardInterface on_menu_forward] Menu bloqueado")

    def on_menu_confirm(self, event_type, duration):
        if event_type == 'PRESS':
            item = self._get_current_menu_item()
            # Lógica de bloqueio: verifica se o item selecionado exige bloqueio
            if item.get('block', False):
                print(f"[KeyboardInterface] Item '{item['description']}' ativou o bloqueio de navegação.")
                self.blocked = True
            print(f"[KeyboardInterface on_menu_confirm] Confirmando ação: {item['description']}")
            item['callback'](event_type='PRESS', duration=0.0)

    def audio_live_connect(self, event_type, duration):
        if event_type == 'PRESS':
            print("[KeyboardInterface audio_live_connect] Acionando alternância de conexão de áudio")
            self.session_controller.handle_audio_live_connect()
            self.live_connected = not self.live_connected
            self.blocked = not self.blocked

    def video_live_connect(self, event_type, duration):
        if event_type == 'PRESS':
            print("[KeyboardInterface video_live_connect] Acionando alternância de conexão de vídeo")
            self.session_controller.handle_video_live_connect()
            self.live_connected = not self.live_connected
            self.blocked = not self.blocked
            
    def audio_turn_connect(self, event_type, duration):
        if event_type == 'PRESS':
            self.turn_controller.handle_audio_live_connect()
            self.turn_connected = not self.turn_connected
            self.blocked = not self.blocked
            self.turn_blocked = False
            



    def on_key_t(self, event_type, duration):
        key_code = evdev.ecodes.KEY_T
        if event_type == 'PRESS':
            self._start_hold_timer(key_code, Config.LOCK_THRESHOLD_MS_AUDIO)
        if event_type == 'RELEASE':
            self._cancel_hold_timer(key_code)
            if (duration > Config.LOCK_THRESHOLD_MS_DATE):
                print(f"[KeyboardInterface on_key_t] Long press detectado ({
                      duration:.2f}ms). Solicitando data")
                self.time_controller.handle_date_request()
            else:
                print(f"[KeyboardInterface on_key_t] Short press detectado ({
                      duration:.2f}ms). Solicitando horas")
                self.time_controller.handle_time_request()

    def on_key_q(self, event_type, duration):
        if event_type == 'PRESS':
            print("[KeyboardInterface on_key_q] Comando de saída disparado")
            self.handle_quit()

    def on_key_a(self, event_type, duration):
        if self.turn_connected and self.turn_blocked:
            return
        if self.turn_connected:
            key_code = evdev.ecodes.KEY_1
            if event_type == 'PRESS':
                self._start_hold_timer(key_code, Config.LOCK_THRESHOLD_MS_AUDIO)
                if not self.audio_pressed:
                    print(
                        "[KeyboardInterface on_key_a] Iniciando envio de áudio (Hold/Lock)")
                    self.sfx_controller.audio_button_press()
                    self.audio_pressed = True
                    self.audio_is_locked = False
                    self.turn_controller.start_sending_audio_only()
            elif event_type == 'RELEASE':
                self._cancel_hold_timer(key_code)
                if (self.audio_is_locked):
                    print("[KeyboardInterface on_key_a] Destravando áudio fixo")
                    self.turn_controller.stop_sending_audio()
                    self.sfx_controller.audio_button_release()
                    self.audio_pressed = False
                    self.lock_turn()
                elif duration < Config.LOCK_THRESHOLD_MS_AUDIO:
                    print(
                        "[KeyboardInterface on_key_a] Curto toque detectado: Travando áudio (Lock)")
                    self.audio_is_locked = True
                else:
                    print(
                        "[KeyboardInterface on_key_a] Soltura de tecla detectada: Finalizando Hold de áudio")
                    self.turn_controller.stop_sending_audio()
                    self.sfx_controller.audio_button_release()
                    self.audio_pressed = False 
                    self.lock_turn()
        else:
            key_code = evdev.ecodes.KEY_1
            if event_type == 'PRESS':
                self._start_hold_timer(key_code, Config.LOCK_THRESHOLD_MS_AUDIO)
                if not self.audio_pressed:
                    print(
                        "[KeyboardInterface on_key_a] Iniciando envio de áudio (Hold/Lock)")
                    self.sfx_controller.audio_button_press()
                    self.audio_pressed = True
                    self.audio_is_locked = False
                    self.session_controller.start_sending_audio_only()
            elif event_type == 'RELEASE':
                self._cancel_hold_timer(key_code)
                if (self.audio_is_locked):
                    print("[KeyboardInterface on_key_a] Destravando áudio fixo")
                    self.session_controller.stop_sending_audio()
                    self.sfx_controller.audio_button_release()
                    self.audio_pressed = False
                elif duration < Config.LOCK_THRESHOLD_MS_AUDIO:
                    print(
                        "[KeyboardInterface on_key_a] Curto toque detectado: Travando áudio (Lock)")
                    self.audio_is_locked = True
                else:
                    print(
                        "[KeyboardInterface on_key_a] Soltura de tecla detectada: Finalizando Hold de áudio")
                    self.session_controller.stop_sending_audio()
                    self.sfx_controller.audio_button_release()
                    self.audio_pressed = False

    def on_key_d(self, event_type, duration):
        if event_type == 'PRESS':
            print("[KeyboardInterface on_key_d] Solicitando descrição de ambiente")
            self.session_controller.handle_description_request()

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
        
        
        
    # Lógica dos botões de hold
        
    def _trigger_hold_sound(self):
        """Função que será chamada quando o tempo de hold expirar."""
        print("[KeyboardInterface] Tempo de HOLD atingido! Disparando som.")
        self.sfx_controller.hold_button_press_sfx() 

    def _start_hold_timer(self, key_code, threshold_ms):
        # 1. Se já existir um timer para essa tecla, cancela (segurança)
        self._cancel_hold_timer(key_code)
        
        # 2. Cria um novo timer
        # threading.Timer recebe (tempo_em_segundos, função_para_rodar)
        timer = threading.Timer(threshold_ms / 1000.0, self._trigger_hold_sound)
        
        # 3. Guarda e inicia
        self._hold_timers[key_code] = timer
        timer.start()

    def _cancel_hold_timer(self, key_code):
        # Busca o timer no dicionário e o remove ao mesmo tempo
        timer = self._hold_timers.pop(key_code, None)
        if timer:
            timer.cancel()
            print(f"[KeyboardInterface] Timer da tecla {key_code} cancelado.")

    # Dentro da classe KeyboardInterface

    def lock_turn(self):
        print("[KeyboardInterface] Turno bloqueado: IA processando/falando...")
        self.turn_blocked = True

    def unlock_turn(self):
        print("[KeyboardInterface] Turno liberado: Pode falar agora.")
        self.turn_blocked = False
        # Opcional: tocar um som de "beep" para avisar o usuário que ele pode falar
        self.sfx_controller.hold_button_press_sfx()