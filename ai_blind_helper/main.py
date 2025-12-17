import argparse
import sys
from controller import MainController 

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="camera",
                        choices=["camera", "screen", "none"])
    args = parser.parse_args()

    # Toda a complexidade foi movida para dentro do controller
    controller = MainController(video_mode=args.mode)
    
    try:
        controller.run()
    except KeyboardInterrupt:
        print("\nInterrupção forçada via Terminal.")
        sys.exit(0)

if __name__ == "__main__":
    main()