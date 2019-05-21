class Player:

    def __init__(self, index: int, print_turn = False):
        self.__index = index
        self.moves = 0
        self.turns = 0
        self.message_queue = []
        self.transpose = False
        self.print_turn = print_turn

    def get_index(self):
        return self.__index
    
    def send_input_line(self, line):
        self.message_queue.append(line)

    def read_input(self):
        if not len(self.message_queue):
            return None
        line = self.message_queue[0]
        self.message_queue = self.message_queue[1:]
        return line

    def print_lines(self):
        for msg in self.message_queue:
            print(msg)

    def get_message(self):
        raise NotImplementedError()

    def update(self):
        raise NotImplementedError()

    def win(self, stats=None):
        print(str(self) + " won :D")

    def lose(self, stats=None):
        print(str(self) + " lost ):")

    def __str__(self):
        return type(self).__name__