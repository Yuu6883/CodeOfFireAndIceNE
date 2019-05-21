class Player:

    def __init__(self, index: int):
        self.__index = index
        self.moves = 0
        self.message_queue = []
        self.transpose = False

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
        pass

    def lose(self, stats=None):
        pass