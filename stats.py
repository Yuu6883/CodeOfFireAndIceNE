from ai.graph import plot_ai

def main():
    plot_ai("WOOD2")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exit")