import argparse
import sys
from provider import *
from logger import *
from event import EventBus

def main():    
    # START LOGGING: This should be the first thing to run
    logger = TerminalLogger()
    logger.start()

    # Your original code starts here
    state_provider = StateProvider()
    manager_provider = ManagerProvider()
    reader_provider = ReaderProvider()
    
    event_bus = EventBus(state_provider=state_provider)
    
    application_provider = ApplicationProvider(
        manager_provider=manager_provider, 
        reader_provider=reader_provider,
        state_provider=state_provider
    )
    
    controller_provider = ControllerProvider(
        application_provider=application_provider, 
        state_provider=state_provider,
        event_bus=event_bus
    )
    
    interface_provider = InterfaceProvider(
        controller_provider=controller_provider, 
        event_bus=event_bus
    )
    
    try:
        print("[Main main] Calling interface_provider.keyboard_interface.run()")
        interface_provider.keyboard_interface.run()
    except KeyboardInterrupt:
        print("\n[Main main] Forced interruption via Terminal (SIGINT).")
        sys.exit(0)
    except Exception as e:
        # This extra block ensures unexpected errors also go to the log
        print(f"\n[Main main] Unhandled fatal error: {e}")
        raise # Re-raise the error so the full traceback appears in the log

if __name__ == "__main__":
    main()