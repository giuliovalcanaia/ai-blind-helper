class KeyboardController:
    def __init__(self, keyboard_application):
        self.keyboard_application = keyboard_application
        
    def start(self):
        self.keyboard_application.start()
        
    def stop(self):
        self.keyboard_application.stop()

    def register_key(self, key_code, callback):
        self.keyboard_application.register_key(key_code, callback)