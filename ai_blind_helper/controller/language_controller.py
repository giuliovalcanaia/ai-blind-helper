from config import Config

class LanguageController:
    def __init__(self, clock_app, date_app, msg_app):
        self.clock_app = clock_app
        self.date_app = date_app
        self.msg_app = msg_app
    
    def set_system_language(self, new_lang: str):
        """
        Altera o idioma global, persiste a escolha e reinicializa os subsistemas.
        """
        if new_lang == Config.LANGUAGE:
            return

        print(f">>> [Sistema] A alterar idioma para: {new_lang.upper()} e a guardar...")
        
        # 1. Atualiza e Persiste (Guarda no JSON)
        Config.set_language(new_lang)

        # 2. Recria as instâncias que dependem do idioma (Hot-Swap)
        self.clock_app.set_language(language = new_lang)
        self.date_app.set_language(language = new_lang)
        self.msg_app.set_language(language = new_lang)
        
        # Se estas apps também tiverem suporte a multi-idioma, recrie-as também:
        # self.description_app = DescriptionApplication(language=new_lang)
        
        print(f">>> [Sistema] Idioma {new_lang.upper()} aplicado e persistido.")
        

    def handle_cycle_language(self):
        """
        Cicla entre os idiomas disponíveis (PT -> EN -> ES -> ...)
        """
        
        try:
            current_index = Config.LANGUAGES.index(Config.LANGUAGE)
        except ValueError:
            current_index = 0

        # Calcula o próximo índice
        next_index = (current_index + 1) % len(Config.LANGUAGES)
        next_lang = Config.LANGUAGES[next_index]

        # Aplica a mudança
        self.set_system_language(next_lang)