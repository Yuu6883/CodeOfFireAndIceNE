from .constants import MAP_HEIGHT, MAP_WIDTH, UP, RIGHT, DOWN, LEFT, MAX_MOVE_LENGTH
from .cell import Cell
from .unit import Unit
from .vec2 import Vec2
from typing import List

class Path:

    def __init__(self):
        self.__MAP_SIZE = MAP_HEIGHT * MAP_WIDTH
        self.__INFINITY = self.__MAP_SIZE + 1
        self.__distances: List[List[int]] = None

    def init(self, grid: List[List[Cell]]):

        # Init
        self.__distances = [[(0 if i == j else self.__INFINITY) for j in range(self.__MAP_SIZE)] \
             for i in range(self.__MAP_SIZE)]

        # Distance to neighbor = 1
        for row in grid:
            for cell in row:
                for neighbor in cell.get_neighbors():
                    if neighbor:
                        self.__distances[self.get_id(cell)][self.get_id(neighbor)] = 1
        
        # Floyd-Warshall
        for k in range(self.__MAP_SIZE):
            for i in range(self.__MAP_SIZE):
                for j in range(self.__MAP_SIZE):
                    if self.__distances[i][j] >= self.__distances[i][k] + self.__distances[k][j]:
                        self.__distances[i][j] = self.__distances[i][k] + self.__distances[k][j]

        with open("distances.txt", "w") as f:
            [f.write(repr(row)) for row in self.__distances]

    def get_nearest_cell(self, grid: List[List[Cell]], unit: Unit, target: Cell):
        start = unit.get_cell()
        player_id = unit.get_owner()
        start_id = self.get_id(start)
        target_id = self.get_id(target)
        order: List[int] = None

        if not player_id:
            order = UP, RIGHT, DOWN, LEFT
        else:
            order = DOWN, LEFT, UP, RIGHT

        visited = [False] * self.__MAP_SIZE

        queue = [Vec2(0, start_id)]
        visited[start_id] = True

        best_cell = start
        best_distance = self.__distances[start_id][target_id]

        while len(queue):

            pair = queue.pop()
            depth = pair.get_x()
            cell_id = pair.get_y()
            cell = self.get_cell(grid, cell_id)

            if self.__distances[cell_id][target_id] < best_distance and cell.is_capturable(player_id, unit.get_level()):
                best_distance = self.__distances[cell_id][target_id]
                best_cell = cell
            
            if depth < MAX_MOVE_LENGTH and cell.get_owner() == unit.get_owner():
                for direction in order:
                    neighbor = cell.get_neighbor(direction)
                    if neighbor:
                        neighbor_id = self.get_id(neighbor)
                        visited[neighbor_id] = True
                        queue.append(Vec2(depth + 1, neighbor_id))
        
        return best_cell
        
    def get_id(self, cell: Cell):
        return cell.get_x() + cell.get_y() * MAP_WIDTH

    def get_cell(self, grid: List[List[Cell]], cell_id: int) -> Cell:
        return grid[cell_id % MAP_WIDTH][cell_id // MAP_WIDTH]
