import argparse
import asyncio
from application import Application

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        type=str,
        default="camera",
        help="Fonte de vídeo",
        choices=["camera", "screen", "none"],
    )
    args = parser.parse_args()

    app = Application(video_mode=args.mode)
    try:
        asyncio.run(app.start())
    except KeyboardInterrupt:
        pass
