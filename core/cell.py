from .entity import Entity
from .constants import CAPTURE_LEVEL, MAX_LEVEL, BUILDING_TYPE
from typing import List


class Cell(Entity):

    def __init__(self, x, y):
        super().__init__(x, y, -1)
        self.__unit = None
        self.__building = None
        self.__active = True
        self.__neighbours: List[Cell] = [None, None, None, None]
        self.__mine_spot = False

    def get_unit(self):
        return self.__unit

    def set_unit(self, unit):
        self.__unit = unit

    def get_building(self):
        return self.__building

    def set_building(self, building):
        self.__building = building
    
    def get_neighbors(self):
        return self.__neighbours

    def get_neighbor(self, direction: int):
        if direction < 0 or direction >= 4:
            return None
        return self.__neighbours[direction]

    def set_neighbor(self, index: int, cell):
        self.__neighbours[index] = cell

    def is_active(self):
        return self.__active

    def set_active(self):
        self.__active = True

    def set_inactive(self):
        self.__active = False

    def is_mine(self):
        return self.__mine_spot

    def set_mine(self):
        self.__mine_spot = True

    def is_free(self):
        return self.__unit is None and self.__building is None

    def is_capturable(self, player_id: int, level: int):

        if self.get_owner() != player_id and self.is_active() and self.is_protected() and level < CAPTURE_LEVEL:
            return False
        
        if self.is_free():
            return True

        if self.get_owner() == player_id:
            return False

        if self.__unit:
            if level != MAX_LEVEL and level <= self.__unit.get_level():
                return False
        
        return True

    def is_protected(self):

        if self.__building and self.__building.get_type() == BUILDING_TYPE.TOWER:
            return True

        for neighbor in self.__neighbours:
            if not neighbor or neighbor.get_owner() != self.get_owner():
                continue
            
            building = neighbor.get_building()
            if neighbor.is_active() and building != None and building.get_type() == BUILDING_TYPE.TOWER:
                return True
        return False

    def is_playable(self, player_id: int):
        if self.get_owner() == player_id and self.is_active():
            return True
        print(self.__neighbours)
        for neighbor in self.__neighbours:
            if neighbor != None and neighbor.get_owner() == player_id and neighbor.is_active():
                return True
        return False

    def is_neighbor(self, cell):
        for neighbor in self.__neighbours:
            if neighbor != None and neighbor.get_x() == cell.get_x() and neighbor.get_y() == cell.get_y():
                return True
        return False

    def __repr__(self):
        return f'[{self.get_x()}, {self.get_y()}, Owner: {self.get_owner()}]'
