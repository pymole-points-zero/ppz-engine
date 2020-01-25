from engine import Game


def simple_surround():
    ##.#
    #.0.
    ##.#

    game = Game(3, 3)
    game.reset(random_crosses=False)

    game.auto_turn(0)
    game.auto_turn(1)
    game.auto_turn(2)
    game.auto_turn(3)
    game.auto_turn(4)
    game.auto_turn(5)
    game.auto_turn(6)
    game.auto_turn(7)

    print(game)
    print(game.score)


def double_simple():
    # #.#.#
    # .0.0.
    # #.#.#

    game = Game(5, 3)
    game.reset(random_crosses=False)

    game.make_move(1, 1)
    game.make_move(3, 1)
    game.make_move(5, 1)
    game.make_move(9, 1)
    game.make_move(11, 1)
    game.make_move(13, 1)

    game.make_move(6, -1)
    game.make_move(8, -1)

    game.make_move(7, 1)

    game.change_turn()
    print(game.player)
    game.surround_check(mode='surround')

    print(game)
    print(game.score)


def graph_while():
    # #....#
    # .#0##.
    # .#...#
    # .####.
    # #....#

    game = Game(6, 5)
    game.reset(random_crosses=False)
    print(game)

    game.make_move(1, 1)
    game.make_move(2, 1)
    game.make_move(3, 1)
    game.make_move(4, 1)
    game.make_move(6, 1)
    game.make_move(11, 1)
    game.make_move(12, 1)
    game.make_move(0, 2, 1)
    game.make_move(2, 2, 1)
    game.make_move(3, 2, 1)
    game.make_move(0, 3, 1)
    game.make_move(4, 3, 1)
    game.make_move(1, 4, 1)
    game.make_move(2, 4, 1)
    game.make_move(3, 4, 1)


    game.make_move(1, 1, -1)
    game.fix_dot(6)
    game.change_turn()
    game.surround_check(mode='suicide')

    print(game)
    print(game.score)


double_simple()
simple_surround()
# graph_while()