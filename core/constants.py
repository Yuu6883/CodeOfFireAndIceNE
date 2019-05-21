from enum import Enum
import re

MAP_WIDTH = 12
MAP_HEIGHT = 12

MAX_TURNS = 100
PLAYER_COUNT = 2

VOID = -2
NEUTRAL = -1

UP = 0
RIGHT = 1
DOWN = 2
LEFT = 3

CELL_INCOME = 1
MINE_INCOME = 4
MINE_INREMENT = 4

UNIT_COST = 0, 10, 20, 30
UNIT_UPKEEP = 0, 1, 4, 20
CAPTURE_LEVEL = 3

MAX_MOVE_LENGTH = 1
MAX_LEVEL = 3


class ACTIONTYPE(Enum):
    MOVE = 0
    BUILD = 1
    TRAIN = 2


class BUILDING_TYPE(Enum):
    HQ = 0
    MINE = 1
    TOWER = 2


class LEAGUE(Enum):
    WOOD3 = 0
    WOOD2 = 0
    WOOD1 = 0
    BRONZE = 0


MOVETRAIN_PATTERN = re.compile("^(MOVE|TRAIN) ([0-9]*) ([0-9]*) ([0-9]*)$")
MOVE_PATTERN = re.compile("^MOVE ([0-9]*) ([0-9]*) ([0-9]*)$")
TRAIN_PATTERN = re.compile("^TRAIN ([0-9]*) ([0-9]*) ([0-9]*)$")
MSG_PATTERN = re.compile("^MSG (.*)$")
BUILD_PATTERN = re.compile("^BUILD (TOWER|MINE) ([0-9]*) ([0-9]*)$")


def BUILD_COST(t):
    if t == BUILDING_TYPE.MINE:
        return 20
    if t == BUILDING_TYPE.TOWER:
        return 15
    return 0


def TYPE_TO_STRING(t):
    if t == BUILDING_TYPE.HQ:
        return "HQ"
    if t == BUILDING_TYPE.MINE:
        return "MINE"
    if t == BUILDING_TYPE.TOWER:
        return "TOWER"
    return ""


MAPGENERATOR_R = 0.45
MAPGENERATOR_ITERATIONSAUTOMATA = 3
MAPGENERATOR_T = 6
NUMBER_MINESPOTS_MIN = 8
NUMBER_MINESPOTS_MAX = 20
