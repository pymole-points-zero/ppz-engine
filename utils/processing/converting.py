# TODO use sgfmill for now but in future adapt for 52 size of board
from sgfmill import sgf


colors = 'bw'


def moves_to_sgf(starting_crosses, moves, sgf_filename):
    game = sgf.Sgf_game(size=15)

    node = game.extend_main_sequence()
    node.set_setup_stones(starting_crosses[-1], starting_crosses[1])

    color_index = 0
    for move in moves:
        node = game.extend_main_sequence()

        color_index = 1 - color_index
        node.set_move(colors[color_index], move)

    with open(sgf_filename, 'wb') as f:
        f.write(game.serialise())

# moves_to_sgf({-1: [(13, 13)], 1: [(3, 3)]}, [(1, 2), (2, 3), (1, 2)], 'file.txt')