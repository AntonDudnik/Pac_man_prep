import sys
from pacman.config import load_config
from pacman.engine import GameEngine


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 pac-man.py <config.json>", file=sys.stderr)
        sys.exit(1)

    config = load_config(sys.argv[1])
    engine = GameEngine(config)
    engine.run()

    '''
    try:
        config = load_config(sys.argv[1])
        engine = GameEngine(config)
        engine.run()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    '''


if __name__ == "__main__":
    main()
