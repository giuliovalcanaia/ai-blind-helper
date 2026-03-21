from config import Config
from event import (EventBus, LANGUAGE_CYCLE)

class LanguageController:
    def __init__(self, clock_app, date_app, msg_app, audio_menu, event_bus: EventBus):
        print(f"[LanguageController __init__] Initializing language controller")
        self.clock_app = clock_app
        self.date_app = date_app
        self.msg_app = msg_app
        self.audio_menu = audio_menu
        
        event_bus.subscribe(
            LANGUAGE_CYCLE,
            self.handle_cycle_language
        )
    
    def set_system_language(self, new_lang: str):
        print(f"[LanguageController set_system_language] Requested language change to: {new_lang}")
        
        if new_lang == Config.LANGUAGE:
            print(f"[LanguageController set_system_language] Language {new_lang} is already current. No action needed.")
            return

        print(f"[LanguageController set_system_language] Updating Config and persisting new language: {new_lang}")
        Config.set_language(new_lang)

        print(f"[LanguageController set_system_language] Restarting subsystems (Clock, Date, Msg) for {new_lang}")
        self.clock_app.set_language(language = new_lang)
        self.date_app.set_language(language = new_lang)
        self.msg_app.set_language(language = new_lang)
        
        print(f"[LanguageController set_system_language] Language {new_lang.upper()} successfully applied across all systems")

    def handle_cycle_language(self):
        print("[LanguageController handle_cycle_language] Starting language switch cycle")
        
        try:
            current_index = Config.LANGUAGES.index(Config.LANGUAGE)
        except ValueError:
            print("[LanguageController handle_cycle_language] Error: Current language not found in list. Resetting to index 0")
            current_index = 0

        next_index = (current_index + 1) % len(Config.LANGUAGES)
        next_lang = Config.LANGUAGES[next_index]

        print(f"[LanguageController handle_cycle_language] Next language identified: {next_lang}")
        self.set_system_language(next_lang)
        self.audio_menu.play_language_changed()