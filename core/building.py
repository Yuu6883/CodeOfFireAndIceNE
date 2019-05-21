from .constants import BUILDING_TYPE
from .entity import Entity


class Building(Entity):
    def __init__(self, cell, owner_id: int, t: BUILDING_TYPE):
        super().__init__(cell.get_x(), cell.get_y(), owner_id)
        self.__bt = t
        self.__cell = cell

    def get_type(self):
        return self.__bt

    def get_int_value(self):
        return self.__bt.value
    
    def get_cell(self):
        return self.__cell

    def dispose(self):
        pass

    @staticmethod
    def convert_type(s: str):
        if s == "MINE":
            return BUILDING_TYPE.MINE
        return BUILDING_TYPE.TOWER
