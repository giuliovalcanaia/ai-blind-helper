class KeyboardController:
    def __init__(self, keyboard_application):
        print(f"[KeyboardController __init__] Inicializando controlador com keyboard_application: {keyboard_application}")
        self.keyboard_application = keyboard_application
        
    def start(self):
        print("[KeyboardController start] Iniciando o serviço de monitoramento do teclado")
        self.keyboard_application.start()
        print("[KeyboardController start] Serviço de teclado iniciado com sucesso")
        
    def stop(self):
        print("[KeyboardController stop] Solicitando parada do serviço de teclado")
        self.keyboard_application.stop()
        print("[KeyboardController stop] Serviço de teclado interrompido")

    def register_key(self, key_code, callback):
        print(f"[KeyboardController register_key] Registrando callback para a tecla: {key_code}")
        self.keyboard_application.register_key(key_code, callback)
        print(f"[KeyboardController register_key] Tecla {key_code} registrada com sucesso")