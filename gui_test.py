from core.gui import GUIEngine
from starter.starter import StarterBot
from core.constants import LEAGUE
from boss.boss1 import Boss1

def main():
    """Boss1 VS Starter"""
    engine = GUIEngine(league=LEAGUE.BRONZE, strict=False, debug=False, sleep=0.1)
    engine.add_player(Boss1)
    engine.add_player(StarterBot)
    engine.start()

if __name__ == "__main__":
    try:
        while True:
            main()
    except KeyboardInterrupt:
        print("Exit")