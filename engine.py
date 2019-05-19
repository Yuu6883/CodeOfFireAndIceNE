from gamestate import GameState
from player import Player
from constants import LEAGUE, PLAYER_COUNT
import random


if __name__ == "__main__":
    p1 = Player(0)
    p2 = Player(1)

    state = GameState(random.randint(0, 2 * 31), LEAGUE.WOOD3)
    state.generate_map(LEAGUE.WOOD3)
    state.create_hq(PLAYER_COUNT)

    state.send_state(p1)

    p1.print_lines()