from core.engine import Engine
from bot import Bot

def main():
    engine = Engine(strict=True, debug=True, sleep=0.1)
    engine.add_player(Bot(0))
    engine.add_player(Bot(1))
    engine.start()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exit")