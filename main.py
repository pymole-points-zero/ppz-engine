# Using model weights engine generates game match and writes results to stdout.

import argparse
from argparse import Namespace


parser = argparse.ArgumentParser()

parser.add_argument('mode', choices=('selfplay', 'match'))

parser.add_argument('--training_parameters', type=str)

# как для selfplay, так и для match
parser.add_argument('--best_weights', type=str)

parser.add_argument('--match_parameters', type=str)
parser.add_argument('--candidate_weights', type=str)

args = parser.parse_args()


test_params = {
    'field_size': (15, 15),
    'example_simulations': 2,
    'compare_simulations': 1,
    'random_crosses': False,
}

for key, value in test_params.items():
    args.__setattr__(key,value)


if args.mode == 'selfplay':
    if args.best_weights is None:
        parser.print_help()
        parser.exit(0)

    from selfplay import SelfplayLoop
    loop = SelfplayLoop(args)
    loop.run()

elif args.mode == 'match':
    if args.candidate_weights is None or args.best_weights is None:
        parser.print_help()
        parser.exit(1)

    if args.match_parameters is None:
        parser.print_help()
        parser.exit(1)

    from selfplay import MatchLoop
    loop = MatchLoop(args)
    loop.run()
