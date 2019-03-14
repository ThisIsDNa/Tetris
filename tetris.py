#------------------------------------------------------------------------
# 1. The Tetris grid is 10 cells wide and 22 cells tall, with the top 2 rows hidden.
# 2. All Tetrominoes (Tetris pieces) will start in the middle of the top 2 rows.
# 3. There are 7 Tetrominoes : “I”, “O”, “J”, “L”, “S”, “Z”, “T”.
# 4. The Super Rotation System is used for all rotations.
# 5. The “7 system” random generator is used to randomize the next pieces.
# 6. One lookahead piece is allowed (the player knows what the next piece will be).
#------------------------------------------------------------------------
import random as rand
from enum import Enum
import pygame, sys
import numpy as np
import getpass
import math
import ast
import pyglet

#------------------------------------------------------------------------
# 1. Basic Configuration
# 2. Colors + Pieces
#		- Color: 0 [BG]
#		- Color: 1 [T-Piece]
#		- Color: 2 [S-Piece]
#		- Color: 3 [Z-Piece]
#		- Color: 4 [J-Piece]
#		- Color: 5 [L-Piece]
#		- Color: 6 [I-Piece]
#		- Color: 7 [O-Piece]
#		- Color: 8 [BG Grid]
# 3. Pieces
#------------------------------------------------------------------------
cell_size =	25
cols =		10
rows =		22
maxfps = 	60

colors = [
(0, 0, 0),
(148, 0, 211),
(0, 255, 127),
(176, 48, 96),
(255, 127, 80),
(65, 105, 225),
(224, 255, 255),
(255, 215, 0),
(35, 35, 35)
]

tetris_shapes = [
	[[1, 1, 1],
	 [0, 1, 0]],

	[[0, 2, 2],
	 [2, 2, 0]],
	
	[[3, 3, 0],
	 [0, 3, 3]],
	
	[[4, 0, 0],
	 [4, 4, 4]],
	
	[[0, 0, 5],
	 [5, 5, 5]],
	
	[[6, 6, 6, 6]],
	
	[[7, 7],
	 [7, 7]]
]

#------------------------------------------------------------------------
# This section contains the following mechanics:
#   1. Rotation
#   2. Collision Check
#   3. Row Clear
#   4. Join Matrices
#   5. New Board
#------------------------------------------------------------------------
def rotate_clockwise(shape):
	return [ [ shape[y][x]
			for y in range(len(shape)) ]
		for x in range(len(shape[0]) - 1, -1, -1) ]

def check_collision(board, shape, offset):
	off_x, off_y = offset
	for cy, row in enumerate(shape):
		for cx, cell in enumerate(row):
			try:
				if cell and board[ cy + off_y ][ cx + off_x ]:
					return True
			except IndexError:
				return True
	return False

def remove_row(board, row):
	del board[row]
	return [[0 for i in range(cols)]] + board
	
def join_matrices(mat1, mat2, mat2_off):
	off_x, off_y = mat2_off
	for cy, row in enumerate(mat2):
		for cx, val in enumerate(row):
			mat1[cy+off_y-1	][cx+off_x] += val
	return mat1

def new_board():
	board = [ [ 0 for x in range(cols) ]
				  for y in range(rows) ]
	board += [[ 1 for x in range(cols)]]
	return board

class Moves(Enum):
    LEFT  = 1
    RIGHT = 2
    DROP  = 3
    ROT   = 4

#------------------------------------------------------------------------
# This sections contains the actual Tetris mechanics:
# a. Incoming tetromino
# b. New game
# c. Clearing lines
# d. Movement
# e. Quitting
# f. Drop
# g. Hard drop
# h. Rotations
# i. Pause
# j. Controls
# k. AI
#------------------------------------------------------------------------
class TetrisApp(object):
	def __init__(self, training = False):
		pygame.init()
		pygame.key.set_repeat(250,25)
		self.width = cell_size*(cols+6)
		self.height = cell_size*rows
		self.rlim = cell_size*cols
		self.bground_grid = [[ 8 if x%2==y%2 else 0 for x in range(cols)] for y in range(rows)]
		self.default_font =  pygame.font.Font(pygame.font.get_default_font(), 12)
		self.screen = pygame.display.set_mode((self.width, self.height))
		pygame.event.set_blocked(pygame.MOUSEMOTION)
		# rand.seed(1)
		self.next_stone = tetris_shapes[rand.randrange(len(tetris_shapes))]
		self.training = training

		snd = pyglet.media.load('fallout.ogg')
		looper = pyglet.media.SourceGroup(snd.audio_format, None)
		looper.loop = True
		looper.queue(snd)
		p = pyglet.media.Player()
		p.queue(looper)
		p.play()

		self.init_game()

	def new_stone(self):
		self.stone = self.next_stone[:]
		self.next_stone = tetris_shapes[rand.randrange(len(tetris_shapes))]
		self.stone_x = int(cols / 2 - len(self.stone[0])/2)
		self.stone_y = 0
		if check_collision(self.board,
		                   self.stone,
		                   (self.stone_x, self.stone_y)):
			self.gameover = True
	
	def init_game(self):
		self.board = new_board()
		self.new_stone()
		self.level = 1
		self.score = 0
		self.lines = 0
		pygame.time.set_timer(pygame.USEREVENT+1, 1000)
	
	def disp_msg(self, msg, topleft):
		x,y = topleft
		for line in msg.splitlines():
			self.screen.blit(
				self.default_font.render(
					line,
					False,
					(255,255,255),
					(0,0,0)),
				(x,y))
			y+=14
	
	def center_msg(self, msg):
		for i, line in enumerate(msg.splitlines()):
			msg_image =  self.default_font.render(line, False,
												 (255,255,255), (0,0,0))
			msgim_center_x, msgim_center_y = msg_image.get_size()
			msgim_center_x //= 2
			msgim_center_y //= 2
			self.screen.blit(msg_image, (self.width // 2-msgim_center_x,
										 self.height // 2-msgim_center_y+i*22))
	
	def draw_matrix(self, matrix, offset):
		off_x, off_y  = offset
		for y, row in enumerate(matrix):
			for x, val in enumerate(row):
				if val:
					pygame.draw.rect(
						self.screen,
						colors[val],
						pygame.Rect((off_x+x) * cell_size,
									(off_y+y) * cell_size, 
									cell_size, cell_size), 0)
	
#---------------------------------------------------------------------------
# Original BPS scoring system (Line Clear Points)
#	- single: 40
#	- double: 100
#	- triple: 300
#	- tetris: 1200
#---------------------------------------------------------------------------
	def add_cl_lines(self, n):
		linescores = [0, 40, 100, 300, 1200]
		self.lines += n
		self.score += linescores[n] * self.level
		if self.lines >= self.level*6:
			self.level += 1
			newdelay = 1000-50*(self.level-1)
			newdelay = 100 if newdelay < 100 else newdelay
			pygame.time.set_timer(pygame.USEREVENT+1, newdelay)
	
	def move(self, delta_x):
		if not self.gameover and not self.paused:
			new_x = self.stone_x + delta_x
			if new_x < 0:
				new_x = 0
			if new_x > cols - len(self.stone[0]):
				new_x = cols - len(self.stone[0])
			if not check_collision(self.board,
			                       self.stone,
			                       (new_x, self.stone_y)):
				self.stone_x = new_x


    # def holdPiece(self):
	# 	if not self.gameover and not self.paused:
    #     if self.hold == 0:
    #         self.hold = self.active
    #         self.active = self.queue.pop(0)
    #         self.queue.append(Piece(randint(0,6),0))
    #     else:
    #         tmp = self.active
    #         self.active = self.hold
    #         self.hold = tmp 
    #     self.xActive = 4
    #     self.yActive = 0


	def quit(self):
		self.center_msg("Exiting...")
		pygame.display.update()
		sys.exit()
	
	def drop(self, manual):
		if not self.gameover and not self.paused:
			self.score += 1 if manual else 0
			self.stone_y += 1
			if check_collision(self.board,
			                   self.stone,
			                  (self.stone_x, self.stone_y)):
				self.board = join_matrices(self.board,
										   self.stone,
										  (self.stone_x, self.stone_y))
				self.new_stone()
				cleared_rows = 0
				while True:
					for i, row in enumerate(self.board[:-1]):
						if 0 not in row:
							self.board = remove_row(self.board, i)
							cleared_rows += 1
							break
					else:
						break
				self.add_cl_lines(cleared_rows)
				return True
		return False
	
	def insta_drop(self):
		if not self.gameover and not self.paused:
			while(not self.drop(True)):
				pass
	
	def rotate_stone(self):
		if not self.gameover and not self.paused:
			new_stone = rotate_clockwise(self.stone)
			if not check_collision(self.board, new_stone,
			                       (self.stone_x, self.stone_y)):
				self.stone = new_stone
	
	def toggle_pause(self):
		self.paused = not self.paused
	
	def start_game(self):
		if self.gameover:
			self.init_game()
			self.gameover = False
			self.run_train(self.weights)
	
	def run(self):
		self.gameover = False
		self.paused = False

		key_actions = {
			'ESCAPE':	self.quit,
			'LEFT':		lambda:self.move(-1),
			'RIGHT':	lambda:self.move(+1),
			'DOWN':		lambda:self.drop(True),
			'UP':		self.rotate_stone,
			'p':		self.toggle_pause,
			'RETURN':	self.start_game,
			'SPACE':	self.insta_drop
		}
		
		dont_burn_my_cpu = pygame.time.Clock()

	# def disp_msg(self, msg, topleft):
	# 	x,y = topleft
	# 	for line in msg.splitlines():
	# 		self.screen.blit(
	# 			self.default_font.render(
	# 				line,
	# 				False,
	# 				(255,255,255),
	# 				(0,0,0)),
	# 			(x,y))
	# 		y+=14

		while 1:
			self.screen.fill((0,0,0))
			if self.gameover:
				self.center_msg("""Game Over!\nYour score: %d\
								Press enter to continue""" % self.score)
			else:
				if self.paused:
					self.center_msg("Paused")
				else:
					pygame.draw.line(self.screen,
						(255,255,255),
						(self.rlim+1, 0),
						(self.rlim+1, self.height-1))
					self.disp_msg("Next:", (self.rlim+cell_size, 2))
					self.disp_msg("Score: %d\n\nLevel: %d\
								\nLines: %d" % (self.score, self.level, self.lines),
								(self.rlim+cell_size, cell_size*5))
					self.draw_matrix(self.bground_grid, (0,0))
					self.draw_matrix(self.board, (0,0))
					self.draw_matrix(self.stone, (self.stone_x, self.stone_y))
					self.draw_matrix(self.next_stone, (cols+1,2))

			pygame.display.update()
			
			for event in pygame.event.get():
				if event.type == pygame.USEREVENT+1:
					self.drop(False)
				elif event.type == pygame.QUIT:
					self.quit()
				elif event.type == pygame.KEYDOWN:
					for key in key_actions:
						if event.key == eval("pygame.K_"+key):
							key_actions[key]()
					
			dont_burn_my_cpu.tick(maxfps)

	def run_train(self, weights):
		train_actions = {
            Moves.LEFT:  lambda:self.move(-1),
            Moves.RIGHT: lambda:self.move(1),
            Moves.DROP:  self.insta_drop,
            Moves.ROT:   self.rotate_stone
        }
		self.weights = weights
		self.init_game()
		pygame.time.set_timer(pygame.USEREVENT+1, 100)
		self.gameover = False
		self.paused = False
		train = Train(weights)
		dont_burn_my_cpu = pygame.time.Clock()

		while True:
			if self.training:
				if self.gameover:
					return self.score
				else:
					train.set_board(self.board, self.stone)
					next_moves = train.get_best_move()
					for move in next_moves:
						train_actions[move]()
						dont_burn_my_cpu.tick(maxfps)
			else:
				self.screen.fill((0,0,0))
				if self.gameover:
					self.center_msg("""Game Over!\nYour score: %d\
									Press space to continue""" % self.score)
				else:
					if self.paused:
						self.center_msg("Paused")
					else:
						pygame.draw.line(self.screen, (255,255,255),
										(self.rlim+1, 0), (self.rlim+1, self.height-1))
						self.disp_msg("Generation: 10", (self.rlim+cell_size, 2))
						self.disp_msg("Next:", (self.rlim+cell_size, 20))
						self.disp_msg("Score: %d\n\nLevel: %d\nLines: %d" % (self.score, self.level, self.lines),
									(self.rlim+cell_size, cell_size*5))
						self.draw_matrix(self.bground_grid, (0,0))
						self.draw_matrix(self.board, (0,0))
						self.draw_matrix(self.stone, (self.stone_x, self.stone_y))
						self.draw_matrix(self.next_stone, (cols+1,2))
				pygame.display.update()

				for event in pygame.event.get():
					if event.type == pygame.USEREVENT+1:
						train.set_board(self.board, self.stone)
						next_moves = train.get_best_move()
						for move in next_moves:
							train_actions[move]()
					elif event.type == pygame.QUIT:
						self.quit()
					elif event.type == pygame.KEYDOWN:
						if event.key == eval("pygame.K_SPACE"):
							self.start_game()
						elif event.key == eval("pygame.K_ESCAPE"):
							self.quit()

				dont_burn_my_cpu.tick(maxfps)

#------------------------------------------------------------------------
# This sections contains the following mechanics:
# 1. Memory
#	a. Hold variables of heuristic interest
# 2. Train
#	a. Determines best moves according to given weights
#	b. Enumerate all possible move combinations, then score them
#		- Returns ([list of move combinations], [list of Memory states])
#		- Go through with original orientation 
# 		- Translate normal orientation, then iterate left + right translations
#		- Iterate through possible rotations
#		- Translate rotated orientations, then iterate through left + right orientations
#	c. Go through with movement if translate is successful
#	d. Go through with tetromino rotations if rotation was successful
#	e. Insta drop
#	f. Soft drop
#------------------------------------------------------------------------
class Memory:
    def __init__(self, board, stone, stone_x, stone_y):
        self.board = board
        self.stone = stone
        self.stone_x = stone_x
        self.stone_y = stone_y

    @staticmethod
    def clone(data):
        board_copy = list()
        for row in data.board:
            board_copy.append(row[:])
        return Memory(board_copy, data.stone[:], data.stone_x, data.stone_y)

class Train:
    def __init__(self, weights):
        self.weights = weights

    def set_board(self, board, stone):
        self.num_rows = len(board) - 1
        self.num_cols = len(board[0])
        self.begin_state = Memory(board, stone, int(self.num_cols / 2 - len(stone[0])/2), 0)

#------------------------------------------------------------------------------------------
# The score for each move is computed by assessing the grid the move would result in. 
# This assessment is based on four heuristics: 
# 	- aggregate height, complete lines, holes, and bumpiness
# 	- AI will try to either minimize or maximize each of these factors
#------------------------------------------------------------------------------------------
    def get_best_move(self):
        (moves, states) = self.enumerate(self.begin_state)
        scores = list()
        for state in states:
            score =   self.weights[0] * self.aggregate_height(state) \
					+ self.weights[1] * self.complete_lines(state) \
					+ self.weights[2] * self.holes(state) \
					+ self.weights[3] * self.slope(state)
            scores.append(score)
        return moves[scores.index(max(scores))]

    def enumerate(self, begin_state):
        moves = list()
        states = list()

        num_left = 0
        num_right = 0
        num_rot = 0

        temp = Memory.clone(begin_state)
        moves.append([Moves.DROP])
        self.insta_drop(temp)
        states.append(temp)

        temp = Memory.clone(begin_state)
        while self.move(temp, -1):
            num_left += 1
            moves.append([Moves.LEFT] * num_left + [Moves.DROP])
            drop_temp = Memory.clone(temp)
            self.insta_drop(drop_temp)
            states.append(drop_temp)

        temp = Memory.clone(begin_state)
        while self.move(temp, 1):
            num_right += 1
            moves.append([Moves.RIGHT] * num_right + [Moves.DROP])
            drop_temp = Memory.clone(temp)
            self.insta_drop(drop_temp)
            states.append(drop_temp)

        temp = Memory.clone(begin_state)
        while self.rotate_stone(temp):
            num_rot += 1
            if num_rot > 3:
                break
            rot_temp = Memory.clone(temp)
            moves.append([Moves.ROT] * num_rot + [Moves.DROP])
            self.insta_drop(rot_temp)
            states.append(rot_temp)

            num_left = 0
            num_right = 0

            rot_temp = Memory.clone(temp)
            while self.move(rot_temp, -1):
                num_left += 1
                moves.append([Moves.ROT] * num_rot + [Moves.LEFT] * num_left + [Moves.DROP])
                drop_temp = Memory.clone(rot_temp)
                self.insta_drop(drop_temp)
                states.append(drop_temp)

            rot_temp = Memory.clone(temp)
            while self.move(rot_temp, 1):
                num_right += 1
                moves.append([Moves.ROT] * num_rot + [Moves.RIGHT] * num_right + [Moves.DROP])
                drop_temp = Memory.clone(rot_temp)
                self.insta_drop(drop_temp)
                states.append(drop_temp)

        return (moves, states)

    def move(self, data, delta_x):
        new_x = data.stone_x + delta_x
        if new_x < 0 or new_x > self.num_cols - len(data.stone[0]):
            return False
        if not check_collision(data.board, data.stone, (new_x, data.stone_y)):
            data.stone_x = new_x
            return True
        return False

    def rotate_stone(self, data):
        new_stone = rotate_clockwise(data.stone)
        if not check_collision(data.board, new_stone, (data.stone_x, data.stone_y)):
            data.stone = new_stone
            return True
        return False

    def insta_drop(self, data):
        while not self.drop(data):
            pass

    def drop(self, data):
        data.stone_y += 1
        if check_collision(data.board, data.stone, (data.stone_x, data.stone_y)):
            data.board = join_matrices(data.board, data.stone, (data.stone_x, data.stone_y))
            return True
        return False

#------------------------------------------------------------------------
# These methods calculate the following heuristic variables
# 	- aggregate height, complete lines, holes, and slope
#------------------------------------------------------------------------
    def heights(self, data):
        heights = list()
        for col in range(self.num_cols):
            count = 0
            for row in range(self.num_rows):
                if data.board[row][col] == 0:
                    count += 1
                else:
                    break
            heights.append(self.num_rows - count)
        return heights

    def aggregate_height(self, data):
        return sum(self.heights(data))

    def complete_lines(self, data):
        count = 0
        for line in data.board[:-1]:
            if 0 not in line:
                count += 1
        return count

    def holes(self, data):
        holes = 0
        for col in range(self.num_cols):
            empty = 0
            for row in range(self.num_rows - 1, -1, -1):
                if data.board[row][col] == 0:
                    empty += 1
                else:
                    holes += empty
                    empty = 0
        return holes

    def slope(self, data):
        board_heights = self.heights(data)
        slope = 0
        for i in range(self.num_cols - 1):
            slope += abs(board_heights[i] - board_heights[i + 1])
        return slope

#------------------------------------------------------------------------
# This sections does the following:
# 1. Run the actual game
# 2. Grab weights from Evolutionary Algorithm
#------------------------------------------------------------------------
if __name__ == '__main__':
	App = TetrisApp()
	# App.run()
	file = open("best_weights50.txt", "r")
	weights = ast.literal_eval(file.readline())
	for i, data in enumerate(weights):
		weights[i] = float(data) 
	App.run_train(weights)