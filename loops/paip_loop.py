# Points AI protocol 6
import random
from points.engine import Points
from mcts import MCTSRootParallelizer, MCTS
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
        self.log = open('/home/pymole/PycharmProjects/ppz-engine/lol' + str(random.randint(0, 100)), 'w')

        self.input = open(self.args.input_pipe, 'r')
        self.out = open(self.args.output_pipe, 'w')
        #
        # self.log.write(self.args.output_pipe + ' ' + self.args.input_pipe)
        # self.log.flush()
        # TODO select vs readline to reduce cpu usage
        while not self.quit_event:
            command_line = self.input.readline()
            if command_line:
                self.log.write(command_line)
                self.log.flush()
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
        except Exception as e:
            answer = '? ' + command_id + ' ' + command_name
            self.log.write(str(e))
            import sys, traceback
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_tb(exc_traceback, file=self.log)
            self.log.flush()
        finally:
            self.out.write(answer + '\n')
            self.out.flush()
            self.log.write(answer + '\n')
            self.log.flush()
            # print(answer)

    def list_commands(self):
        return self.commands_dispatch_table.keys()

    def quit(self):
        self.quit_event = True

    def init(self, width, height, random_seed):
        # TODO throw error if field size of init not equal to args field size
        random.seed(int(random_seed))

        # init game
        self.game = Points(self.args.field_width, self.args.field_height)
        if self.args.first_crosses is None and self.args.second_crosses is None:
            custom_crosses = None
        else:
            custom_crosses = [
                [] if self.args.first_crosses is None else self.args.first_crosses,
                [] if self.args.second_crosses is None else self.args.second_crosses,
            ]
        self.game.reset(custom_crosses=custom_crosses)

        # init MCTS
        self.mcts = MCTS(self.model, self.args.simulations, c_puct=2)

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

        # low level game control
        player = self.parse_color(color)

        # players switching every time
        self.game.make_move_coordinate(int(x), int(y), player)

        self.game.player = player
        self.game.surround_check(mode='surround')  # check surrounds
        self.game.turn_tick()
        self.game.player = self.game.opponent(self.game.player)
        self.game.surround_check(mode='suicide')  # check suicide move into house

        if not self.game.free_dots:
            self.game.is_ended = True

        return x, y, color

    def gen_move(self, color):
        if self.game is None or self.game.is_ended or self.mcts is None:
            raise Exception

        player = self.parse_color(color)
        self.game.player = player

        self.mcts.search(self.game)
        policy = self.mcts.get_dirichlet_policy(self.game)

        a = int(np.argmax(policy))

        x, y = self.game.get_pos_of_ind(a)

        return str(x), str(y), color

    def parse_color(self, color):
        if color == '1':
            return 1
        if color == '0':
            return 0

        raise Exception
