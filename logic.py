import numpy as np

def lastTurnPlayerReward(game):
	if game.score[-game.player] > game.score[game.player]:
		return 1
	elif game.score[-game.player] < game.score[game.player]:
		return -1

	return 0

def getFieldPerc(field, player):
	# game field from player's perspective
	return field * player

def stringRepresentation(field):
	out = (''.join(map(str, i)) for w in field for i in w)
	out = ''.join(out)
	return out

def getSymmetries(game, pi):
	l = []
	isSquare = game.width == game.height
	curPlrPercField = getFieldPerc(game.field, game.player)			# get field from player's percpective
	pi_board = np.reshape(pi, (game.width, game.height))

	if isSquare:
		pi_board = np.reshape(pi, (game.width, game.height))
		for i in range(1, 5):
			for j in [True, False]:
				newB = np.rot90(curPlrPercField, i)
				newPi = np.rot90(pi_board, i)
				if j:
					newB = np.fliplr(newB)
					newPi = np.fliplr(newPi)
				l.append( (newB, newPi.ravel()) )
	else:
		v_flip_perc = np.flip(curPlrPercField, 0)						# create for processor time economy
		v_flip_pi = np.flip(pi_board, 0)
		l = [
			(curPlrPercField, 				np.reshape(pi_board, (game.field_size,))),
			(np.flip(curPlrPercField, 1), 	np.reshape(np.flip(pi_board, 1), (game.field_size,))),
			(v_flip_perc, 					np.reshape(v_flip_pi, (game.field_size,))),
			(np.flip(v_flip_perc, 1), 		np.reshape(np.flip(v_flip_pi, 1), (game.field_size,)))
		]

	return l