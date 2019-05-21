from constants import LEAGUE, MAP_HEIGHT, MAP_WIDTH, UNIT_COST, BUILDING_TYPE, PLAYER_COUNT, \
    NUMBER_MINESPOTS_MAX, NUMBER_MINESPOTS_MIN, VOID, UP, RIGHT, LEFT, DOWN, \
    NEUTRAL, MAPGENERATOR_T, MAPGENERATOR_R, MAPGENERATOR_ITERATIONSAUTOMATA, \
    BUILD_COST, MINE_INREMENT, CELL_INCOME, MINE_INCOME, UNIT_UPKEEP
from cell import Cell
from building import Building
from unit import Unit
from path import Path
from typing import List
from vec2 import Vec2
from player import Player
import numpy as np
import random, math


class GameState:

    def __init__(self, seed: int, league: LEAGUE):

        self.__map = [[Cell(x, y) for y in range(MAP_HEIGHT)] for x in range(MAP_WIDTH)]
        
        self.__player_golds = [2 * UNIT_COST[1]] * PLAYER_COUNT
        self.__player_income = [1] * PLAYER_COUNT

        self.__seed = seed
        self.__path_find = Path()

        random.seed(seed)

        if league == LEAGUE.WOOD1 or league == LEAGUE.BRONZE:
            self.__mines = 2 * round((random.randint(0, NUMBER_MINESPOTS_MAX - NUMBER_MINESPOTS_MIN)\
                + NUMBER_MINESPOTS_MIN) / 2)
        else:
            self.__mines = 0

        self.__units = {}
        self.__buildings = []
        self.__HQs = []

    def get_cell(self, x: int, y: int) -> Cell:
        return self.__map[x][y]

    def get_unit(self, ID: int) -> Unit:
        return self.__units.get(ID)

    def get_income(self, index: int) -> int:
        return self.__player_income[index]

    def get_gold(self, index: int) -> int:
        return self.__player_golds[index]

    def get_sym_cell(self, x: int, y: int) -> Cell:
        return self.__map[MAP_WIDTH - x - 1][MAP_HEIGHT - y - 1]

    def in_bound(self, x: int, y: int) -> bool:
        return x >= 0 and x < MAP_WIDTH and y >= 0 and y < MAP_HEIGHT

    def is_inside(self, x: int, y: int) -> bool:
        return self.in_bound(x, y) and self.__map[x][y].get_owner() != VOID

    def compute_neighbors(self):
        for x in range(MAP_WIDTH):
            for y in range(MAP_HEIGHT):
                self.is_inside(x, y - 1) and self.__map[x][y].set_neighbor(UP, self.__map[x][y - 1])
                self.is_inside(x, y + 1) and self.__map[x][y].set_neighbor(UP, self.__map[x][y + 1])
                self.is_inside(x + 1, y) and self.__map[x][y].set_neighbor(UP, self.__map[x + 1][y])
                self.is_inside(x - 1, y) and self.__map[x][y].set_neighbor(UP, self.__map[x - 1][y])

    def get_next_cell(self, unit: Unit, target: Cell) -> Cell:
        return self.__path_find.get_nearest_cell(self.__map, unit, target)

    def get_mine_spots(self):
        return self.__mines

    def get_value(self, x: int, y: int) -> int:
        return self.__map[x][y].get_owner() if self.in_bound(x, y) else NEUTRAL

    def get_neighbors(self, x: int, y: int) -> List[int]:
        neighbors = []
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                neighbors.append(self.get_value(x + dx, y + dy))
        return neighbors

    def update_map(self):
        current_map = []

        for x in range(MAP_WIDTH):
            row = []
            for y in range(MAP_HEIGHT):
                cell = Cell(x, y)
                cell.set_owner(self.get_cell(x, y).get_owner())
                row.append(cell)
            current_map.append(row)

        for x in range(MAP_WIDTH):
            for y in range(MAP_HEIGHT):
                neighbors = self.get_neighbors(x, y)

                if neighbors.count(NEUTRAL) >= MAPGENERATOR_T:
                    current_map[x][y].set_owner(NEUTRAL)
                else:
                    current_map[x][y].set_owner(VOID)
        
        for x in range(MAP_WIDTH):
            for y in range(MAP_HEIGHT):
                self.__map[x][y].set_owner(current_map[x][y].get_owner())

    def not_visited(self, x: int, y: int, visited: List[List[Cell]]) -> bool:
        if not self.is_inside(x, y):
            return False
        return visited[x][y].get_owner() == NEUTRAL

    def dfs(self, x: int, y: int, comp: List[Vec2], visited: List[List[Cell]]):
        pair = Vec2(x, y)
        comp.append(pair)

        # weird algorithm but ok (magic number)
        visited[x][y].set_owner(2)

        self.not_visited(x - 1, y, visited) and self.dfs(x - 1, y, comp, visited)
        self.not_visited(x + 1, y, visited) and self.dfs(x + 1, y, comp, visited)
        self.not_visited(x, y - 1, visited) and self.dfs(x, y - 1, comp, visited)
        self.not_visited(x, y + 1, visited) and self.dfs(x, y + 1, comp, visited)

    def find_comp(self) -> List[List[Cell]]:
        connected_comp = []
        visited = []

        for x in range(MAP_WIDTH):
            row = []
            for y in range(MAP_HEIGHT):
                cell = Cell(x, y)
                cell.set_owner(self.get_cell(x, y).get_owner())
                row.append(cell)
            visited.append(row)

        for x in range(MAP_WIDTH):
            for y in range(MAP_HEIGHT):
                if visited[x][y].get_owner() == NEUTRAL:
                    comp = []
                    self.dfs(x, y, comp, visited)
                    connected_comp.append(comp)
        
        return connected_comp

    def link_comp(self):
        connected_comp = self.find_comp()

        if len(connected_comp) == 1:
            return

        random_points = [random.choice(comp) for comp in connected_comp]

        for i in range(len(random_points)):
            for j in range(i + 1, len(random_points)):
                node1: Vec2 = random_points[i]
                node2: Vec2 = random_points[j]

                start_x = min([node1.get_x(), node2.get_x()])
                end_x = max([node1.get_x(), node2.get_x()])

                start_y = min([node1.get_y(), node2.get_y()])
                end_y = max([node1.get_y(), node2.get_y()])

                for x in range(start_x, end_x + 1):
                    self.__map[x][node2.get_y()].set_owner(NEUTRAL)
                    self.get_sym_cell(x, node2.get_y()).set_owner(NEUTRAL)

                for y in range(start_y, end_y + 1):
                    self.__map[node1.get_x()][y].set_owner(NEUTRAL)
                    self.get_sym_cell(node1.get_x(), y).set_owner(NEUTRAL)

    def generate_map(self, league: LEAGUE):
        
        for x in range(MAP_WIDTH):
            for y in range(MAP_HEIGHT):
                if random.random() > MAPGENERATOR_R:
                    self.__map[x][y].set_owner(NEUTRAL)
                else:
                    self.__map[x][y].set_owner(VOID)

        self.__map[0][0].set_owner(NEUTRAL)
        self.__map[0][1].set_owner(NEUTRAL)
        self.__map[1][0].set_owner(NEUTRAL)
        self.__map[1][1].set_owner(NEUTRAL)

        # print("First")
        # self.print_map()

        if league == LEAGUE.WOOD1 or league == LEAGUE.BRONZE:
            self.__map[1][0].set_mine()
            self.get_sym_cell(1, 0).set_mine()

        for _ in range(MAPGENERATOR_ITERATIONSAUTOMATA):
            self.update_map()
            # print("Update: " + str(i))
            # self.print_map()

        for row in self.__map:
            for cell in row:
                # No idea why
                inverted = ((cell.get_owner() + 2 + 1) % 2) - 2
                cell.set_owner(inverted)

        # print("Inverted")
        # self.print_map()
        
        for x in range(MAP_WIDTH):
            for y in range(x + 1):
                self.get_sym_cell(x, y).set_owner(self.get_cell(x, y).get_owner())

        # print("Sym")
        # self.print_map()

        for i in range(3):
            for j in range(3):
                self.get_cell(i, j).set_owner(NEUTRAL)
                self.get_sym_cell(i, j).set_owner(NEUTRAL)
        
        self.link_comp()

        if league == LEAGUE.WOOD1 or league == LEAGUE.BRONZE:
            for _ in range(round(self.__mines / 2) - 1):
                rand_x = random.randint(0, MAP_WIDTH - 1)
                rand_y = random.randint(0, MAP_HEIGHT - 1)
                
                while self.get_cell(rand_x, rand_y).get_owner() == VOID \
                or self.get_cell(rand_x, rand_y).is_mine() \
                or rand_x + rand_y == 0 \
                or rand_x + rand_y == MAP_HEIGHT + MAP_WIDTH - 2:
                    rand_x = random.randint(0, MAP_WIDTH - 1)
                    rand_y = random.randint(0, MAP_HEIGHT - 1)

                self.get_cell(rand_x, rand_y).set_mine()
                self.get_sym_cell(rand_x, rand_y).set_mine()

        self.compute_neighbors()
        self.__path_find.init(self.__map)

    def create_hq(self, player_count: int):

        assert player_count == 2, "More than 2 players mode not implemented"

        hq0 = Building(self.get_cell(0, 0), 0, BUILDING_TYPE.HQ)
        hq1 = Building(self.get_cell(MAP_WIDTH - 1, MAP_HEIGHT - 1), 1, BUILDING_TYPE.HQ)
        self.__HQs = hq0, hq1
        self.get_cell(0, 0).set_owner(0)
        self.get_cell(MAP_WIDTH - 1, MAP_HEIGHT - 1).set_owner(1)
        self.add_building(hq0)
        self.add_building(hq1)

    def get_HQs(self):
        return self.__HQs

    def kill_unit(self, unit: Unit):
        unit.die()
        unit.dispose()
        del self.__units[unit.get_id()]

    def clear_cell(self, cell: Cell):
        if cell.get_unit():
            self.kill_unit(cell.get_unit())
            cell.set_unit(None)

        if cell.get_building() and cell.get_building().get_type() != BUILDING_TYPE.HQ:
            building = cell.get_building()
            building.dispose()
            self.__buildings = list(filter(lambda b: b.get_x() != building.get_x() \
                or b.get_y() != building.get_y(), self.__buildings))
            cell.set_building(None)

    def kill_units(self, units: List[Unit]):
        [self.kill_unit(unit) for unit in units]

    def init_turn(self, player_id: int):
        self.compute_active_cells(player_id)
        self.kill_separated_units(player_id)
        self.compute_all_income()
        self.compute_gold(player_id)
        if self.__player_golds[player_id] < 0:
            self.negative_gold_wipeout(player_id)
        for unit in self.__units:
            if unit.get_owner() == player_id:
                unit.new_turn()

    def compute_active_cells(self, player_id: int):
        for row in self.__map:
            for cell in row:
                if cell.get_owner() == player_id:
                    cell.set_inactive()

        start = self.__HQs[player_id].get_cell()
        queue = [start]
        start.set_active()

        while len(queue):
            current_cell = queue[0]
            queue = queue[1:]

            for cell in current_cell.get_neighbors():
                if cell and not cell.is_active() and cell.get_owner() == player_id:
                    cell.set_active()
                    queue.append(cell)
        
    def kill_separated_units(self, player_id: int):
        to_kill = [unit for unit in self.__units.values() if unit.is_alive() and unit.get_owner() == player_id \
            and not unit.get_cell().is_active()]
        self.kill_units(to_kill)

    def get_building_cost(self, building_type: BUILDING_TYPE, player_id: int) -> int:
        cost = BUILD_COST(building_type)
        if building_type == BUILDING_TYPE.TOWER:
            return cost
        for building in self.__buildings:
            if building.get_type() == BUILDING_TYPE.MINE and building.get_owner() == player_id:
                cost += MINE_INREMENT
        return cost

    def compute_income(self, player_id: int):
        update_income = 0

        for row in self.__map:
            for cell in row:
                if cell.get_owner() == player_id and cell.is_active():
                    update_income += CELL_INCOME
        
        for building in self.__buildings:
            if building.get_owner() == player_id and building.get_type() == BUILDING_TYPE.MINE \
                and building.get_cell().is_active():

                update_income += MINE_INCOME

        for unit in self.__units.values():
            if unit.get_owner() == player_id and unit.is_alive() and unit.get_cell().is_active():
                update_income -= UNIT_UPKEEP[unit.get_level()]

        self.__player_income[player_id] = update_income

    def compute_all_income(self):
        for player_id in range(PLAYER_COUNT):
            self.compute_income(player_id)

    def compute_gold(self, player_id: int):
        self.__player_golds[player_id] += self.__player_income[player_id]

    def negative_gold_wipeout(self, player_id: int):
        self.__player_golds[player_id] = 0
        to_kill = [unit for unit in self.__units.values() if unit.is_alive() and unit.get_owner() == player_id]
        self.kill_units(to_kill)

    def add_unit(self, unit: Unit):
        self.clear_cell(unit.get_cell())

        # 1 billion IQ code here
        self.__units[unit.get_id()] = unit
        unit.get_cell().set_owner(unit.get_owner())
        unit.get_cell().set_unit(unit)

        self.__player_golds[unit.get_owner()] -= UNIT_COST[unit.get_level()]
        for player_id in range(PLAYER_COUNT):
            self.compute_income(player_id)

    def move_unit(self, unit: Unit, new_pos: Cell):
        self.clear_cell(new_pos)

        unit.get_cell().set_unit(None)
        unit.moved()
        unit.set_x(new_pos.get_x())
        unit.set_y(new_pos.get_y())
        unit.set_cell(new_pos)

        new_pos.set_owner(unit.get_owner())
        new_pos.set_unit(unit)

        for player_id in range(PLAYER_COUNT):
            self.compute_income(player_id)

    def add_building(self, building: Building):
        self.__buildings.append(building)
        building.get_cell().set_building(building)
        cost = self.get_building_cost(building.get_type(), building.get_owner())

        if building.get_type == BUILDING_TYPE.MINE:
            cost -= MINE_INREMENT
        
        self.__player_golds[building.get_owner()] -= cost
    
    def send_map(self, player: Player):
        for y in range(MAP_HEIGHT):
            line = ""
            for x in range(MAP_WIDTH):
                owner = self.__map[x][y].get_owner()
                data = ""
                if owner == VOID:
                    data = "#"
                elif owner == NEUTRAL:
                    data = "."
                else:
                    if owner == player.get_index():
                        data = 'o'
                    else:
                        data = 'x'
                    if self.__map[x][y]:
                        data = data.upper()
                line += data
            player.send_input_line(line)

    def send_mines(self, player: Player):
        self.send_map(player)

    def send_units(self, player: Player):
        player.send_input_line(str(len(self.__units.keys())))

        units = self.__units.values()

        # Don't have to sort the units

        for unit in units:
            player.send_input_line(f'{(unit.get_owner() - player.get_index() + PLAYER_COUNT) % PLAYER_COUNT} \
{unit.get_id()} {unit.get_level()} {unit.get_x()} \
{unit.get_y()}')

    def send_buildings(self, player: Player):
        player.send_input_line(len(self.__buildings))

        # Don't have to sort buildings either

        for building in self.__buildings:
            player.send_input_line(f'{(building.get_owner() - player.get_index() + PLAYER_COUNT) % PLAYER_COUNT} \
{building.get_int_value()} {building.get_x()} {building.get_y()}')

    def send_state(self, player: Player):

        player.send_input_line(self.__player_golds[player.get_index()])
        player.send_input_line(self.__player_income[player.get_index()])

        opponent_index = (player.get_index() + 1) % PLAYER_COUNT

        player.send_input_line(self.__player_golds[opponent_index])
        player.send_input_line(self.__player_income[opponent_index])

        self.send_map(player)
        self.send_buildings(player)
        self.send_units(player)

    def get_scores(self):
        scores = self.__player_golds.copy()
        for unit in self.__units:
            scores[unit.get_owner()] += UNIT_COST[unit.get_level()]
        return scores
    
    def print_map(self):
        
        line = ""
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                owner = self.__map[x][y].get_owner()
                data = ""
                if owner == VOID:
                    data = "#"
                elif owner == NEUTRAL:
                    data = "."
                else:
                    if owner == 0:
                        data = 'o'
                    else:
                        data = 'x'
                    if self.__map[x][y]:
                        data = data.upper()
                line += data
            line += "\n"
        print(line)