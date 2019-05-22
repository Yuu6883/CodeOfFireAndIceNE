from .gamestate import GameState
from .player import Player
from .constants import LEAGUE, PLAYER_COUNT, MOVE_PATTERN, MOVETRAIN_PATTERN, \
    BUILD_PATTERN, MAX_LEVEL, UNIT_COST, BUILDING_TYPE, MAX_TURNS
from .action import Action, ACTIONTYPE
from .building import Building
from .unit import Unit
import random
import time


class Engine:

    def __init__(self, league: LEAGUE = LEAGUE.WOOD3, sleep = 0, debug = False, strict = False, seed = random.randint(0, 2 * 31)):
        self.__players = []
        self.current_player: Player = None
        self.__state: GameState = None
        self.__league: LEAGUE = league
        self.__started = False
        self.__turns = 0
        self.__actions = []
        self.__move_count = 0
        self.__gameover = False
        self.__sleep = sleep
        self.__debug = debug
        self.__strict = strict
        self.__error_log = []
        self.seed = seed

    def get_map(self):
        return self.__state.get_map()
    
    def set_league(self, league: LEAGUE):
        if self.__started:
            return print("Can't change league when the game already started")
        self.__league = league

    def add_player(self, player: Player):
        if len(self.__players) >= PLAYER_COUNT:
            return print(f'Current player capacity is {PLAYER_COUNT}')
        self.__players.append(player)

    def start(self):
        if len(self.__players) != PLAYER_COUNT:
            return print("Not enough player to initiate the game")
        self.__started = True
        self.__state = GameState(self.seed, self.__league)
        self.__state.generate_map(self.__league)
        self.__state.create_hq(PLAYER_COUNT)

        self.current_player = random.choice(self.__players)
        self.gameloop()

    def get_turns(self):
        return self.__turns

    def get_player(self, index: int):
        return self.__players[index]
    
    def get_income(self, index: int):
        return self.__state.get_income(index)

    def get_gold(self, index: int):
        return self.__state.get_gold(index)

    def game_over(self):
        pass

    def gameloop(self):

        if self.__gameover:
            self.game_over()
            return

        if self.__turns // 2 >= MAX_TURNS:
            scores = self.__state.get_scores()
            print(f'Scores [ {self.__players[0]}: {scores[0]} ---- {self.__players[1]}: {scores[1]} ]')
            if scores[0] > scores[1]:
                self.kill_player(self.__players[1])
            elif scores[1] > scores[0]:
                self.kill_player(self.__players[0])
            else:
                print("Wow a tie")
            return
        success = 0
        self.__state.init_turn(self.current_player.get_index())
        self.__state.send_state(self.current_player)
        self.current_player.update()
        try:
            self.parse_action()
            success = sum([self.execute_action(action) for action in self.__actions])
        except Exception as e:
            print("Caught Exception while executing an action:")
            print(e)
            # raise e
            self.kill_player(self.current_player)
        if success != len(self.__actions) and not self.__debug and not self.__strict:
            self.debug("Some actions failed, enable strict mode to see more details")
        self.__actions.clear()
        self.__turns += 1
        self.check_hq_capture()
        self.current_player = self.__players[\
            (self.__players.index(self.current_player) + 1)\
                    % len(self.__players)]
        if self.__sleep > 0:
            time.sleep(self.__sleep)

        self.gameloop()
                    
    def kill_player(self, player: Player):
        player.lose()
        [p.win() for p in self.__players if not p is player]
        self.__gameover = True

    def parse_action(self):
        # Referee.java readInput
        msg = self.current_player.get_message()
        self.debug("Player Message:" + msg)
        actions_str = msg.split(";")
        for action_str in actions_str:
            action_str = action_str.strip(" ")
            if action_str == "WAIT":
                continue

            # Ignore Msg Command

            if not self.match_move_train(self.current_player, action_str) and \
                not self.match_build(self.current_player, action_str):
                # self.throw(f'Message not matching any regex {action_str}')
                print("Invalid Input: " + action_str)
                
    def match_move_train(self, player: Player, msg: str):
        if not MOVETRAIN_PATTERN.match(msg):
            return False
        args = msg.split()
        action_type = ACTIONTYPE.MOVE if msg.startswith("MOVE") else ACTIONTYPE.TRAIN
        
        try:
            id_or_level = int(args[1])
            x = int(args[2])
            y = int(args[3])
        except:
            self.throw("Invalid Integer")
            return True

        if not self.__state.in_bound(x, y):
            return self.throw("Coordinate not in map")

        if action_type == ACTIONTYPE.TRAIN:
            if self.__league == LEAGUE.WOOD3 and id_or_level != 1:
                return self.throw("WOOD3 can't train unit level that's not 1")
            self.create_train_action(player, id_or_level, x, y, msg)
        else:
            self.create_move_action(player, id_or_level, x, y, msg)   
        return True  

    def match_build(self, player: Player, msg: str):
        if not BUILD_PATTERN.match(msg):
            return False

        args = msg.split()
        try:
            build_type = Building.convert_type(args[1])
            x = int(args[2])
            y = int(args[3])
        except:
            return self.throw("Invalid Integer")
        finally:
            if not self.__state.in_bound(x, y):
                return self.throw("Coordinate not in map")
            
            action = Action(msg, ACTIONTYPE.BUILD, player.get_index(), \
                self.__state.get_cell(x, y), build_type)
            self.__actions.append(action)
            return True

    def create_train_action(self, player: Player, level: int, 
        x: int, y: int, action_str: str):
        if level <= 0 or level > MAX_LEVEL:
            return self.throw(f'Invalid Level: {level}')

        action = Action(action_str, ACTIONTYPE.TRAIN, player.get_index(),
            level, self.__state.get_cell(x, y))
        self.__actions.append(action)

    def create_move_action(self, player: Player, unit_id: int,
         x: int, y: int, action_str: str):
        if not self.__state.get_unit(unit_id):
            return self.throw(f'Unknown unit ID: {unit_id}')
        
        if player.get_index() != self.__state.get_unit(unit_id).get_owner():
            return self.throw("Trying to move enemy unit")

        action = Action(action_str, ACTIONTYPE.MOVE, player.get_index(),
        unit_id, self.__state.get_cell(x, y))
        self.__actions.append(action)

    def execute_action(self, action: Action):
        if action.get_type() != ACTIONTYPE.MOVE and \
             not action.get_cell().is_playable(action.get_player()):
            return self.throw(f'Cell is not playable at {action.get_cell()}')
        
        if action.get_type() == ACTIONTYPE.MOVE:
            return self.make_move_action(action)
        elif action.get_type() == ACTIONTYPE.TRAIN:
            return self.make_train_action(action)
        else:
            return self.make_build_action(action)

    def make_move_action(self, action: Action):

        if not self.__state.get_unit(action.get_unit_id()).can_play():
            return self.throw("Invalid move (unit can't move)")

        unit_id: int = action.get_unit_id()
        unit: Unit = self.__state.get_unit(unit_id)

        if not action.get_cell().is_capturable(action.get_player(), unit.get_level()):
            return self.throw("Not capturable")

        next_cell = self.__state.get_next_cell(unit, action.get_cell())

        if next_cell.get_x() == unit.get_cell().get_x() and \
            next_cell.get_y() == unit.get_cell().get_y():
            return self.throw("Unit can't stay still")

        self.__state.move_unit(unit, next_cell)
        self.__state.compute_all_active_cells()
        return True

    def make_train_action(self, action: Action):
        player: Player = self.__players[action.get_player()]
        if self.__state.get_gold(player.get_index()) < UNIT_COST[action.get_level()]:
            return self.throw("Not enough gold to train unit")

        if not action.get_cell().is_capturable(action.get_player(), action.get_level()):
            return self.throw("Can't capture cell" + str(action.get_cell()))
        
        unit = Unit(action.get_cell(), action.get_player(), action.get_level())
        self.__state.add_unit(unit)
        self.__state.compute_all_active_cells()
        return True

    def make_build_action(self, action: Action):

        if self.__league == LEAGUE.WOOD3:
            return self.throw("No build in WOOD3")
        if self.__league == LEAGUE.WOOD2 and \
            action.get_build_type() == BUILDING_TYPE.TOWER:
            return self.throw("No TOWER in WOOD2")
        if not action.get_cell().is_free():
            return self.throw("Cell is not free to build on")
        if not action.get_cell().get_owner() != action.get_player():
            return self.throw("Must be built on own territory")
        if self.__state.get_gold(action.get_player()) < \
            self.__state.get_building_cost(action.get_build_type(), action.get_player()):
            return self.throw("Not enough gold to build")
        if action.get_build_type() == BUILDING_TYPE.MINE and not action.get_cell().is_mine():
            return self.throw("Must build mine on a cell with mine")
        if action.get_build_type() == BUILDING_TYPE.TOWER and action.get_cell().is_mine():
            return self.throw("Can't build tower on a mine")
        # Finally
        building = Building(action.get_cell(), action.get_player(), action.get_build_type())
        self.__state.add_building(building)
        return True

    def check_hq_capture(self):
        for hq in self.__state.get_HQs():
            if hq.get_cell().get_owner() != hq.get_owner():
                self.kill_player(self.__players[hq.get_owner()])

    def log_errors(self):
        print("\n".join(self.__error_log))

    def clear_errors(self):
        print(f'{len(self.__error_log)} error logs cleared')
        self.__error_log.clear()

    def throw(self, msg: str):
        if self.__strict:
            raise Exception(msg)
        else:
            self.debug(msg)
        self.__error_log.append(msg)
        return False

    def debug(self, msg: str):
        if self.__debug:
            print(msg)