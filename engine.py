import math
import random
import numpy as np

class Game:
	sides = (
		(-1, 0),
		(0, -1),
		(0, 1),
		(1, 0)
	)

	diogonal = (
		(-1, -1),
		(1, 1),
		(-1, 1),
		(1, -1)
	)

	allsides = tuple(list(sides) + list(diogonal))

	def __init__(self, w=15, h=15):
		self.width = w
		self.height = h
		self.field_size = w * h

	def __str__(self):
		s = ""
		for i in self.field:
			for j in i:
				s += str(j[0]) + " " * (4 - len(str(j[0])))
			s += "\n"

		return s

	'''
	каждая точка (x, y) характеризуется:
		её обладателем [0]:
			0 - ничья
			-1 - принадлежит первому игроку
			1 - принадлежит второму игроку
		окруженностью [1]:
			0 - никем не окружена
			-1 - окружена первым игроком
			1 - окружена вторым игроком
	'''

	def reset(self, random_crosses = True, cross={}):
		self.field = np.full((self.width, self.height, 2), fill_value=0, dtype=np.int8)
		self.turn = 1
		self.score = {-1:0, 1:0}
		self.sur_zones = []
		self.busy_dots = []
		self.free_dots = set(range(self.field_size))
		self.player = -1

		if random_crosses:
			cross = self._random_crosses()
		elif not cross:
			cross = self._make_1cross(center=True)

		for owner, dots in cross.items():
			for x, y in dots:
				self.put_dot(x, y, owner)
				self.fix_dot(self.get_ind_of_pos(x, y))

		return cross

	def put_dot(self, x, y, owner):
		self.field[x, y, 0] = owner

	def auto_turn(self, ind, owner=None):
		# Automatised method for player turn
		pos = self.get_pos_of_ind(ind)
		if owner is None:
			owner = self.player
		self.put_dot(*pos, owner)
		self.fix_dot(ind)
		self.surround_check(mode='all')		# check all points of p1
		self.change_turn()					# change turn
		self.surround_check(mode='last')	# check p1 last turn for trapping 

	def fix_dot(self, dot_ind):
		self.busy_dots.append(dot_ind)
		self.free_dots.remove(dot_ind)

	def get_ind_of_pos(self, x, y):
		return self.width * y + x

	def get_pos_of_ind(self, ind):
		pos = (ind%self.width, ind//self.width)
		return pos

	def can_put_dot(self, x, y):
		# if no owner and not surrounded
		if self.field[x, y, 0] == 0 and self.field[x, y, 1] == 0:
			return True

		return False
	
	def wave_check(self, x, y):
		# self.player - surrounder
		# -self.player - surrounded
		chain = []
		
		toCheck = [(x, y)]
		checked = []

		while toCheck:
			dot = toCheck.pop(-1)

			# волна достигла края игровой доски
			if self.field[dot[0], dot[1], 0] != self.player and \
				((dot[0] == self.width - 1) or (dot[0] == 0) or (dot[1] == self.height - 1) or (dot[1] == 0)):
				return (
					False,	# возвращаем пустую цепь
					set(checked) - set(chain)
				)

			checked.append(dot)

			# инициализация соседних от текущей точки координат
			neighbors = [
				(dot[0] + off_x, dot[1] + off_y)
				for off_x, off_y in self.sides
			]

			for neib in neighbors:
				if neib in checked or neib in toCheck:
					continue
				if (self.field[neib[0], neib[1], 0] == self.player and self.field[neib[0], neib[1], 1] != -self.player):
					# добавляем точку в цепь, если она окружет
					if neib not in chain:
						chain.append(neib)
				else:
					# окружаемую точку или пустой пункт добавляем в стэк для дальнейшей проверки
					toCheck.append(neib)

		# составление графа, состоящего из точек цепи
		neigh = { i:[] for i in chain }
		for i in range(len(chain) - 1):
			elm1 = chain[i]
			for elm2 in chain[i + 1:]:
				if elm1 in ((elm2[0] + s[0], elm2[1] + s[1]) for s in self.allsides):
					neigh[elm1].append(elm2)
					neigh[elm2].append(elm1)

		# поиск циклов эйлера в графе
		start = 0
		pathes = []
		while len(pathes) == 0:
			while len(neigh[chain[start]]) != 2:
				start += 1

			toCheck = [([chain[start]], 0)]
			
			while toCheck:
				curPath, curPathLen = toCheck.pop()
				lastElement = curPath[-1]

				for n in neigh[lastElement]:
					if n in curPath:
						continue
					newPath = curPath + [n]
					updatedPath = (newPath, curPathLen + self._points_distance(lastElement, n))

					if n in neigh[chain[start]] and len(newPath) >= 4:
						pathes.append(updatedPath)
					else:
						toCheck.append(updatedPath)
			start += 1

		# нахождение длиннейшего цикла эйлера
		longest_len = 0
		for path, length in pathes:
			if length > longest_len:
				chain = path

		return (chain, set(checked) - set(chain))

	def surround_check(self, mode = 'all'):
		# формирование списка точек, для проверки на окружение
		if mode == 'all':
			toCheck = set(
				(x, y)
				for x in range(1, self.width - 1) for y in range(1, self.height - 1)
				if self.field[x, y, 0] == -self.player and self.field[x, y, 1] == 0
			)
		elif mode == 'last':
			toCheck = set([self.get_pos_of_ind(self.busy_dots[-1])])

		while toCheck:
			x, y = toCheck.pop()

			# запуск волны
			chain, sur = self.wave_check(x, y)	# получаем цепь и окруженные точки
			toCheck -= sur 		# убираем окруженные точки из проверки проверочной очереди

			# если волна не дошла до края и цепь не пуста
			if chain:
				for dot in sur:
					# добавляем точку, если её еще нет в занятых
					if self.field[dot[0], dot[1], 0] == 0:
						d = self.get_ind_of_pos(dot[0], dot[1])
						if d not in self.busy_dots:
							self.fix_dot(d)

					# если точка принадлежит текущему игроку и она окружена, то она освобождается
					# от окружения путем убавления одного очка противоположного игрока
					if (self.field[dot[0], dot[1], 0] == self.player) and (self.field[dot[0], dot[1], 1] == -self.player):
						self.score[-self.player] -= 1
					# если же точка вражеская, то получаем за неё плюс 1 к счету
					elif (self.field[dot[0], dot[1], 0] == -self.player):
						self.score[self.player] += 1


					# меняем владельца точки на игрока, который завершил ход
					self.field[dot[0], dot[1], 1] = self.player

				if chain not in self.sur_zones:
					self.sur_zones.append(chain)

	def _random_crosses(self):
		variants = (
			(self._make_4crosses, None),
			(self._make_1cross, False),
			(self._make_1cross, True),
			(None, None)
		)

		func, *args = random.choice(variants)

		if func is None:
			return {-1:[], 1:[]}
		elif args[0] is None:
			return func()
		else:
			return func(*args)

	def _make_4crosses(self):
		min_side = min(self.width, self. height)

		# square where the crosses will be
		square_side_len = math.floor(self._points_distance((min_side//2, 0), (0, min_side//2)))

		rand_cross_center = lambda: (
			math.floor(random.uniform(0.3, 0.6) * square_side_len),
			random.choice([-1, 1]) * math.floor(random.uniform(0.3, 0.6) * square_side_len)
		)
		
		# get two crosses relativly to the center of the board
		cross1_center = rand_cross_center()

		while True:
			cross2_center = rand_cross_center()
			if self._points_distance(cross1_center, cross2_center) > 4:
				break
		
		crosses_centers = [
			cross1_center,
			cross2_center
		]

		# reflect by horizontal and vertical side
		vertical_reflection = random.choice([-1, 1])
		for x, y in list(crosses_centers):
			crosses_centers.append( (-x, vertical_reflection * y) )

		# make absolute coords
		board_centerW, board_centerH = self.width//2, self.height//2
		for i in range(len(crosses_centers)):
			c = crosses_centers[i]
			crosses_centers[i] = (c[0] + board_centerW, c[1] + board_centerH)

		# make crosses
		crosses = {
			-1: [],
			1: []
		}

		for x, y in crosses_centers:
			crosses[-1].append( tuple(map(int, (x - 1, y - 1) )) )
			crosses[-1].append( tuple(map(int, (x, y) )) )
			crosses[1].append( tuple(map(int, (x, y - 1) )) )
			crosses[1].append( tuple(map(int, (x - 1, y) )) )

		return crosses

	def _make_1cross(self, center = False):
		# center
		
		crosses = {
			-1: [],
			1: []
		}
		
		if center:
			x, y = self.width//2, self.height//2
		else:
			# randomize the position of the cross
			x = random.randint(1, self.width - 2)
			y = random.randint(1, self.height - 2)

		crosses[-1].append( tuple(map(int, (x - 1, y - 1) )) )
		crosses[-1].append( tuple(map(int, (x, y) )) )
		crosses[1].append( tuple(map(int, (x, y - 1) )) )
		crosses[1].append( tuple(map(int, (x - 1, y) )) )

		return crosses

	def _points_distance(self, p1, p2):
		return math.sqrt( ((p1[0]-p2[0])**2)+((p1[1]-p2[1])**2) )

	def change_turn(self):
		# Определяем, кто ходит. Четный ход -1, нечетный 1
		self.turn += 1
		self.player = -self.player

	def gameEnded(self):
		return not self.free_dots


'''
game = Game(15, 15)
game.reset(random_crosses=True)
print(game)


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
print(game.field)
'''