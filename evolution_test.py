from ai.population import Population

def main():
    Population(visualize=False, size=24, selection_size=6, game_number=5, folder="WOOD3_Improved").start()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exit")