from ai.population import Population
from core.constants import LEAGUE

def main():
    Population(league=LEAGUE.WOOD2, folder="WOOD2.2", idle_limit=50).start()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exit")
        exit(1)