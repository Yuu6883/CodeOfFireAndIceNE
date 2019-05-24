from ai.graph import plot_ai

def main():
    plot_ai("WOOD3_Improved")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exit")