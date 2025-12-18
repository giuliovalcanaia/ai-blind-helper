import argparse
import sys
from provider import *

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="camera",
                        choices=["camera", "screen", "none"])
    args = parser.parse_args()

    state_provider = StateProvider()
    manager_provider = ManagerProvider()
    reader_provider = ReaderProvider()
    application_provider = ApplicationProvider(manager_provider=manager_provider, reader_provider=reader_provider)
    controller_provider = ControllerProvider(video_mode=args.mode, application_provider=application_provider, state_provider=state_provider)
    interface_provider = InterfaceProvider(controller_provider)
    
    try:
        interface_provider.keyboard_interface.run()
    except KeyboardInterrupt:
        print("\nInterrupção forçada via Terminal.")
        sys.exit(0)

if __name__ == "__main__":
    main()