import numpy as np


def last_turn_player_reward(game):
	opponent = game.opponent(game.player)
	if game.score[opponent] > game.score[game.player]:
		return 1
	if game.score[opponent] < game.score[game.player]:
		return -1

	return 0


def field_perception(points, owners, cur_player):
	# current player always 0
	if cur_player == 1:
		points = np.flip(points, axis=2)
		owners = np.flip(owners, axis=2)

	return np.concatenate([points, owners], axis=2)


def symmetries(points, owners, cur_player, policy, value):
	field_matrix = field_perception(points, owners, cur_player)
	# TODO extract grounding move
	policy_matrix = np.reshape(policy, field_matrix.shape)

	# square matrix have more symmetries
	if field_matrix.shape[0] == field_matrix.shape[1]:
		for k in range(1, 5):
			for flip in (True, False):
				field = np.rot90(field_matrix, k)
				policy = np.rot90(policy_matrix, k)
				if flip:
					field = np.fliplr(field)
					policy = np.fliplr(policy)

				yield field, policy.ravel(), value
	else:
		v_flip_field = np.flipud(field_matrix)		# create for processor time economy
		v_flip_policy = np.flipud(policy_matrix)

		# initial
		yield field_matrix, policy, value
		# horizontal flip
		yield np.fliplr(field_matrix), np.fliplr(policy_matrix).ravel(), value
		# vertical flip
		yield v_flip_field, v_flip_policy.ravel(), value
		# horizontal and vertical
		yield np.fliplr(v_flip_field), np.fliplr(v_flip_policy).ravel(), value


# f = np.array([[[1, 2], [3, 4], [5, 6]], [[2, 1], [4, 3], [6, 5]]])
# print(f.reshape((-1, *f.shape)))

# o = np.array([[[1, 2], [3, 4], [5, 6]], [[1, 2], [3, 4], [5, 6]]])
#
# print(field_perception(f, o, 1))
