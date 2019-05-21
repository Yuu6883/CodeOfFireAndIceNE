from .vec2 import Vec2


class Entity(Vec2):
    def __init__(self, x=-1, y=-1, owner=0):
        super().__init__(x, y)
        self.__owner = owner

    def get_owner(self):
        return self.__owner

    def set_owner(self, owner):
        self.__owner = owner
