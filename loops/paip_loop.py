# Points AI protocol 6
import random
from points.engine import Points
from mcts.MCTS import MCTS
from neural import RNN
import numpy as np


class PAIPLoop:
    def __init__(self, args):
        self.args = args
        self.game = None
        self.reading_thread = None
        self.quit_event = False
        self.commands_dispatch_table = {
            'list_commands': self.list_commands,
            'quit': self.quit,
            'init': self.init,
            'author': self.author,
            'name': self.name,
            'version': self.version,
            'license': self.license,
            'play': self.play,
            'gen_move': self.gen_move,
            # 'gen_move_with_complexity': self.gen_move_with_complexity,
            # 'gen_move_with_time': self.gen_move_with_time,
            # 'gen_move_with_full_time': self.gen_move_with_full_time,
            # 'undo': self.undo,
        }

    def run(self):
        self.nnet = RNN.from_file(self.args.weights)
        self.quit_event = False

        # open named pipe file for reading
        pipe = open(self.args.pipe, 'r')

        while not self.quit_event:
            command_line = pipe.readline()
            if command_line:
                self.dispatch(command_line)

    def dispatch(self, command_line):
        # parse command line
        command_id, command_name, *args = command_line.split()

        # execute command
        try:
            answer_arguments = self.commands_dispatch_table[command_name](*args)
            answer = '=' + command_id + command_name
            if answer_arguments is not None:
                answer += ' '.join(answer_arguments)
        except Exception:
            answer = '? ' + command_id + command_name
        finally:
            print(answer)

    def list_commands(self):
        return self.commands_dispatch_table.keys()

    def quit(self):
        self.quit_event = True

    def init(self, width, height, random_seed):
        random.seed(int(random_seed))
        # init game with center crosses
        self.game = Points(int(width), int(height))
        self.game.reset(random_crosses=False)

        # init MCTS
        self.mcts = MCTS(self.args.parameters['example_simulations'], self.nnet, c_puct=4)

    def author(self):
        return ('Roman Shevela',)

    def name(self):
        return ('Pymole Points Zero',)

    def version(self):
        return ('0.1',)

    def license(self):
        return ('Unknown',)

    def play(self, x, y, color):
        if self.game is None or self.game.is_ended:
            raise Exception

        if color == '1':
            color = 1
        elif color == '0':
            color = -1
        else:
            raise Exception

        # players switching every time
        self.game.make_move_coordinate(int(x), int(y), self.game.player)

        self.game.surround_check(mode='surround')  # check surrounds
        self.game.change_turn()
        self.game.surround_check(mode='suicide')  # check suicide move into house

        if not self.game.free_dots:
            self.is_ended = True

    def gen_move(self):
        if self.game is None or self.game.is_ended or self.mcts is None:
            raise Exception

        self.mcts.search(self.game)
        policy = self.mcts.get_policy(self.game)

        a = int(np.argmax(policy))

        x, y = self.game.get_pos_of_ind(a)
        color = '0' if self.game.player == -1 else '1'

        return x, y, color
