from core.player import Player
from core.constants import MAP_HEIGHT, MAP_WIDTH, VOID, NEUTRAL, UNIT_COST, UNIT_UPKEEP,\
    UP, LEFT, RIGHT, DOWN, CAPTURE_LEVEL, LEAGUE, DIRECTIONS, STAY, MAX_LEVEL, MAX_TURNS
from core.cell import Cell
from core.building import Building, BUILDING_TYPE
from core.unit import Unit

from ai.nn.training_nn import TrainingAgent
from ai.nn.moving_nn import MovingAgent

import math, tensorflow as tf
tf.logging.set_verbosity(tf.logging.ERROR)

CELL_ENCODE = {
    "x": -0.05,
    "o": 0.05,
    "X": -0.1,
    "O": 0.1,
    "#": -1,
    ".": 0
}

ME = 0
ENEMY = 1

class Data:
    def __init__(self, bot = None):
        if bot:
            self.uid = str(bot.uid)
            self.training_weights = bot.training_agent.get_weights().tolist()
            self.moving_weights = bot.moving_agent.get_weights().tolist()
            self.wins = bot.win_num
            self.lost = bot.lost_num
            self.scores = bot.scores.copy()
            self.best = max(max(self.scores), 1) if len(self.scores) else 1
            self.average_score = max([sum(self.scores) / len(self.scores) if len(self.scores) else 0, 1])
        else:
            self.average_score = 1
            self.best = 1
        self.should_randomize = False

    def get_score(self):
        if self.best < 0 or self.average_score < 0:
            return 0
        return self.average_score + self.best ** 2

    def __repr__(self):
        return f'Data#{self.uid}[best:{round(self.best)}, average:{round(self.average_score)}]'

    def __str__(self):
        return repr(self)

def update_cell(cell: Cell, char: str):
    if char == "X":
        cell.set_active()
        cell.set_owner(ENEMY)
    elif char == "x":
        cell.set_inactive()
        cell.set_owner(ENEMY)
    elif char == "O":
        cell.set_active()
        cell.set_owner(ME)
    elif char == "o":
        cell.set_inactive()
        cell.set_owner(ME)
    elif char == "#":
        cell.set_owner(VOID)
    elif char == ".":
        cell.set_owner(NEUTRAL)
    else:
        raise KeyError()

CELL_DECODE = {value: key for key, value in CELL_ENCODE.items()}

def decode(cell: Cell):
    if not cell:
        return "#"
    if cell.get_owner() == ME:
        return "O" if cell.is_active() else "o"
    elif cell.get_owner() == ENEMY:
        return "X" if cell.is_active() else "x"
    elif cell.get_owner() == VOID:
        return "#"
    elif cell.get_owner() == NEUTRAL:
        return "."
    else:
        raise KeyError()

DIRECTION_ENCODE = [1, -0.5, -1, 0.5, 0]
MAP_SIZE = MAP_HEIGHT * MAP_WIDTH

from math import tanh

class AIBot(Player):

    ID = 0

    def __init__(self, index: int, randomize=False):
        super().__init__(index, print_turn=False)
        self.training_agent: TrainingAgent = None
        self.moving_agent: MovingAgent = None
        self.map = [[Cell(x, y) for y in range(MAP_HEIGHT)] for x in range(MAP_WIDTH)]
        self.my_units = {}
        self.enemy_unit_num = 0
        self.actions = []
        self.population = None
        self.id = AIBot.ID
        self.uid = ""
        self.randomize_onplay = randomize
        self.sess = None
        AIBot.ID += 1
        # print(f'AIBot#{self.id} constructor called')

        # Connect the nodes
        for x in range(MAP_WIDTH):
            for y in range(MAP_HEIGHT):
                self.in_bound(x, y - 1) and self.map[x][y].set_neighbor(UP, self.map[x][y - 1])
                self.in_bound(x, y + 1) and self.map[x][y].set_neighbor(DOWN, self.map[x][y + 1])
                self.in_bound(x + 1, y) and self.map[x][y].set_neighbor(RIGHT, self.map[x + 1][y])
                self.in_bound(x - 1, y) and self.map[x][y].set_neighbor(LEFT, self.map[x - 1][y])

    def activate(self):
        self.sess = tf.Session()
        if self.randomize_onplay:
            self.randomize()
            self.randomize_onplay = False

    def deactivate(self):
        self.sess.close()
        self.sess = None
        self.training_agent = None
        self.moving_agent = None

    def get_message(self):
        if len(self.actions):
            string = ";".join(self.actions)
            # print(f'{self} returning commands {string}')
            return string
        return "WAIT"
    
    def update(self):
        """self.transpose always make sure (0, 0) is the player's HQ
        and (11, 11) is the enemy HQ"""

        self.turns += 1
        if self.print_turn:
            print(f'\n\nTurn {self.turns}')

        # Clear old data
        self.actions.clear()
        self.my_units.clear()
        self.clear_units_and_buildings()
        self.enemy_unit_num = 0

        # Update both sides' income and gold
        self.gold = int(self.read_input())
        self.income = int(self.read_input())
        self.opponent_gold = int(self.read_input())
        self.opponent_income = int(self.read_input())

        # print(f'My Gold: {self.gold}, My Income: {self.income}\n' + 
        #       f'Enemy Gold: {self.opponent_gold}, Enemy Income: {self.opponent_income}')

        # Encoding and storing map
        for i in range(MAP_WIDTH):
            map_line = self.read_input()
            if not i and map_line[0] == "X":
                self.transpose = True
            for j in range(MAP_HEIGHT):
                x, y = i, j
                if self.transpose:
                    x, y = self.trs(i, j)

                # print(f'[{x}, {y}, {map_line[j]}]', end=" ")
                update_cell(self.map[x][y], map_line[j])

        # Update builings
        building_count = int(self.read_input())
        for _ in range(building_count):
            owner, building_type, x, y = [int(j) for j in self.read_input().split()]
            if self.transpose:
                x, y = self.trs(x, y)
            building = Building(self.map[x][y], owner, building_type)
            self.map[x][y].set_building(building)

        # Update units
        unit_count = int(self.read_input())
        for _ in range(unit_count):
            owner, unit_id, level, x, y = [int(j) for j in self.read_input().split()]
            if self.transpose:
                x, y = self.trs(x, y)
            unit = Unit(self.map[x][y], owner, level)
            if owner == ME:
                self.my_units[unit_id] = unit
            else:
                self.enemy_unit_num += 1
            self.map[x][y].set_unit(unit)

        self.train()
        self.move()
        # self.print_map()
            
    def trs(self, x: int, y: int):
        return MAP_WIDTH - x - 1, MAP_HEIGHT - y - 1

    def send_input_line(self, line):
        super().send_input_line(line)
        # print("Input Received: " + str(line))

    def set_population(self, population):
        self.population = population

    def init(self):
        mines = int(self.read_init_input())
        for _ in range(mines):
            x, y = [int(i) for i in self.read_init_input().split()]
            self.map[x][y].set_mine()
            # print(f'Mine[{x}, {y}]')

    def print_map(self):
        # Debug
        for row in self.map:
            print("".join([decode(cell) for cell in row]))

    def clear_units_and_buildings(self):
        # Make sure every update the map is rid of old units and building data
        for row in self.map:
            for cell in row:
                cell.set_unit(None)
                cell.set_building(None)

    def get_neighbor_encoding(self, cell: Cell):
        arr = []
        x, y = cell.get_x(), cell.get_y()
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if not dx and not dy:
                    continue
                if self.in_bound(x + dx, y + dy):
                    arr.append(self.map[x + dx][y + dy])
                else:
                    arr.append(None)
        return [CELL_ENCODE[decode(c)] for c in arr]

    def get_neighbor_move_encoding(self, unit:Unit, cell: Cell):
        arr = []
        x, y = cell.get_x(), cell.get_y()
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if not dx and not dy:
                    continue
                if self.in_bound(x + dx, y + dy):
                    # Might need to remove this
                    if not self.map[x + dx][y + dy].is_capturable(ME, unit.get_level()):
                        arr.append(None)
                    else:
                        arr.append(self.map[x + dx][y + dy])
                else:
                    arr.append(None)
        return [CELL_ENCODE[decode(c)] for c in arr]

    def get_trainable_cells(self):
        arr = []
        for row in self.map:
            for cell in row:
                if cell.is_playable(ME) and cell.is_capturable(ME, CAPTURE_LEVEL):
                    arr.append(cell)
        return arr

    def in_bound(self, x, y):
        return x >= 0 and x < MAP_WIDTH and y >= 0 and y < MAP_HEIGHT

    def train(self):
        assert self.training_agent != None
        # Make TRAIN actions
        my_unit, enemy_unit = len(self.my_units) / MAP_SIZE, self.enemy_unit_num / MAP_SIZE

        my_income, enemy_income = tanh(self.income / 5), tanh(self.opponent_income / 5)

        my_gold, enemy_gold = tanh(self.gold / 50), tanh(self.opponent_gold / 50)

        turn = self.turns / MAX_TURNS

        for cell in self.get_trainable_cells():
            # print(f'Trainable {cell}')
            encoded = self.get_neighbor_encoding(cell)
            # print(f'Encoded: {encoded}')
            x, y = cell.get_x() / 11, cell.get_y() / 11

            inputs = encoded + [x, y, my_unit, enemy_unit, my_income, enemy_income, \
                my_gold, enemy_gold, turn]
            # print(f'Inputs: {inputs}')
            result = self.training_agent.predict(inputs)[0].tolist()
            # print(f'Output: {result}')
            level = result.index(max(result))
            if not level:
                continue

            # For next prediction
            self.gold -= UNIT_COST[level]
            self.income -= UNIT_UPKEEP[level]
        
            self.make_train_action(cell.get_x(), cell.get_y(), level)

    def make_train_action(self, x, y, level):
        if self.transpose:
            x, y = self.trs(x, y)
        self.actions.append(f'TRAIN {level} {x} {y}')

    def move(self):
        assert self.moving_agent != None
        # Make MOVE actions

        turn = self.turns / MAX_TURNS
        
        for unit_id in self.my_units:
            unit = self.my_units[unit_id]
            level = unit.get_level() / MAX_LEVEL
            cell: Cell = unit.get_cell()
            x, y = cell.get_x(), cell.get_y()

            neighbors = self.get_neighbor_move_encoding(unit, cell)

            result = self.moving_agent.predict(neighbors + [level, x, y, turn])[0].tolist()

            prediction = DIRECTIONS[result.index(max(result))]

            # print(f'Predictions for {unit}: {prediction}')
            self.make_move_action(x, y, unit_id, prediction)

    def make_move_action(self, x, y, unit_id, direction):
        if direction == STAY:
            return
        if self.transpose:
            x, y = self.trs(x, y)
            if direction == LEFT:
                direction = RIGHT
            elif direction == UP:
                direction = DOWN
            elif direction == RIGHT:
                direction = LEFT
            elif direction == DOWN:
                direction = UP
        if direction == UP:
            y -= 1
        elif direction == DOWN:
            y += 1
        elif direction == RIGHT:
            x += 1
        elif direction == LEFT:
            x -= 1
        if self.in_bound(x, y):
            self.actions.append(f'MOVE {unit_id} {x} {y}')

    def on_gameover(self):
        self.clear_map()

    def get_data(self):
        return Data(bot=self)

    def from_data(self, data: Data):
        self.uid = str(data.uid)
        self.reset()
        self.reset_stats()
        if data.should_randomize:
            self.randomize()
        else:
            self.training_agent = TrainingAgent(self.sess)
            self.moving_agent = MovingAgent(self.sess)
            self.training_agent.set_weights(data.training_weights)
            self.moving_agent.set_weights(data.moving_weights)

    def randomize(self):
        import random
        self.uid = "".join([str(i) for i in random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=4)])
        self.training_agent = TrainingAgent(self.sess)
        self.moving_agent = MovingAgent(self.sess)
        self.training_agent.randomize()
        self.moving_agent.randomize()

    def clear_map(self):
        for row in self.map:
            for cell in row:
                cell.clear()

    def __str__(self):
        return f'Bot{self.uid}'

    def __repr__(self):
        return str(self)
