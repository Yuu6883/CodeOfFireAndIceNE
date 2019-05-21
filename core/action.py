from .constants import ACTIONTYPE, BUILDING_TYPE
from .cell import Cell

class Action:

    def __init__(self, string: str, action_type: ACTIONTYPE, player: int, \
        id_level: int, cell: Cell, build_type: BUILDING_TYPE = None):
        self.__string = string
        self.__type = action_type
        self.__player = player
        if action_type == ACTIONTYPE.MOVE:
            self.__unit_id = id_level
        elif action_type == ACTIONTYPE.TRAIN:
            self.__level = id_level
        self.__cell = cell
        self.__build_type: BUILDING_TYPE = build_type

    def get_type(self):
        return self.__type

    def get_build_type(self):
        return self.__build_type

    def get_unit_id(self):
        return self.__unit_id

    def get_level(self):
        return self.__level

    def get_player(self):
        return self.__player

    def get_cell(self):
        return self.__cell

    def __str__(self):
        return self.__string
