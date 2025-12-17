import evdev
from manager import KeyboardManager
from config import Config


class KeyboardApplication:
    """
    Responsabilidade:
    - Conectar com o Controller
    - Definir QUAIS teclas fazem O QUE
    - Tratar a lógica (se deve agir no press ou no release)
    - Gerenciar o Menu Rolável
    """

    # --- Configuração das Teclas de Navegação do Menu ---
    # Altere aqui para os códigos do seu hardware se necessário
    KEY_MENU_BACK = evdev.ecodes.KEY_LEFT
    KEY_MENU_FORWARD = evdev.ecodes.KEY_RIGHT
    KEY_MENU_CONFIRM = evdev.ecodes.KEY_ENTER

    def __init__(self, controller, device_path):
        self.controller = controller

        # Instancia o manager (sem modificações)
        self.manager = KeyboardManager(device_path)

        # Estado do Menu
        self.menu_index = 0
        self.menu_active = True  # Se quiser que o menu comece ativo

        # --- Configuração do Dicionário do Menu (W, D, R, Q) ---
        self._setup_menu_structure()

        # Variáveis para controle do hold e lock de audio e video
        self.audio_is_locked = False
        self.audio_pressed = False
        self.video_is_locked = False
        self.video_pressed = False

        # --- Inicia binds de teclas físicas ---
        self._setup_bindings()

    def _setup_menu_structure(self):
        """
        Define o dicionário e a ordem do menu rolável.
        As chaves 'w', 'd', 'r', 'q' mapeiam para descrições e os callbacks existentes.
        """
        self.menu_actions = {
            'w': {
                'description': "Conectar / Desconectar",
                'callback': self.on_key_w
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
                'callback': self.on_key_p
            }
        }

        # Lista ordenada para garantir a navegação: w -> d -> r -> q
        self.menu_order = ['w', 'd', 'r', 'q', 'p']

    def start(self):
        self.manager.start()

    def stop(self):
        self.manager.stop()

    def _setup_bindings(self):
        """Registra as teclas no manager."""

        # --- Teclas de Navegação do Menu ---
        self.manager.register_key(self.KEY_MENU_BACK, self.on_menu_back)
        self.manager.register_key(self.KEY_MENU_FORWARD, self.on_menu_forward)
        self.manager.register_key(self.KEY_MENU_CONFIRM, self.on_menu_confirm)

        # --- Teclas de Acesso Direto (Mantidas conforme original) ---
        self.manager.register_key(evdev.ecodes.KEY_W, self.on_key_w)
        self.manager.register_key(evdev.ecodes.KEY_Q, self.on_key_q)
        self.manager.register_key(evdev.ecodes.KEY_T, self.on_key_t)
        self.manager.register_key(evdev.ecodes.KEY_A, self.on_key_a) 
        self.manager.register_key(evdev.ecodes.KEY_D, self.on_key_d)
        self.manager.register_key(evdev.ecodes.KEY_R, self.on_key_r)

        # Funções de audio control
        self.manager.register_key(evdev.ecodes.KEY_J, self.on_key_j)
        self.manager.register_key(evdev.ecodes.KEY_K, self.on_key_k)
        self.manager.register_key(evdev.ecodes.KEY_L, self.on_key_l)
        

    # --- Lógica do Menu Rolável ---

    def _get_current_menu_item(self):
        key_char = self.menu_order[self.menu_index]
        return self.menu_actions[key_char]

    def _announce_current_selection(self):
        """
        Feedback visual/auditivo ao navegar.
        IMPORTANTE: Adicione aqui a chamada para o seu TTS (self.controller.falar(...))
        """
        item = self._get_current_menu_item()
        msg = f">> [MENU] Selecionado: {item['description']} (Tecla virtual: {
            self.menu_order[self.menu_index].upper()})"
        print(msg)
        # Exemplo: self.controller.speak(item['description'])

    def on_menu_forward(self, event_type, duration):
        if event_type == 'PRESS':
            # Incrementa o índice com loop (volta ao 0 se passar do fim)
            self.menu_index = (self.menu_index + 1) % len(self.menu_order)
            self._announce_current_selection()

    def on_menu_back(self, event_type, duration):
        if event_type == 'PRESS':
            # Decrementa o índice com loop (vai para o último se for < 0)
            self.menu_index = (self.menu_index - 1) % len(self.menu_order)
            self._announce_current_selection()

    def on_menu_confirm(self, event_type, duration):
        if event_type == 'PRESS':
            item = self._get_current_menu_item()
            print(f">> [MENU] Confirmando ação: {item['description']}")

            # Chama a função mapeada simulando um evento 'PRESS' com duração 0
            # Isso reutiliza exatamente a lógica que você já programou abaixo.
            item['callback'](event_type='PRESS', duration=0.0)

    # --- Callbacks Originais (Lógica de Aplicação) ---

    def on_key_w(self, event_type, duration):
        if event_type == 'PRESS':
            print(">> [App] 'W' Action Triggered. Toggle connect...")
            self.controller.handle_toggle_connect()

    def on_key_t(self, event_type, duration):
        if event_type == 'RELEASE':
            if (duration > Config.LOCK_THRESHOLD_MS_DATE):
                print(f">> [App] 'T' Solto após {
                      duration:.2f}ms. Dizendo data...")
                self.controller.handle_date_request()
            else:
                print(f">> [App] 'T' Solto após {
                      duration:.2f}ms. Dizendo horas...")
                self.controller.handle_time_request()

    def on_key_q(self, event_type, duration):
        if event_type == 'PRESS':
            print(">> [App] 'Q' Action Triggered. Quitting...")
            self.controller.handle_quit()

    def on_key_a(self, event_type, duration):
        if event_type == 'PRESS':
            if not self.audio_pressed:
                print("Audio iniciado (A)")
                self.audio_pressed = True
                self.audio_is_locked = False
                self.controller.start_sending_audio_only()
        elif event_type == 'RELEASE':
            if (self.audio_is_locked):
                self.controller.stop_sending_audio()
                print("Audio finalizado (A - UNLOCK)")
                self.audio_pressed = False
            elif duration < Config.LOCK_THRESHOLD_MS_AUDIO:
                print("Audio Lock ativado")
                self.audio_is_locked = True
            else:
                print("Audio Hold finalizado")
                self.controller.stop_sending_audio()
                self.audio_pressed = False
    def on_key_d(self, event_type, duration):
        if event_type == 'PRESS':
            print(">> [App] 'D' Action Triggered.")
            self.controller.handle_description_request()

    def on_key_r(self, event_type, duration):
        if event_type == 'PRESS':
            print(">> [App] 'R' Action Triggered.")
            self.controller.handle_transcription_request()

    def on_key_j(self, event_type, duration):
        if event_type == 'PRESS':
            self.controller.handle_audio_rewind()

    def on_key_k(self, event_type, duration):
        if event_type == 'PRESS':
            self.controller.handle_audio_pause_toggle()

    def on_key_l(self, event_type, duration):
        if event_type == 'PRESS':
            self.controller.handle_audio_forward()
            
    def on_key_p(self, event_type, duration):
        if event_type == 'PRESS':
            self.controller.handle_cycle_language()
