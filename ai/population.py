from core.constants import LEAGUE, PLAYER_COUNT
from ai.bot import AIBot, Data
from ai.nn.util import mutate, crossover
import numpy as np
import random
import json
import tensorflow as tf
import pickle
import os
import shutil

class Population:

    def __init__(self, size=128, selection_size=16, visualize=False, game_number=5, folder="generations", ideal_generation=1000, idle_limit=10):
        
        assert size > selection_size
        
        sess = tf.InteractiveSession()
        self.generation = 0
        self.size = size
        self.selection_size = selection_size
        self.folder = folder
        self.ideal_generation = ideal_generation

        if not os.path.exists(f'./ai/{folder}'):
            os.mkdir(f'./ai/{folder}')

        if visualize:
            from core.gui import GUIEngine
            self.engine = GUIEngine(league=LEAGUE.WOOD3, silence=True, idle_limit=idle_limit)
        else:
            from core.engine import Engine
            self.engine = Engine(league=LEAGUE.WOOD3, silence=True, idle_limit=idle_limit)
            
        self.bots = [self.engine.add_player(AIBot, sess, randomize=True),\
            self.engine.add_player(AIBot, sess, randomize=True)]
        self.sess = sess
        self.num_game = game_number
        self.generation_data = []
        self.results = []
        self.current_index = 0

    def start(self, continue_simulation=True):
        gen_folders = os.listdir(f'./ai/{self.folder}')
        new_pop = False
        if len(gen_folders):
            print("Found existing generations in " + f'./ai/{self.folder}')
            latest_gen = sorted([int(s[3:]) for s in gen_folders])[-1]
            print("Latest generation: " + str(latest_gen))

            if not continue_simulation:
                user_input = input("Do you want to overwrite existing generation and train from gen1?")
                if user_input.lower() == "y" or user_input.lower() == "yes":
                    shutil.rmtree(f'./ai/{self.folder}')
                    new_pop = True
            else:
                self.load_gen(latest_gen)
        else:
            new_pop = True

        if new_pop:
            self.simulate(randomize=True)
            self.natural_selection()
    
        while self.generation < self.ideal_generation:
            self.simulate()
            self.natural_selection()
        
    def simulate(self, randomize=False):
        
        self.current_index = 0
        self.generation += 1

        # print(f'Simulating Generation {self.generation} ', end="")
        while len(self.results) < self.size:
            if not randomize:
                data1, data2 = self.generation_data[self.current_index:self.current_index+PLAYER_COUNT]
                p1, p2 = self.engine.get_players()
                p1.from_data(data1)
                p2.from_data(data2)

            for i in range(self.num_game):
                if not i:
                    self.engine.start()
                else:
                    self.engine.restart()
                print(f'Generation {self.generation} Progress {len(self.results)} / {self.size} Game {i + 1}')
            
            for p in self.engine.get_players():
                self.results.append(p.get_data())
                p.reset_stats()
                if randomize:
                    p.randomize()

        print("Generation Stats:")
        scores = [i.average_score for i in self.results]
        average = sum(scores) / len(scores)
        max_score = max(scores)
        print(f'Best: {max_score}, Average: {average}')

    def natural_selection(self, write=True):

        self.generation_data.clear()

        temp = sorted(self.results, key=lambda k: k.get_score(), reverse=True)

        best = temp[:self.selection_size]

        if write:
            for index in range(len(best)):
                obj = best[index]
                if not os.path.exists(f'./ai/{self.folder}/gen{self.generation}'):
                    os.mkdir(f'./ai/{self.folder}/gen{self.generation}')
                with open(f'./ai/{self.folder}/gen{self.generation}/parent{index+1}.nnet', "wb") as f:
                    pickle.dump(obj, f)

        for nn in best:
            self.generation_data.append(nn)

        while len(self.generation_data) < self.size:
            parent1, parent2 = np.random.choice(best, 2, False)
            data = Data()
            data.training_weights = mutate(crossover(parent1.training_weights, parent2.training_weights))
            data.moving_weights = mutate(crossover(parent1.moving_weights, parent2.moving_weights))
            # print("Offspring:", len(data.training_weights), len(data.moving_weights))
            self.generation_data.append(data)

        np.random.shuffle(self.generation_data)
        self.results.clear()
            
    def load_gen(self, gen):
        assert type(gen) is int and gen > 0
        if not os.path.exists(f'./ai/{self.folder}/gen{gen}'):
            print("Can't find path: " + f'./ai/{self.folder}/gen{gen}')
            exit(1)
        files = os.listdir(f'./ai/{self.folder}/gen{gen}')

        self.generation = gen
        self.generation_data.clear()
        self.results.clear()
        
        if len(files) != self.selection_size:
            print(f'WARNING: Found {len(files)} .nnet in target folder while the population requires {self.selection_size} .nnet to start simulation')
            user_input = input("Do you want to merge .nnet files into the population? Enter Y/N")
            if user_input.lower() == "y" or user_input.lower() == "yes":
                files = files[:self.selection_size]
            else:
                print("Exiting")
                exit(0)

        for file in files:
            with open(f'./ai/{self.folder}/gen{gen}/{file}', "rb") as f:
                self.results.append(pickle.load(f))
                print(f'{file} loaded')

        self.natural_selection(write=False)
        return self

