from core.constants import LEAGUE, PLAYER_COUNT
from ai.bot import AIBot, Data
from ai.nn.util import mutate, crossover, SWAP_RATE, REGEN_RATE
from core.engine import Engine
from multiprocessing.pool import Pool
from multiprocessing.sharedctypes import Value
from termcolor import colored
import multiprocessing as mp
import numpy as np
import random
import json
import tensorflow as tf
import pickle
import os
import shutil
import time

calc = lambda x: (round(sum([d.best for d in x]) / len(x)), round(sum([d.average_score for d in x]) / len(x)))
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

class Population:

    progress = 0

    def __init__(self, size=24, selection_size=6, game_number=5, folder="generations", \
        ideal_generation=1000, idle_limit=100, league:LEAGUE=LEAGUE.WOOD3, restart_generation=20, 
        visualize=False, batch_size=os.cpu_count(), save_every=10, print_game = False):
        
        assert size > selection_size
        assert not (size % batch_size), f'Population Size ({size}) must be divisible by Batch Size ({batch_size})'
        assert not ((size // batch_size) % 2), f'Batch Data must be an even number ({(size // batch_size)})'
        
        self.batch_size = batch_size
        self.generation = 0
        self.simulated = 0
        self.restart_limit = restart_generation
        self.size = size
        self.selection_size = selection_size
        self.folder = folder
        self.ideal_generation = ideal_generation
        self.visualize = visualize
        self.save_every = save_every
        self.print_game = print_game

        if not os.path.exists(f'./ai/{folder}'):
            os.mkdir(f'./ai/{folder}')

        if visualize:
            from core.gui import GUIEngine
            self.batch_size = 1
            self.num_game = 1
            self.engines = [GUIEngine(league=league, silence=False, idle_limit=idle_limit, sleep=0.1)]

        else:
            print(f'Initializing Population with size({size}) selection({selection_size}) batch({batch_size}) league({league.name})')
            self.engines = [Engine(league=league, silence=True, idle_limit=idle_limit) for _ in range(batch_size)]
            
        [(engine.add_player(AIBot, randomize=True),\
            engine.add_player(AIBot, randomize=True)) for engine in self.engines]
        self.num_game = game_number
        self.generation_data = [None] * self.size
        self.results = [None] * self.size
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
                    print("Exit")
                    exit(0)
            else:
                self.load_gen(latest_gen)
        else:
            new_pop = True

        if self.visualize:
            self.batch_size = self.size
            while True:
                self.simulate()

        if new_pop:
            self.generation += 1
            self.simulate(True)
            self.simulated += 1
            self.natural_selection()
            
        while self.generation < (self.ideal_generation or 2**31):
            self.generation += 1
            self.simulate()            
            self.simulated += 1
            self.natural_selection()

    def simulate(self, randomize=False):
        if not self.visualize:
            if self.batch_size != 1:
                try:
                    with Pool(processes=self.batch_size) as p:
                        packets = [Packet(self.generation, self.num_game, self.size, self.selection_size,
                            self.engines[batch], batch, self.batch_size, self.generation_data[batch*(self.size // self.batch_size):\
                            (batch+1)*(self.size // self.batch_size)], print_game=self.print_game, randomize=randomize) for batch in range(self.batch_size)]

                        self.results = np.concatenate(p.map(simulate, packets)).tolist()
                    return
                except Exception as e:
                    raise e
        
        self.results = simulate(Packet(self.generation, self.num_game, self.size, self.selection_size,
                        self.engines[0], 0, 1, self.generation_data, print_game=True, randomize=randomize))

    def natural_selection(self, write=True):

        self.generation_data = [None] * self.size

        temp = sorted(self.results, key=lambda k: k.get_score() if k else 0, reverse=True)

        # print("Population Data:")
        # for index in range(len(temp)):
        #     if index == self.selection_size:
        #         print("------------------------------")
        #     print(temp[index])

        best = temp[:self.selection_size]
        
        if write and not self.generation % self.save_every:

            # print("Generation Stats:")
            # print(f'Best: {round(best[0].best)}, Average: {round(best[0].average_score)}')
            # top_best, top_average = calc(best)
            # print(f'Top{len(best)} Best-Average: {top_best}, Average: {top_average}')
            pop_best, pop_average = calc(temp)
            # print(f'Population({self.size}) Best-Average: {pop_best}, Average: {pop_average}')

            for index in range(len(best)):
                obj = best[index]
                if not os.path.exists(f'./ai/{self.folder}'):
                    os.mkdir(f'./ai/{self.folder}')
                if not os.path.exists(f'./ai/{self.folder}/gen{self.generation}'):
                    os.mkdir(f'./ai/{self.folder}/gen{self.generation}')
                with open(f'./ai/{self.folder}/gen{self.generation}/parent{index+1}.nnet', "wb") as f:
                    pickle.dump(obj, f)
                    
            print(f'[{pop_best}, {pop_average}] Done writing Gen({self.generation}) files')
            time.sleep(1)
        elif write:
            print(f'Gen {self.generation} Done')

        # Make sure the parent joins back
        for index in range(len(best)):
            self.generation_data[index] = best[index]
        
        # Make offsprings to fill the empty spots
        for index in range(len(best), self.size):
            parent1, parent2 = np.random.choice(best, 2, False)
            time.sleep(0.05)
            
            data = Data()
            data.uid = parent1.uid[:2] + parent2.uid[2:]
            # print(f'Generated new offspring {data.uid}')
            factor = sum([parent1.get_score() <= 150, parent2.get_score() <= 150]) * 0.4
            if random.random() < REGEN_RATE + factor:
                data.should_randomize = True
            else:
                if random.random() < SWAP_RATE:
                    time.sleep(0.1)
                    if random.random() > 0.5:
                        data.training_weights = parent1.training_weights.copy()
                        data.moving_weights = parent2.moving_weights.copy() 
                    else:
                        data.training_weights = parent2.training_weights.copy()
                        data.moving_weights = parent1.moving_weights.copy() 
                else:
                    data.training_weights = mutate(crossover(parent1.training_weights, parent2.training_weights))
                    data.moving_weights = mutate(crossover(parent1.moving_weights, parent2.moving_weights))
            # print("Offspring:", len(data.training_weights), len(data.moving_weights))
            self.generation_data[index] = data

        np.random.shuffle(self.generation_data)
        self.results = [None] * self.size
            
    def load_gen(self, gen):
        assert type(gen) is int and gen > 0
        if not os.path.exists(f'./ai/{self.folder}/gen{gen}'):
            print("Can't find path: " + f'./ai/{self.folder}/gen{gen}')
            exit(1)
        files = os.listdir(f'./ai/{self.folder}/gen{gen}')

        self.generation = gen

        self.generation_data = [None] * self.size
        self.results = [None] * self.size
        
        if len(files) != self.selection_size:
            print(f'WARNING: Found {len(files)} .nnet in target folder while the population requires {self.selection_size} .nnet to start simulation')
            user_input = input("Do you want to merge .nnet files into the population? Enter Y/N")
            if user_input.lower() == "y" or user_input.lower() == "yes":
                files = files[:self.selection_size]
            else:
                print("Exiting")
                exit(0)

        for index in range(len(files)):
            file = files[index]
            with open(f'./ai/{self.folder}/gen{gen}/{file}', "rb") as f:
                self.results[index] = pickle.load(f)
        print(f'Loaded {len(files)} .nnet files')

        self.natural_selection(write=False)
        return self

class Packet:
    def __init__(self, generation, num_game, size, selection_size, engine, 
        batch, batch_size, generation_data, progress=0, print_game = False, randomize=False):
        self.generation = generation
        self.num_game = num_game
        self.size = size
        self.selection_size = selection_size
        self.engine = engine
        self.batch = batch
        self.batch_size = batch_size
        self.generation_data = generation_data
        self.randomize = randomize
        self.progress = progress
        self.print_game = print_game

    def __repr__(self):
        # return f'Generation{self.generation} Games{self.num_game} Population{self.size} Selection Size{self.selection_size} ' +\
        #     f'Engine {type(self.engine).__name__} Batch{self.batch} Batch{self.batch_size} Generation Data {self.generation_data}'
        return f'Batch{self.batch} Data{self.generation_data}'

    def __str__(self):
        return repr(self)

def simulate(packet: Packet):

    current_index = 0
    
    # print(f'Simulating Generation {packet.generation} Data Length{len(packet.generation_data)}')
    engine: Engine = packet.engine
    engine.activate_players()
    results = []
    np.random.shuffle(packet.generation_data)
    while current_index < packet.size // packet.batch_size:

        if not packet.randomize:
            data1, data2 = packet.generation_data[current_index:current_index+PLAYER_COUNT]
            p1, p2 = engine.get_players()
            p1.from_data(data1)
            p2.from_data(data2)
        else:
            engine.get_players()[1].randomize()

        for i in range(packet.num_game):

            if not i:
                engine.start()
            else:
                engine.restart()
                
            if packet.print_game:
                print(f'Gen{packet.generation} Batch{packet.batch} Game{i + 1} Result-{engine.get_result()}')
            # packet.progress += 1
            # print(f'Progress: {packet.progress.value}/{packet.size * packet.num_game}')
        
        p = engine.get_players()[0]
        results.append(p.get_data())
        p.reset_stats()
        if packet.randomize:
            p.randomize()
        
        current_index += 2

    engine.deactivate_players()
    # print(f'Batch{packet.batch} Done!')
    return results

