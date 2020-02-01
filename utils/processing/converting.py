# TODO use sgfmill for now but in future adapt for 52 size of board
from sgfmill import sgf
from utils.game import last_turn_player_reward

colors = 'bw'


def save_sgf(ended_game, sgf_filename):
    if not ended_game.is_ended:
        return

    sgf_game = sgf.Sgf_game(size=15)

    root = sgf_game.get_root()

    root.set('GM', 40)  # game type - dots
    root.set('CA', 'UTF-8')   # encoding
    root.set('RU', 'russian')   # rules

    # starting position
    root.set_setup_stones(ended_game.starting_crosses[-1], ended_game.starting_crosses[1])

    # result
    # TODO добавить поддержку счета
    winner = ended_game.get_winner()
    result_string = 'B+R' if winner == -1 else 'W+R' if winner == 1 else '0'
    root.set('RE', result_string)

    # set moves
    color_index = 0
    for move in map(ended_game.get_pos_of_ind, ended_game.moves):
        node = sgf_game.extend_main_sequence()

        color_index = 1 - color_index
        node.set_move(colors[color_index], move)

    with open(sgf_filename, 'wb') as f:
        f.write(sgf_game.serialise())

# moves_to_sgf({-1: [(13, 13)], 1: [(3, 3)]}, [(1, 2), (2, 3), (1, 2)], 'file.txt')