import sys
import math
from core.player import Player

# MAP SIZE
WIDTH = 12
HEIGHT = 12

# OWNER
ME = 0
OPPONENT = 1

# BUILDING TYPE
HQ = 0


class Position:

    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def __repr__(self):
        return f'Position[{self.x}, {self.y}]'
    
    def __str__(self):
        return repr(self)


class MyUnit:

    def __init__(self, owner, id, level, x, y):
        self.owner = owner
        self.id = id
        self.level = level
        self.pos = Position(x, y)

    def __repr__(self):
        return f'Unit[Owner:{self.owner}, ID:{self.id}, Level:{self.level}, Pos:{self.pos}]'
    
    def __str__(self):
        return repr(self)

class MyBuilding:

    def __init__(self, owner, b_type, x, y):
        self.owner = owner
        self.type = b_type
        self.pos = Position(x, y)

    def __repr__(self):
        return f'Building[Type:{self.type}, Owner:{self.owner}, Pos: {self.pos}]'

    def __str__(self):
        return repr(self)


class StarterBot(Player):

    def __init__(self, index: int):
        super().__init__(index, print_turn=False)
        self.buildings = []
        self.units = []
        self.actions = []
        self.gold = 0
        self.income = 0
        self.opponent_gold = 0
        self.opponent_income = 0


    def get_my_HQ(self):
        for b in self.buildings:
            if b.type == HQ and b.owner == ME:
                return b


    def get_opponent_HQ(self):
        for b in self.buildings:
            if b.type == HQ and b.owner == OPPONENT:
                return b


    def move_units(self):
        center = Position(5, 5)

        for unit in self.units:
            if unit.owner == ME:
                self.actions.append(f'MOVE {unit.id} {center.x} {center.y}')


    def get_train_position(self):
        hq = self.get_my_HQ()

        if hq.pos.x == 0:
            return Position(0, 1)
        return Position(11, 10)


    def train_units(self):
        train_pos = self.get_train_position()

        if self.gold > 30:
            self.actions.append(f'TRAIN 1 {train_pos.x} {train_pos.y}')


    def init(self):
        # Unused in Wood 3
        # number_mine_spots = int(self.read_input())
        # for i in range(number_mine_spots):
        #     x, y = [int(j) for j in self.read_input().split()]
        pass

    def update(self):
        # print(self.message_queue)
        self.turns += 1
        if self.print_turn:
            print(f'\n\nTurn {self.turns}')
        self.units.clear()
        self.buildings.clear()
        self.actions.clear()

        self.gold = int(self.read_input())
        self.income = int(self.read_input())
        self.opponent_gold = int(self.read_input())
        self.opponent_income = int(self.read_input())

        for _ in range(12):
            line = self.read_input()

        building_count = int(self.read_input())
        for _ in range(building_count):
            owner, building_type, x, y = [int(j) for j in self.read_input().split()]
            self.buildings.append(MyBuilding(owner, building_type, x, y))

        unit_count = int(self.read_input())
        for _ in range(unit_count):
            owner, unit_id, level, x, y = [int(j) for j in self.read_input().split()]
            self.units.append(MyUnit(owner, unit_id, level, x, y))

    def build_output(self):
        # TODO "core" of the AI
        self.train_units()
        self.move_units()

    def output(self):
        if self.actions:
            return (';'.join(self.actions))
        else:
            return 'WAIT'

    def get_message(self):
        self.build_output()
        return self.output()