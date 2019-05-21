from core.engine import Engine
from starter.starter import StarterBot
from boss.boss1 import Boss1

def main():
    """Boss1 VS Starter"""
    engine = Engine(strict=False, debug=False, sleep=0.1)
    engine.add_player(StarterBot(0))
    engine.add_player(Boss1(1))
    engine.start()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exit")