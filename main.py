# Using model weights engine generates game match and writes results to stdout.
import argparse
import platform
import os

# shutdown tensorflow
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'


parser = argparse.ArgumentParser()

# all mode have engine arguments
parser_engine = argparse.ArgumentParser()
parser_engine.add_argument('--field_width', type=int, required=True)
parser_engine.add_argument('--field_height', type=int, required=True)
parser_engine.add_argument('--simulations', type=int, required=True)
parser_engine.add_argument('--random_crosses', action='store_true')

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