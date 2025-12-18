class KeyboardApplication:
    def __init__(self, keyboard_manager):
        self.keyboard_manager = keyboard_manager
        
    def start(self):
        self.keyboard_manager.start()
        
    def stop(self):
        self.keyboard_manager.stop()
        
    def register_key(self, key_code, callback):
        self.keyboard_manager.register_key(key_code, callback)