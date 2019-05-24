from core.player import Player
from core.constants import MAP_HEIGHT, MAP_WIDTH, VOID, NEUTRAL,\
    UP, LEFT, RIGHT, DOWN, CAPTURE_LEVEL, LEAGUE, DIRECTIONS, STAY
from core.cell import Cell
from core.building import Building, BUILDING_TYPE
from core.unit import Unit

from ai.nn.training_nn import TrainingAgent
from ai.nn.moving_nn import MovingAgent

import math

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
            self.training_weights = bot.training_agent.get_weights().tolist()
            self.moving_weights = bot.moving_agent.get_weights().tolist()
            self.wins = bot.win_num
            self.lost = bot.lost_num
            self.scores = bot.scores.copy()
            self.average_score = sum(self.scores) / len(self.scores) if len(self.scores) else 0

    def get_score(self):
        return self.average_score

    def __repr__(self):
        return f'Data[win:{self.wins}, lose:{self.lost}]'

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

def normalize(a: int, b: int):
    l = math.sqrt(a ** 2 + b ** 2)
    if not l:
        return 1, 1
    return a / l, b / l

class AIBot(Player):

    ID = 0

    def __init__(self, index: int, sess, randomize=False):
        super().__init__(index, print_turn=False)
        self.training_agent = TrainingAgent(sess)
        self.moving_agent = MovingAgent(sess)
        self.map = [[Cell(x, y) for y in range(MAP_HEIGHT)] for x in range(MAP_WIDTH)]
        self.my_units = {}
        self.enemy_unit_num = 0
        self.actions = []
        self.population = None
        self.id = AIBot.ID
        AIBot.ID += 1
        # print(f'AIBot#{self.id} constructor called')

        # Connect the nodes
        for x in range(MAP_WIDTH):
            for y in range(MAP_HEIGHT):
                self.in_bound(x, y - 1) and self.map[x][y].set_neighbor(UP, self.map[x][y - 1])
                self.in_bound(x, y + 1) and self.map[x][y].set_neighbor(DOWN, self.map[x][y + 1])
                self.in_bound(x + 1, y) and self.map[x][y].set_neighbor(RIGHT, self.map[x + 1][y])
                self.in_bound(x - 1, y) and self.map[x][y].set_neighbor(LEFT, self.map[x - 1][y])
        
        if randomize:
            self.training_agent.randomize()
            self.moving_agent.randomize()

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
        # Make TRAIN actions
        my_unit, enemy_unit = normalize(len(self.my_units), self.enemy_unit_num)

        my_income, enemy_income = normalize(self.income, self.opponent_income)

        my_gold, enemy_gold = normalize(self.gold, self.opponent_gold)

        results = []
        for cell in self.get_trainable_cells():
            # print(f'Trainable {cell}')
            encoded = self.get_neighbor_encoding(cell)
            # print(f'Encoded: {encoded}')
            x, y = cell.get_x() / 11, cell.get_y() / 11

            inputs = encoded + [x, y, my_unit, enemy_unit, my_income, enemy_income, \
                my_gold, enemy_gold]
            # print(f'Inputs: {inputs}')
            output = self.training_agent.predict(inputs)[0][0]
            # print(f'Output: {output}\n')
            results.append({"cell": cell, "output": output})

        results = sorted(results, key=lambda key: key["output"], reverse=True)
        # print(f'Results: {results}')
        for result in results:
            if result["output"] < 0.5:
                break
            if self.get_league() == LEAGUE.WOOD3:
                self.make_train_action(result["cell"].get_x(), result["cell"].get_y(), 1)
            else:
                if result["output"] < 0.7:
                    self.make_train_action(result["cell"].get_x(), result["cell"].get_y(), 1)
                elif result["output"] < 0.9:
                    self.make_train_action(result["cell"].get_x(), result["cell"].get_y(), 2)
                else:
                    self.make_train_action(result["cell"].get_x(), result["cell"].get_y(), 3)

    def make_train_action(self, x, y, level):
        if self.transpose:
            x, y = self.trs(x, y)
        self.actions.append(f'TRAIN {level} {x} {y}')

    def move(self):
        # Make MOVE actions
        
        for unit_id in self.my_units:
            unit = self.my_units[unit_id]
            cell: Cell = unit.get_cell()
            x, y = cell.get_x(), cell.get_y()

            neighbors = self.get_neighbor_move_encoding(unit, cell)

            result = [self.moving_agent.predict(neighbors + [x, y, DIRECTION_ENCODE[direction]]) \
                for direction in DIRECTIONS]

            result = [i[0][0] for i in result]

            prediction = DIRECTIONS[result.index(max(result))]

            # print(f'Predictions for {unit}: {prediction}')
            self.make_move_action(x, y, unit_id, prediction)

    def make_move_action(self, x, y, unit_id, direction):
        if direction == STAY:
            return
        if self.transpose:
            x, y = self.trs(x, y)
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
    
    def __repr__(self):
        return f'AIBot#{self.id} [Wins: {self.win_num}, Loses: {self.lost_num}]'

    def __str__(self):
        return repr(self)

    def get_data(self):
        return Data(bot=self)

    def from_data(self, data: Data):
        self.reset()
        self.reset_stats()
        self.training_agent.set_weights(data.training_weights)
        self.moving_agent.set_weights(data.moving_weights)

    def randomize(self):
        self.training_agent.randomize()
        self.moving_agent.randomize()

    def clear_map(self):
        for row in self.map:
            for cell in row:
                cell.clear()
