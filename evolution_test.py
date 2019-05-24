from ai.population import Population
from core.constants import LEAGUE

def main():
    Population(visualize=False, size=24, selection_size=6, game_number=3, 
        league=LEAGUE.WOOD2, folder="WOOD2", showcase=True, idle_limit=50).start()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exit")