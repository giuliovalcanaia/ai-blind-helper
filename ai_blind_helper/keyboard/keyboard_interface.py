from config import Config
import threading
from event import *
from keymap_gpio import *
# To change to evdev, just replace the above line with:
# from keymap.evdev import *


class KeyboardInterface:

    def __init__(self, event_bus: EventBus, loop_controller, keyboard_controller):
        print("[KeyboardInterface __init__] Initializing keyboard interface and mapping dependencies")
        self.loop_controller = loop_controller
        self.keyboard_controller = keyboard_controller
        
        self.event_bus = event_bus

        self.menu_index = 0
        self.menu_active = True

        self._setup_menu_structure()

        self.audio_is_locked = False
        self.audio_pressed = False
        self.video_is_locked = False
        self.video_pressed = False

        self._setup_bindings()
        
        self.is_blocked = False
        
        self._hold_timers = {}
        self.live_connected = False
        
    def run(self):
        print("[KeyboardInterface run] Running loop_controller")
        self.loop_controller.run()

    def _setup_menu_structure(self):
        print("[KeyboardInterface _setup_menu_structure] Setting up scrollable menu structure")
        self.menu_actions = {
            'w': {
                'description': "Connect / Disconnect Gemini Audio",
                'callback': self.audio_live_connect,
                'on_select': lambda: self.event_bus.emit(MENU_SELECT_AUDIO_LIVE),
                'block': True
            },
            'v': {
                'description': "Connect / Disconnect Gemini Video",
                'callback': self.video_live_connect,
                'on_select': lambda: self.event_bus.emit(MENU_SELECT_VIDEO_LIVE),
                'block': True
            },
            'd': {
                'description': "Describe Surroundings",
                'callback': self.handle_describe_surroundings,
                'on_select': lambda: self.event_bus.emit(MENU_SELECT_DESCRIBE),
                'block': True
            },
            'r': {
                'description': "Transcribe Text",
                'callback': self.handle_transcript_text,
                'on_select': lambda: self.event_bus.emit(MENU_SELECT_TRANSCRIBE),
                'block': True
            },
            'q': {
                'description': "Log out",
                'callback': self.handle_quit_request,
                'on_select': lambda: self.event_bus.emit(MENU_SELECT_EXIT),
                'block': False
            },
            'p': {
                'description': "Change Language",
                'callback': self.handle_change_language,
                'on_select': lambda: self.event_bus.emit(MENU_SELECT_CHANGE_LANGUAGE),
                'block': False
            }
        }
        self.menu_order = ['w', 'v', 'd', 'r', 'p']

    def start(self):
        print("[KeyboardInterface start] Starting KeyboardController")
        self.event_bus.emit(KB_START)

    def stop(self):
        print("[KeyboardInterface stop] Stoping KeyboardController")
        self.event_bus.emit(KB_STOP)

    def _setup_bindings(self):
        print("[KeyboardInterface _setup_bindings] Binding key bindings")
        self.keyboard_controller.register_key(self.KEY_MENU_BACK, self.on_menu_back)
        self.keyboard_controller.register_key(self.KEY_MENU_FORWARD, self.on_menu_forward)
        self.keyboard_controller.register_key(self.KEY_MENU_CONFIRM, self.on_menu_confirm)

        self.keyboard_controller.register_key(KEY_QUIT, self.handle_quit_request)
        self.keyboard_controller.register_key(KEY_TIME_REQUEST, self.on_time_request)
        self.keyboard_controller.register_key(KEY_AUDIO_REQUEST, self.on_audio_request)


    def _get_current_menu_item(self):
        key_char = self.menu_order[self.menu_index]
        return self.menu_actions[key_char]

    def _display_current_selected(self):
        
        item = self._get_current_menu_item()
        print(f">> [MENU] Selected: {item['description']} (VirtualKey: {self.menu_order[self.menu_index].upper()})")
        if 'on_select' in item and callable(item['on_select']):
            try:
                item['on_select']()
            except Exception as e:
                print(f"Error playing audio from the menu: {e}")

    def on_menu_forward(self, event_type, duration):
        if not self.is_blocked:
            if event_type == 'PRESS':
                print("[KeyboardInterface on_menu_forward] Navigating forward in the menu")
                self.menu_index = (self.menu_index + 1) % len(self.menu_order)
                self._display_current_selected()
                
        else:
            print("[KeyboardInterface on_menu_forward] Menu blocked")

    def on_menu_back(self, event_type, duration):
        if not self.is_blocked:
            if event_type == 'PRESS':
                print("[KeyboardInterface on_menu_back] Navigating rewind in the menu")
                self.menu_index = (self.menu_index - 1) % len(self.menu_order)
                self._display_current_selected()
        else:
            print("[KeyboardInterface on_menu_forward] Menu blocked")

    def on_menu_confirm(self, event_type, duration):
        if event_type == 'PRESS':
            item = self._get_current_menu_item()
            if item.get('block', False):
                print(f"[KeyboardInterface] Item '{item['description']}' activated navigation lock.")
                self.is_blocked = True
            print(f"[KeyboardInterface on_menu_confirm] Confirming action: {item['description']}")
            item['callback'](event_type='PRESS', duration=0.0)

    def audio_live_connect(self, event_type, duration):
        if event_type == 'PRESS':
            print("[KeyboardInterface audio_live_connect] Toggling audio connection")
            self.event_bus.emit(SESSION_AUDIO_LIVE_CONNECT_TOGGLE)
            self.live_connected = not self.live_connected
            self.is_blocked = not self.is_blocked

    def video_live_connect(self, event_type, duration):
        if event_type == 'PRESS':
            print("[KeyboardInterface video_live_connect] Toggling video connection")
            self.event_bus.emit(SESSION_VIDEO_LIVE_CONNECT_TOGGLE)
            self.live_connected = not self.live_connected
            self.is_blocked = not self.is_blocked
            



    def on_time_request(self, event_type, duration):
        key_code = KEY_TIME_REQUEST
        if event_type == 'PRESS':
            self._start_hold_timer(key_code, Config.LOCK_THRESHOLD_MS_AUDIO)
        if event_type == 'RELEASE':
            self._cancel_hold_timer(key_code)
            if (duration > Config.LOCK_THRESHOLD_MS_DATE):
                print(f"[KeyboardInterface on_key_t] Long press detected ({duration:.2f}ms). Requesting date")
                self.event_bus.emit(DATE_REQUEST)
            else:
                print(f"[KeyboardInterface on_key_t] Short press detected ({duration:.2f}ms). Requesting time")
                self.event_bus.emit(TIME_REQUEST)

    def handle_quit_request(self, event_type, duration):
        if event_type == 'PRESS':
            print("[KeyboardInterface on_key_q] Quit command triggered")
            self.handle_quit()

    def on_audio_request(self, event_type, duration):
        key_code = KEY_AUDIO_REQUEST
        if event_type == 'PRESS':
            self._start_hold_timer(key_code, Config.LOCK_THRESHOLD_MS_AUDIO)
            if not self.audio_pressed:
                print(
                    "[KeyboardInterface on_key_a] Starting audio send (Hold/Lock)")
                self.event_bus.emit(SFX_AUDIO_BUTTON_PRESS)
                self.audio_pressed = True
                self.audio_is_locked = False
                self.event_bus.emit(SESSION_START_AUDIO_STREAM)
        elif event_type == 'RELEASE':
            self._cancel_hold_timer(key_code)
            if (self.audio_is_locked):
                print("[KeyboardInterface on_key_a] Unlocking fixed audio")
                self.event_bus.emit(SESSION_STOP_AUDIO_STREAM)
                self.event_bus.emit(SFX_AUDIO_BUTTON_RELEASE)
                self.audio_pressed = False
            elif duration < Config.LOCK_THRESHOLD_MS_AUDIO:
                print(
                    "[KeyboardInterface on_key_a] Short press detected: Locking audio (Lock)")
                self.audio_is_locked = True
            else:
                print(
                    "[KeyboardInterface on_key_a] Key release detected: Ending audio hold")
                self.event_bus.emit(SESSION_STOP_AUDIO_STREAM)
                self.event_bus.emit(SFX_AUDIO_BUTTON_RELEASE)
                self.audio_pressed = False

    def handle_describe_surroundings(self, event_type, duration):
        if event_type == 'PRESS':
            print("[KeyboardInterface handle_describe_surroundings] Requesting environment description")
            self.event_bus.emit(DESCRIPTION_REQUEST)

    def handle_transcript_text(self, event_type, duration):
        if event_type == 'PRESS':
            print("[KeyboardInterface handle_transcript_text] Requesting text transcription")
            self.event_bus.emit(TRANSCRIPTION_REQUEST)

    def handle_rewind(self, event_type, duration):
        if event_type == 'PRESS':
            print("[KeyboardInterface handle_rewind] Rewind command triggered")
            self.event_bus.emit(AUDIO_REWIND)

    def handle_pause_toggle(self, event_type, duration):
        if event_type == 'PRESS':
            print("[KeyboardInterface handle_pause_toggle] Pause toggle command triggered")
            self.event_bus.emit(AUDIO_PAUSE_TOGGLE)

    def handle_forward(self, event_type, duration):
        if event_type == 'PRESS':
            print("[KeyboardInterface handle_forward] Forward command triggered")
            self.event_bus.emit(AUDIO_FORWARD)

    def handle_change_language(self, event_type, duration):
        if event_type == 'PRESS':
            print("[KeyboardInterface handle_change_language] Requesting language rotation")
            self.event_bus.emit(LANGUAGE_CYCLE)
            self.language_controller.handle_cycle_language()

    def handle_quit(self):
        print("[KeyboardInterface handle_quit] Initiating system shutdown")
        self.loop_controller.stop_running()
        self.event_bus.emit(SESSION_STOP)
        


    def _trigger_hold_sound(self):
        """Function called when the hold timer expires."""
        print("[KeyboardInterface] HOLD time reached! Playing sound.")
        self.event_bus.emit(SFX_HOLD_BUTTON_PRESS)

    def _start_hold_timer(self, key_code, threshold_ms):
        self._cancel_hold_timer(key_code)
        timer = threading.Timer(threshold_ms / 1000.0, self._trigger_hold_sound)
        self._hold_timers[key_code] = timer
        timer.start()

    def _cancel_hold_timer(self, key_code):
        timer = self._hold_timers.pop(key_code, None)
        if timer:
            timer.cancel()
            print(f"[KeyboardInterface] Timer for key {key_code} cancelled.")