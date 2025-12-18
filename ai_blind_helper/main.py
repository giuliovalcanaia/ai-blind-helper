import argparse
import sys
from provider import ApplicationProvider, ControllerProvider, ManagerProvider, ReaderProvider

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="camera",
                        choices=["camera", "screen", "none"])
    args = parser.parse_args()

    manager_provider = ManagerProvider()
    reader_provider = ReaderProvider()
    application_provider = ApplicationProvider(manager_provider=manager_provider, reader_provider=reader_provider)
    controller_provider = ControllerProvider(video_mode=args.mode, application_provider=application_provider)
    application_provider.keyboard.set_controller(controller_provider.main_controller)

    main_controller = controller_provider.main_controller
    
    try:
        main_controller.run()
    except KeyboardInterrupt:
        print("\nInterrupção forçada via Terminal.")
        sys.exit(0)

if __name__ == "__main__":
    main()