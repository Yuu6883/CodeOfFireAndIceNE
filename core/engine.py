from .gamestate import GameState
from .player import Player
from .constants import LEAGUE, PLAYER_COUNT, MOVE_PATTERN, MOVETRAIN_PATTERN, \
    BUILD_PATTERN, MAX_LEVEL, UNIT_COST, BUILDING_TYPE, MAX_TURNS
from .action import Action, ACTIONTYPE
from .building import Building
from .unit import Unit
import random
import time
import math

class Engine:

    def __init__(self, league: LEAGUE = LEAGUE.WOOD3, sleep = 0, \
        debug = False, strict = False, seed = None, auto_restart=False,\
            silence=False, idle_limit = 5):
        self.__players = []
        self.current_player: Player = None
        self.__state: GameState = None
        self.__league: LEAGUE = None
        self.__started = False
        self.__turns = 0
        self.__actions = []
        self.__move_count = 0
        self.__gameover = False
        self.__sleep = sleep
        self.__debug = debug
        self.__strict = strict
        self.__error_log = []
        self.seed = seed if seed else random.randint(0, 2 * 31)
        self.set_league(league)
        self.__auto_restart = auto_restart
        self.__silence = silence
        self.__idle_limit = idle_limit
        self.__result = ""

    def restart(self, new_seed=True):
        if self.__started:
            self.print("Force restarting")
        [p.reset() for p in self.__players]

        self.__started = True
        self.__gameover = False
        self.__turns = 0
        self.__actions.clear()
        self.__move_count = 0
        self.__idle_count = [0, 0]
        random.seed(time.thread_time_ns())
        if not self.__state:
            self.__state = GameState(random.randint(0, 2** 31) if new_seed else self.seed \
                , self.__league)
            self.__state.generate_map(self.__league)
        else:
            self.__state.reset()
        self.__state.create_hq(PLAYER_COUNT)

        self.current_player = random.choice(self.__players)
        self.send_init_messages()
        
        while not self.__gameover:
            self.gameloop()

    def get_map(self):
        return self.__state.get_map()
    
    def set_league(self, league: LEAGUE):
        if self.__started:
            return self.print("Can't change league when the game already started")
        self.__league = league
        [p.set_league(self.__league) for p in self.__players]

    def add_player(self, player_class, *args, **kwargs):
        if len(self.__players) >= PLAYER_COUNT:
            return self.print(f'Current player capacity is {PLAYER_COUNT}')
        new_player = player_class(len(self.__players), *args, **kwargs)
        new_player.set_league(self.__league)
        self.__players.append(new_player)
        return new_player

    def set_player(self, players):
        assert len(players) == 2
        assert isinstance(players[0], Player)
        assert isinstance(players[1], Player)
        self.__players = players

    def get_players(self):
        return self.__players

    def start(self):
        if len(self.__players) != PLAYER_COUNT:
            return self.print("Not enough player to initiate the game")
        self.restart(new_seed=False)

    def send_init_messages(self):
        for player in self.__players:
            player.send_init_input(self.__state.get_mine_spots())
            for row in self.__state.get_map():
                for cell in row:
                    if cell.is_mine():
                        player.send_init_input(f'{cell.get_x()} {cell.get_y()}')
            player.init()

    def get_turns(self):
        return self.__turns

    def get_player(self, index: int):
        return self.__players[index]
    
    def get_income(self, index: int):
        return self.__state.get_income(index)

    def get_gold(self, index: int):
        return self.__state.get_gold(index)

    def game_over(self):
        self.__gameover= True
        self.__started = False
        if self.__auto_restart:
            self.restart()

    def get_result(self):
        return self.__result

    def activate_players(self):
        [p.activate() for p in self.__players]

    def deactivate_players(self):
        [p.deactivate() for p in self.__players]

    def gameloop(self):

        if self.__gameover:
            self.game_over()
            return

        if self.__turns // 2 >= MAX_TURNS:
            scores = self.__state.get_scores()
            self.print(f'Scores [ {self.__players[0]}: {scores[0]} --- {self.__players[1]}: {scores[1]} ]')
            if scores[0] > scores[1]:
                self.__result = f'{self.__players[0]} [{scores[0]} --- {scores[1]}] {self.__players[1]}'
                self.kill_player(self.__players[1])
            elif scores[1] > scores[0]:
                self.__result = f'{self.__players[0]} [{scores[0]} --- {scores[1]}] {self.__players[1]}'
                self.kill_player(self.__players[0])
            else:
                self.print("Wow a tie")
                self.__result = f'Tie [{scores[0]} --- {scores[1]}]'
                self.__gameover = True
                self.game_over()
            self.__players[0].add_score(scores[0])
            self.__players[1].add_score(scores[1])
            return
        success = 0
        self.__state.init_turn(self.current_player.get_index())
        self.__state.send_state(self.current_player)
        try:
            self.current_player.update()
        except Exception as e:
            self.print(f'{self.current_player} crashed at turn {self.__turns // 2}')
            self.print(e)
            # raise e
        try:
            self.parse_action()
            success = sum([self.execute_action(action) for action in self.__actions])
            if not success:
                self.__idle_count[self.current_player.get_index()] += 1
            else:
                self.__idle_count[self.current_player.get_index()] = 0
            self.check_idle()
        except Exception as e:
            self.print("Caught Exception while executing an action:")
            self.print(e)
            scores = self.__state.get_scores()
            for player in self.__players:
                if self.current_player is player:
                    player.add_score(scores[player.get_index()] - 100)
                else:
                    player.add_score(scores[player.get_index()])
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

    def check_idle(self):
        if sum([idle_time >= self.__idle_limit for idle_time in self.__idle_count]) == PLAYER_COUNT:
            scores = self.__state.get_scores()
            self.__players[0].add_score(scores[0] - 50)
            self.__players[1].add_score(scores[1] - 50)
            self.__result = f'{self.__players[0]} [{scores[0]} --- {scores[1]}] {self.__players[1]} | idle({self.__idle_limit})'
            self.kill_all()

    def kill_all(self):
        [p.lose() for p in self.__players]
        self.__gameover = True
        self.game_over()
                    
    def kill_player(self, player: Player):
        player.lose()
        [p.win() for p in self.__players if not p is player]
        self.__gameover = True
        self.game_over()

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
                self.print("Invalid Input: " + action_str)
                
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

        if not action.get_cell().is_capturable(action.get_player(), unit.get_level()) and \
            abs(unit.get_x() - action.get_cell().get_x()) + abs(unit.get_y() - action.get_cell().get_y()) == 1:
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
                loser_index = hq.get_owner() 
                winner_index = hq.get_cell().get_owner()
                scores = self.__state.get_scores()
                reward = round(math.sqrt(max([(MAX_TURNS - self.__turns) // 2, 0]))) * 100 + 500
                winner_score = scores[winner_index] + reward
                loser_score = scores[loser_index] + reward // 5

                self.__result = f'{self.__players[0]} [{winner_score} --- {loser_score}] {self.__players[1]} | {self.__players[winner_index]} caputure HQ'

                self.__players[winner_index].add_score(winner_score)
                self.__players[loser_index].add_score(loser_score)
                
                self.kill_player(self.__players[loser_index])

    def log_errors(self):
        self.print("\n".join(self.__error_log))

    def clear_errors(self):
        self.print(f'{len(self.__error_log)} error logs cleared')
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
            self.print(msg)

    def print(self, *args):
        if not self.__silence:
            print(*args)