import argparse
import sys
from provider import *

def main():
    state_provider = StateProvider()
    manager_provider = ManagerProvider()
    reader_provider = ReaderProvider()
    
    application_provider = ApplicationProvider(
        manager_provider=manager_provider, 
        reader_provider=reader_provider
    )
    
    controller_provider = ControllerProvider(
        application_provider=application_provider, 
        state_provider=state_provider
    )
    
    interface_provider = InterfaceProvider(controller_provider)
    
    try:
        print("[Main main] Chamando interface_provider.keyboard_interface.run()")
        interface_provider.keyboard_interface.run()
    except KeyboardInterrupt:
        print("\n[Main main] Interrupção forçada via Terminal (SIGINT).")
        sys.exit(0)

if __name__ == "__main__":
    main()