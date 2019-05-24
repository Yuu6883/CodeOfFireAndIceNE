from .entity import Entity


class Unit(Entity):
    __unit_id_count = 1

    def __init__(self, cell, owner_id: int, level: int):
        super().__init__(cell.get_x(), cell.get_y(), owner_id)
        self.__alive = True
        self.__can_move = False
        self.__cell = cell
        self.__level = level
        self.__id = Unit.__unit_id_count
        Unit.__unit_id_count += 1

    def get_id(self):
        return self.__id

    def get_level(self):
        return self.__level

    def is_alive(self):
        return self.__alive

    def die(self):
        self.__alive = False

    def new_turn(self):
        self.__can_move = True

    def moved(self):
        self.__can_move = False

    def can_play(self):
        return self.__can_move

    def set_cell(self, cell):
        self.__cell = cell

    def get_cell(self):
        return self.__cell

    def dispose(self):
        self.__cell.set_unit(None)
        self.__alive = False

    def __repr__(self):
        return f'Level {self.__level} at {self.__cell}'

    def __str__(self):
        return repr(self)
