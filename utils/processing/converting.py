from unisgf.game_tree import GameTree
from unisgf.collection import Collection
from unisgf.property_value import PropertyValue
from unisgf.rendering import Renderer
from string import ascii_letters
from itertools import islice


colors = 'BW'


class DotsMove(PropertyValue):
    @staticmethod
    def validate_string(data: str):
        if len(data) != 2:
            raise ValueError

        x, y = data
        x = ascii_letters.find(x)
        if x == -1:
            return ValueError
        y = ascii_letters.find(y)
        if y == -1:
            return ValueError

        return x, y

    @staticmethod
    def validate_value(value):
        try:
            x, y = value
        except Exception:
            raise ValueError

        if not isinstance(x, int) or not isinstance(y, int) or x < 0 or y < 0:
            raise ValueError

        return value

    def render(self):
        return ascii_letters[self.value[0]] + ascii_letters[self.value[1]]


def save_sgf(game, sgf_filename):
    if not game.is_ended:
        # TODO raise GameIsNotEnded
        return

    game_tree = GameTree()
    root = game_tree.get_root()
    root['SZ'] = [game.width, game.height]
    root['GM'] = [40]          # game type - dots
    root['CA'] = ['UTF-8']     # encoding
    root['RU'] = ['russian']   # rules

    # starting position (stones)
    if game.starting_crosses[-1]:
        root['AB'] = game.starting_crosses[-1]

    if game.starting_crosses[1]:
        root['AW'] = game.starting_crosses[1]

    # result
    winner = game.get_winner()
    if winner == -1:
        result_string = 'B+' + str(game.score[-1] - game.score[1])
    elif winner == 1:
        result_string = 'W+' + str(game.score[1] - game.score[-1])
    else:
        result_string = '0'

    root['RE'] = [result_string]

    # set moves before grounding
    node = root
    color_index = 0     # 0 - B, first, -1 in game; 1 - W, second, 1 in game

    if game.grounding_move_index is not None:
        moves_before_grounding = islice(game.moves, 0, game.grounding_move_index, 1)
    else:
        moves_before_grounding = game.moves

    for move in map(game.get_pos_of_ind, moves_before_grounding):
        node = node.create_child()
        node[colors[color_index]] = [DotsMove(move)]
        color_index = 1 - color_index

    # grounding saves as node with one property and multiple property values
    if game.grounding_move_index is not None:
        # skip grounding move and fill property with grounding surround
        # moves (after grounding move at game.grounding_move_index)
        node = node.create_child()
        color_index = 1 - color_index
        node[colors[color_index]] = [
            DotsMove(move)
            for move in map(game.get_pos_of_ind,
                            islice(game.moves, game.grounding_move_index + 1, len(game.moves), 1))
        ]

    collection = Collection()
    collection.append(game_tree)

    renderer = Renderer()
    renderer.render_file(sgf_filename, collection)