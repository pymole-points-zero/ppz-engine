# Using model weights engine generates game match and writes results to stdout.
import argparse
import platform
import os
# TODO change dir to current


def main(args):
    # crosses example: 5,4;4,5
    def parse_crosses(crosses):
        return [tuple(map(int, cross.split(','))) for cross in crosses.split(';')]

    if args.first_crosses is not None:
        args.first_crosses = parse_crosses(args.first_crosses)
    if args.second_crosses is not None:
        args.second_crosses = parse_crosses(args.second_crosses)

    if args.mode == 'selfplay':
        from loops import SelfplayLoop
        loop = SelfplayLoop(args)
        loop.run()

    elif args.mode == 'match':
        from loops import MatchLoop
        loop = MatchLoop(args)
        loop.run()

    elif args.mode == 'paip':
        from loops import PAIPLoop
        loop = PAIPLoop(args)
        loop.run()


if __name__ == '__main__':
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

    parser = argparse.ArgumentParser()

    # all mode have engine arguments
    parser_engine = argparse.ArgumentParser()
    parser_engine.add_argument('--field_width', type=int, required=True)
    parser_engine.add_argument('--field_height', type=int, required=True)
    parser_engine.add_argument('--simulations', type=int, required=True)
    parser_engine.add_argument('--random_crosses', action='store_true')
    parser_engine.add_argument('--first_crosses', type=str, required=False)
    parser_engine.add_argument('--second_crosses', type=str, required=False)

    # add different modes as subcommands

    # workaround to run argparse subparsers required on <=3.6
    version = platform.python_version_tuple()
    if int(version[1]) <= 6:
        subparsers = parser.add_subparsers(dest='mode')
    else:
        subparsers = parser.add_subparsers(dest='mode', required=True)

    parser_selfplay = subparsers.add_parser('selfplay', parents=[parser_engine], add_help=False,
                                            help='Run selfplay loop to generate example')
    parser_selfplay.add_argument('--weights', type=str, required=True)

    parser_match = subparsers.add_parser('match', parents=[parser_engine], add_help=False,
                                         help='Match two neural networks')
    parser_match.add_argument('--candidate_weights', type=str, required=True)
    parser_match.add_argument('--best_weights', type=str, required=True)
    parser_match.add_argument('--candidate_turns_first', action='store_true')

    parser_protocol = subparsers.add_parser('paip', parents=[parser_engine], add_help=False,
                                            help='Run PointsAIProtocol v6 mode')
    parser_protocol.add_argument('--weights', type=str, required=True)
    parser_protocol.add_argument('--input_pipe', type=str, required=True)
    parser_protocol.add_argument('--output_pipe', type=str, required=True)

    args = parser.parse_args()

    main(args)