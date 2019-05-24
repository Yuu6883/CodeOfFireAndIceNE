class Player:

    def __init__(self, index: int, print_turn = False):
        self.__index = index
        self.moves = 0
        self.turns = 0
        self.win_num = 0
        self.lost_num = 0
        self.message_queue = []
        self.init_input = []
        self.transpose = False
        self.scores = []
        self.print_turn = print_turn
        self.__league = None

    def get_index(self):
        return self.__index

    def set_index(self, index):
        self.__index = index
    
    def send_input_line(self, line):
        self.message_queue.append(line)

    def reset(self):
        self.moves = 0
        self.turns = 0
        self.message_queue.clear()
        self.init_input.clear()
        self.transpose = False

    def read_input(self):
        if not len(self.message_queue):
            return None
        line = self.message_queue[0]
        self.message_queue = self.message_queue[1:]
        return line

    def read_init_input(self):
        if not len(self.init_input):
            return None
        line = self.init_input[0]
        self.init_input = self.init_input[1:]
        return line

    def print_lines(self):
        for msg in self.message_queue:
            print(msg)

    def get_message(self):
        raise NotImplementedError()

    def update(self):
        raise NotImplementedError()

    def win(self, stats=None):
        self.win_num += 1
        # print(str(self) + " won :D")
        self.on_gameover()

    def lose(self, stats=None):
        self.lost_num += 1
        # print(str(self) + " lost ):")
        self.on_gameover()

    def __str__(self):
        return type(self).__name__ + "#" + str(self.__index)

    def set_league(self, league):
        self.__league = league

    def get_league(self):
        return self.__league

    def send_init_input(self, msg):
        self.init_input.append(msg)

    def init(self, msg):
        pass

    def on_gameover(self):
        pass

    def reset_stats(self):
        self.win_num = 0
        self.lost_num = 0
        self.scores.clear()

    def add_score(self, score:int):
        self.scores.append(score)