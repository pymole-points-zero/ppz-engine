# Points AI protocol 6
import random
from points.engine import Points
from mcts.MCTS import MCTS
from tensorflow.keras.models import load_model
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
        self.model = load_model(self.args.weights)
        self.quit_event = False

        # open named pipe file for reading
        # self.log = open('/home/pymole/PycharmProjects/ppz-engine/lol' + str(random.randint(0, 100)), 'w')

        self.input = open(self.args.input_pipe, 'r')
        self.out = open(self.args.output_pipe, 'w')
        #
        # self.log.write(self.args.output_pipe + ' ' + self.args.input_pipe)
        # self.log.flush()
        # TODO select vs readline to reduce cpu usage
        while not self.quit_event:
            command_line = self.input.readline()
            if command_line:
                # self.log.write(command_line)
                # self.log.flush()
                self.dispatch(command_line)

        self.input.close()

    def dispatch(self, command_line):
        # parse command line
        command_id, command_name, *args = command_line.split()

        # execute command
        try:
            answer_arguments = self.commands_dispatch_table[command_name](*args)
            answer = '= ' + command_id + ' ' + command_name
            if answer_arguments is not None:
                answer += ' ' + ' '.join(answer_arguments)
        except Exception:
            answer = '? ' + command_id + ' ' + command_name
        finally:
            self.out.write(answer + '\n')
            self.out.flush()
            # self.log.write(answer + '\n')
            # self.log.flush()
            # print(answer)

    def list_commands(self):
        return self.commands_dispatch_table.keys()

    def quit(self):
        self.quit_event = True

    def init(self, width, height, random_seed):
        # TODO throw error if field size of init not equal to args field size
        random.seed(int(random_seed))

        # init game with center crosses
        self.game = Points(self.args.field_width, self.args.field_height)
        self.game.reset()

        # init MCTS
        self.mcts = MCTS(self.args.simulations, self.model, c_puct=4)

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
            player = 1
        elif color == '0':
            player = -1
        else:
            raise Exception

        if player != self.game.player:
            raise Exception

        # players switching every time
        self.game.make_move_coordinate(int(x), int(y), self.game.player)

        self.game.surround_check(mode='surround')  # check surrounds
        self.game.change_turn()
        self.game.surround_check(mode='suicide')  # check suicide move into house

        if not self.game.free_dots:
            self.game.is_ended = True

        return x, y, color

    def gen_move(self, color):
        if self.game is None or self.game.is_ended or self.mcts is None:
            raise Exception

        self.mcts.search(self.game)
        policy = self.mcts.get_policy(self.game)

        a = int(np.argmax(policy))

        x, y = self.game.get_pos_of_ind(a)
        color = '0' if self.game.player == -1 else '1'

        return str(x), str(y), color
