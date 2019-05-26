import pickle 
import matplotlib.pyplot as plt
import os
import pandas as pd

def plot_ai(folder):
    if not os.path.exists(f'./ai/{folder}'):
        print("Can't find folder at " + f'./ai/{folder}')
    else:
        folders = os.listdir(f'./ai/{folder}/')
        if not len(folder):
            print("No gen folder found at " + f'./ai/{folder}/')
        else:
            sorted_folders = sorted(folders, key=lambda name:int(name[3:]))
            best_scores = []
            average_scores = []
            for gen_folder in sorted_folders:
                for nnet in os.listdir(f'./ai/{folder}/{gen_folder}/'):
                    gen_best_scores = []
                    gen_average_scores = []
                    with open(f'./ai/{folder}/{gen_folder}/{nnet}', "rb") as f:
                        data_obj = pickle.load(f)
                        gen_best_scores.append(max(data_obj.scores))
                        gen_average_scores.append(data_obj.average_score)
                best_scores.append(max(gen_best_scores))
                average_scores.append(sum(gen_average_scores) / len(gen_average_scores))
            df = pd.DataFrame({"x": list(range(len(best_scores))), "best": best_scores, "average": average_scores})
            plt.title(f'Learning Graph for {folder}')
            plt.xlabel("Generation")
            plt.ylabel("Score")
            plt.ylim((0, max(best_scores) * 1.1))
            plt.plot("x", "best", data=df)
            plt.plot("x", "average", data=df)
            plt.show()

