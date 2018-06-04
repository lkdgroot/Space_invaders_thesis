# Space Invaders
# Created by Lee Robinson

#!/usr/bin/env python
from pygame import *
import sys
from random import shuffle, randrange, choice, random
import decimal
import itertools

import os.path
import numpy
import collections
import pickle
import glob
import uuid
from pathlib import Path
import datetime

from sklearn.preprocessing import PolynomialFeatures

from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from sklearn.externals import joblib
import smtplib
import dqnRB

import operator

#           R    G    B
WHITE 	= (255, 255, 255)
GREEN 	= (78, 255, 87)
YELLOW 	= (241, 255, 0)
BLUE 	= (80, 255, 239)
PURPLE 	= (203, 0, 255)
RED 	= (237, 28, 36)

SCREEN 		= display.set_mode((1280,720))
FONT = "fonts/space_invaders.ttf"
IMG_NAMES 	= ["ship", "ship", "mystery", "enemy1_1", "enemy1_2", "enemy2_1", "enemy2_2",
				"enemy3_1", "enemy3_2", "explosionblue", "explosiongreen", "explosionpurple", "laser", "enemylaser", "moods"]
IMAGES 		= {name: image.load("images/{}.png".format(name)).convert_alpha()
				for name in IMG_NAMES}
				
FRAME_RL = 5

var1 = [i for i in range(75, 251, 50)] #startDistance
var2 = [i for i in range(200, 801, 100)] #enemySpeed
var3 = [i for i in range(200, 801, 100)] #bulletSpeed
var4 = [i for i in range(8, 21, 3)] #columnAmount
var5 = [i for i in numpy.arange(0,0.51,0.10)] #stage2 Cutoff
var6 = [i for i in range(0,6,1)]
#dqnnetwork = dqnRB.DQN(7)

#poly = PolynomialFeatures(degree=2)
#scaler = joblib.load('scalerNNespeed00006d98.pkl')


timeposs = numpy.array([0, 15000,30000,45000,60000,75000,90000, 105000, 120000, 135000, 150000], dtype=float)
but = numpy.array([0, 1000,2000, 3000,4000, 5000,6000, 7000,8000,9000,10000], dtype=float)
Acc_win = numpy.array([0.0, 0.1, 0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0], dtype=float)
mystery_arr = numpy.array([0,1,2,3,4,5], dtype=float)
distdone = numpy.array([200,250,300,350,400,450,500,550,600], dtype=float)

game = None

def startGame(invaders):
	global game
	game = invaders
	return game.main()
	
class Ship(sprite.Sprite):
	def __init__(self):
		sprite.Sprite.__init__(self)
		self.image = IMAGES["ship"]
		self.rect = self.image.get_rect(topleft=(600, 660))
		self.speed = 5

	def update(self, keys, *args):
		if keys[K_LEFT] and self.rect.x > 10:
			self.rect.x -= self.speed
		if keys[K_RIGHT] and self.rect.x < 1200:
			self.rect.x += self.speed
		game.screen.blit(self.image, self.rect)


		
class Bullet(sprite.Sprite):
	def __init__(self, xpos, ypos, direction, speed, filename, side):
		sprite.Sprite.__init__(self)
		self.image = IMAGES[filename]
		self.rect = self.image.get_rect(topleft=(xpos, ypos))
		self.speed = speed
		self.direction = direction
		self.side = side
		self.filename = filename

	def update(self, keys, *args):
		game.screen.blit(self.image, self.rect)
		self.rect.y += self.speed * self.direction
		if self.rect.y < 15 or self.rect.y > 720:
			self.kill()


class Enemy(sprite.Sprite):
	def __init__(self, row, column, speed, columnAmount):
		sprite.Sprite.__init__(self)
		self.row = row
		self.column = column
		self.images = []
		self.load_images()
		self.index = 0
		self.image = self.images[self.index]
		self.rect = self.image.get_rect()
		self.direction = 1
		self.rightMoves = 15
		self.leftMoves = 30
		self.moveNumber = 0
		## Speed!!!
		self.startSpeed = speed
		self.moveTime = speed
		self.firstTime = True
		self.movedY = False;
		## Changing amount of enemies
		self.columnAmount = columnAmount
		
		self.columns = [False] * self.columnAmount
		self.aliveColumns = [True] * self.columnAmount
		self.addRightMoves = False
		self.addLeftMoves = False
		self.numOfRightMoves = 0
		self.numOfLeftMoves = 0
		self.timer = time.get_ticks()
		
		self.distanceAdded = 0
		
	def update(self, keys, currentTime, killedRow, killedColumn, killedArray):
		self.check_column_deletion(killedRow, killedColumn, killedArray)
		if currentTime - self.timer > self.moveTime:
			self.movedY = False;
			if self.moveNumber >= self.rightMoves and self.direction == 1:
				self.direction *= -1
				self.moveNumber = 0
				self.rect.y += 35
				self.distanceAdded += 35
				self.movedY = True
				if self.addRightMoves:
					self.rightMoves += self.numOfRightMoves
				if self.firstTime:
					self.rightMoves = self.leftMoves;
					self.firstTime = False;
				self.addRightMovesAfterDrop = False
			if self.moveNumber >= self.leftMoves and self.direction == -1:
				self.direction *= -1
				self.moveNumber = 0
				self.rect.y += 35
				self.distanceAdded += 35
				self.movedY = True
				if self.addLeftMoves:
					self.leftMoves += self.numOfLeftMoves
				self.addLeftMovesAfterDrop = False
			if self.moveNumber < self.rightMoves and self.direction == 1 and not self.movedY:
				self.rect.x += 10
				self.moveNumber += 1
			if self.moveNumber < self.leftMoves and self.direction == -1 and not self.movedY:
				self.rect.x -= 10
				self.moveNumber += 1

			self.index += 1
			if self.index >= len(self.images):
				self.index = 0
			self.image = self.images[self.index]

			self.timer += self.moveTime
		game.screen.blit(self.image, self.rect)

	def check_column_deletion(self, killedRow, killedColumn, killedArray):
		if killedRow != -1 and killedColumn != -1:
			killedArray[killedRow][killedColumn] = 1
			## Changing amount of enemies
			for column in range(self.columnAmount):
				if all([killedArray[row][column] == 1 for row in range(5)]):
					self.columns[column] = True

		for i in range(int(numpy.floor(self.columnAmount/2))):
			if all([self.columns[x] for x in range(i+1)]) and self.aliveColumns[i]:
				self.leftMoves += 5
				self.aliveColumns[i] = False
				if self.direction == -1:
					self.rightMoves += 5
				else:
					self.addRightMoves = True
					self.numOfRightMoves += 5
					
		for i in range(int(numpy.floor(self.columnAmount/2))):
			if all([self.columns[x] for x in range(self.columnAmount - 1, self.columnAmount - 2 - i, -1)]) and self.aliveColumns[self.columnAmount - 1 - i]:
				self.aliveColumns[self.columnAmount - 1 - i] = False
				self.rightMoves += 5
				if self.direction == 1:
					self.leftMoves += 5
				else:
					self.addLeftMoves = True
					self.numOfLeftMoves += 5

	def load_images(self):
		images = {0: ["1_2", "1_1"],
				  1: ["2_2", "2_1"],
				  2: ["2_2", "2_1"],
				  3: ["3_1", "3_2"],
				  4: ["3_1", "3_2"],
				 }
		img1, img2 = (IMAGES["enemy{}".format(img_num)] for img_num in images[self.row])
		self.images.append(transform.scale(img1, (40, 35)))
		self.images.append(transform.scale(img2, (40, 35)))


class Blocker(sprite.Sprite):
	def __init__(self, size, color, row, column):
	   sprite.Sprite.__init__(self)
	   self.height = size
	   self.width = size
	   self.color = color
	   self.image = Surface((self.width, self.height))
	   self.image.fill(self.color)
	   self.rect = self.image.get_rect()
	   self.row = row
	   self.column = column

	def update(self, keys, *args):
		game.screen.blit(self.image, self.rect)


class Mystery(sprite.Sprite):
	def __init__(self):
		sprite.Sprite.__init__(self)
		self.image = IMAGES["mystery"]
		self.image = transform.scale(self.image, (75, 35))
		self.rect = self.image.get_rect(topleft=(-80, 45))
		self.row = 5
		self.moveTime = 10000
		self.direction = 1
		self.timer = time.get_ticks()
		self.mysteryEntered = mixer.Sound('sounds/mysteryentered.wav')
		self.mysteryEntered.set_volume(0.3)
		self.playSound = True

	def update(self, keys, currentTime, *args):
		resetTimer = False
		if (currentTime - self.timer > self.moveTime) and (self.rect.x < 0 or self.rect.x > 1280) and self.playSound:
			self.mysteryEntered.play()
			self.playSound = False
		if (currentTime - self.timer > self.moveTime) and self.rect.x < 1310 and self.direction == 1:
			self.mysteryEntered.fadeout(4000)
			self.rect.x += 2
			game.screen.blit(self.image, self.rect)
		if (currentTime - self.timer > self.moveTime) and self.rect.x > -100 and self.direction == -1:
			self.mysteryEntered.fadeout(4000)
			self.rect.x -= 2
			game.screen.blit(self.image, self.rect)
		if (self.rect.x > 1310):
			self.playSound = True
			self.direction = -1
			resetTimer = True
		if (self.rect.x < -90):
			self.playSound = True
			self.direction = 1
			resetTimer = True
		if (currentTime - self.timer > self.moveTime) and resetTimer:
			self.timer = currentTime

	
class Explosion(sprite.Sprite):
	def __init__(self, xpos, ypos, row, ship, mystery, score):
		sprite.Sprite.__init__(self)
		self.isMystery = mystery
		self.isShip = ship
		if mystery:
			self.text = Text(FONT, 20, str(score), WHITE, xpos+20, ypos+6)
		elif ship:
			self.image = IMAGES["ship"]
			self.rect = self.image.get_rect(topleft=(xpos, ypos))
		else:
			self.row = row
			self.load_image()
			self.image = transform.scale(self.image, (40, 35))
			self.rect = self.image.get_rect(topleft=(xpos, ypos))
			game.screen.blit(self.image, self.rect)
			
		self.timer = time.get_ticks()
		
	def update(self, keys, currentTime):
		if self.isMystery:
			if currentTime - self.timer <= 200:
				self.text.draw(game.screen)
			if currentTime - self.timer > 400 and currentTime - self.timer <= 600:
				self.text.draw(game.screen)
			if currentTime - self.timer > 600:
				self.kill()
		elif self.isShip:
			if currentTime - self.timer > 300 and currentTime - self.timer <= 600:
				game.screen.blit(self.image, self.rect)
			if currentTime - self.timer > 900:
				self.kill()
		else:
			if currentTime - self.timer <= 100:
				game.screen.blit(self.image, self.rect)
			if currentTime - self.timer > 100 and currentTime - self.timer <= 200:
				self.image = transform.scale(self.image, (50, 45))
				game.screen.blit(self.image, (self.rect.x-6, self.rect.y-6))
			if currentTime - self.timer > 400:
				self.kill()
	
	def load_image(self):
		imgColors = ["purple", "blue", "blue", "green", "green"]
		self.image = IMAGES["explosion{}".format(imgColors[self.row])]

			
class Life(sprite.Sprite):
	def __init__(self, xpos, ypos):
		sprite.Sprite.__init__(self)
		self.image = IMAGES["ship"]
		self.image = transform.scale(self.image, (23, 23))
		self.rect = self.image.get_rect(topleft=(xpos, ypos))
		
	def update(self, keys, *args):
		game.screen.blit(self.image, self.rect)


class Text(object):
	def __init__(self, textFont, size, message, color, xpos, ypos):
		self.font = font.Font(textFont, size)
		self.surface = self.font.render(message, True, color)
		self.rect = self.surface.get_rect(topleft=(xpos, ypos))

	def draw(self, surface):
		surface.blit(self.surface, self.rect)


class SpaceInvaders(object):
	def __init__(self, enemyStart, enemySpeed, bulletSpeed, columnAmount,speedUpPerc,lives, artificial):
		mixer.pre_init(44100, -16, 1, 512)
		init()
		self.caption = display.set_caption('Space Invaders')
		self.screen = SCREEN
		self.background = image.load('images/background.jpg').convert()
		self.background = transform.scale(self.background, (1280,720))
		self.startGame = False
		self.mainScreen = True
		self.gameOver = False
		self.moodScreen = False
		# Initial value for a new game
		## Starting value position
		self.enemyPositionDefault = enemyStart
		# Counter for enemy starting position (increased each new round)
		self.enemyPositionStart = self.enemyPositionDefault
		# Current enemy starting position
		self.enemyPosition = self.enemyPositionStart
		self.livesStart = lives
		self.lives = lives		
		self.logPlayer = []
		
		self.won = 0
		self.timeSpent = 0
		
		self.enemySpeed = enemySpeed
		self.bulletSpeed = bulletSpeed
		self.columnAmount = columnAmount
		self.pressed = 0
		self.bulletShot = 0
		self.bulletHit = 0
		
		self.pressed_when = []
		self.pressed_last = 0
		
		self.RageQuit = False
		
		#to implement
		#gamestate
		self.speedUp = speedUpPerc #
		
		#playerState
		self.mysteryHit = 0  #
		self.reachStage2 = False #
		self.reachDoubleBullet = False #
		self.timeDoubleBullet = 0 #
		
		self.shotStage2 = 0
		self.shotdouble = 0
		self.hitStage2 = 0
		self.hitdouble = 0

		self.instakill = False
		self.enemyBulletHit = 0		
		self.enemyHit = 0
		self.blockerHit = 0
		
		self.mainQuit = False
		
		self.artificial = artificial

	def reset(self, score, lives, newGame=False):
		self.player = Ship()
		self.playerGroup = sprite.Group(self.player)
		self.explosionsGroup = sprite.Group()
		self.bullets = sprite.Group()
		self.mysteryShip = Mystery()
		self.mysteryGroup = sprite.Group(self.mysteryShip)
		self.enemyBullets = sprite.Group()
		self.reset_lives(lives)
		self.enemyPosition = self.enemyPositionStart
		self.make_enemies()
		# Only create blockers on a new game, not a new round
		if newGame:
			self.allBlockers = sprite.Group(self.make_blockers(0), self.make_blockers(1), self.make_blockers(2), self.make_blockers(3))
		self.keys = key.get_pressed()
		self.clock = time.Clock()
		self.timer = time.get_ticks()
		self.noteTimer = time.get_ticks()
		self.shipTimer = time.get_ticks()
		self.score = score
		self.lives = lives
		self.create_audio()
		self.create_text()
		self.killedRow = -1
		self.killedColumn = -1
		self.makeNewShip = False
		self.shipAlive = True
		## Change amount of enemies
		self.killedArray = [[0] * self.columnAmount for x in range(5)]

	def make_blockers(self, number):
		blockerGroup = sprite.Group()
		for row in range(4):
			for column in range(9):
				blocker = Blocker(10, GREEN, row, column)
				blocker.rect.x = 50 + (320 * number) + (column * blocker.width)
				blocker.rect.y = 570 + (row * blocker.height)
				blockerGroup.add(blocker)
		return blockerGroup
	
	def reset_lives_sprites(self):
		self.life1 = Life(1141, 3)
		self.life2 = Life(1168, 3)
		self.life3 = Life(1195, 3)
		self.life4 = Life(1222, 3)
		self.life5 = Life(1249, 3)
		
		if self.lives == 5:
			self.livesGroup = sprite.Group(self.life1, self.life2, self.life3, self.life4, self.life5)		
		elif self.lives == 4:
			self.livesGroup = sprite.Group(self.life1, self.life2, self.life3, self.life4)			
		elif self.lives == 3:
			self.livesGroup = sprite.Group(self.life1, self.life2, self.life3)
		elif self.lives == 2:
			self.livesGroup = sprite.Group(self.life1, self.life2)
		elif self.lives == 1:
			self.livesGroup = sprite.Group(self.life1)
		elif self.lives == 0:
			self.livesGroup = sprite.Group()
	
	def reset_lives(self, lives):
		self.lives = lives
		self.reset_lives_sprites()
	
	def create_audio(self):
		self.sounds = {}
		for sound_name in ["shoot", "shoot2", "invaderkilled", "mysterykilled", "shipexplosion"]:
			self.sounds[sound_name] = mixer.Sound("sounds/{}.wav".format(sound_name))
			self.sounds[sound_name].set_volume(0.2)

		self.musicNotes = [mixer.Sound("sounds/{}.wav".format(i)) for i in range(4)]
		for sound in self.musicNotes:
			sound.set_volume(0.5)

		self.noteIndex = 0

	def play_main_music(self, currentTime):
		moveTime = self.enemies.sprites()[0].moveTime
		if currentTime - self.noteTimer > moveTime:
			self.note = self.musicNotes[self.noteIndex]
			if self.noteIndex < 3:
				self.noteIndex += 1
			else:
				self.noteIndex = 0

			self.note.play()
			self.noteTimer += moveTime

	def create_text(self):
		self.titleText = Text(FONT, 50, "Space Invaders", WHITE, 164, 155)
		self.titleText2 = Text(FONT, 25, "Press any key to continue", WHITE, 201, 225)
		self.gameOverText = Text(FONT, 50, "Game Over", WHITE, 250, 270)
		self.nextRoundText = Text(FONT, 50, "Well played", WHITE, 240, 270)
		self.enemy1Text = Text(FONT, 25, "   =   10 pts", GREEN, 368, 270)
		self.enemy2Text = Text(FONT, 25, "   =  20 pts", BLUE, 368, 320)
		self.enemy3Text = Text(FONT, 25, "   =  30 pts", PURPLE, 368, 370)
		self.enemy4Text = Text(FONT, 25, "   =  ?????", RED, 368, 420)
		self.scoreText = Text(FONT, 20, "Score", WHITE, 5, 5)
		self.livesText = Text(FONT, 20, "Lives ", WHITE, 1066, 5)
		
		self.mainText = Text(FONT, 25, "Press ESC to quit", WHITE, 201, 500)
		
		self.liketext = Text(FONT, 50, "Was this level", WHITE, 400, 270)
		self.liketext1 = Text(FONT, 50, "too Easy, press E", GREEN, 400, 370)
		self.liketext2 = Text(FONT, 50, "OK, press O", YELLOW, 400, 420)
		self.liketext3 = Text(FONT, 50, "too Hard, press H", RED, 400, 470)
		self.continueText = Text(FONT, 50, "Do you wish to continue?", WHITE, 10, 270)
		self.continueText2 = Text(FONT, 50, "If Yes, press Y", GREEN, 10, 330)
		self.continueText3 = Text(FONT, 50, "If No, press N", RED, 10, 390)
		self.continueText4 = Text(FONT, 50, "If no, wait a while for files to upload.", WHITE, 10, 450)
		
		self.saveText = Text(FONT, 50, "Uploading. Please wait...", WHITE, 10, 270)
		
		self.moodText1 = Text(FONT, 40, "What was your mood during this level?", WHITE, 160, 10)
		self.moodText2 = Text(FONT, 40, "Press the correct number on your keyboard", WHITE, 80, 670)


		
	def check_input(self):
		#self.keys = key.get_pressed()
		for e in event.get():
			if e.type == QUIT:
				if self.startGame and len(self.enemies) > 0:
					self.timeSpent = time.get_ticks() - self.startTime
					self.likeScreen = True
					self.startGame = False
					self.RageQuit = True
			if e.type == KEYDOWN:
				if e.key == K_SPACE:
					self.pressed += 1
					gameTimeCurr = time.get_ticks() - self.startTime
					self.logPlayer.append("Button: Space  Time: " + str(gameTimeCurr))
					self.pressed_last = time.get_ticks()
					if len(self.bullets) == 0 and self.shipAlive:
						if self.score < 1000:
							self.bulletShot += 1
							if self.reachStage2:
								self.shotStage2 += 1
							bullet = Bullet(self.player.rect.x+23, self.player.rect.y+5, -1, 15, "laser", "center")
							self.logPlayer.append("Bullet made  X: " + str(self.player.rect.x + 23) + " Y: " + str(self.player.rect.x + 5))
							self.bullets.add(bullet)
							self.allSprites.add(self.bullets)
							self.sounds["shoot"].play()
						else:
							self.bulletShot = self.bulletShot + 2
							self.shotdouble += 2
							if self.reachStage2:
								self.shotStage2 += 2
							leftbullet = Bullet(self.player.rect.x+8, self.player.rect.y+5, -1, 15, "laser", "left")
							rightbullet = Bullet(self.player.rect.x+38, self.player.rect.y+5, -1, 15, "laser", "right")
							self.logPlayer.append("Bullet made  X: " + str(self.player.rect.x + 8) + " Y: " + str(self.player.rect.x + 5))
							self.logPlayer.append("Bullet made  X: " + str(self.player.rect.x + 38) + " Y: " + str(self.player.rect.x + 5))
							self.bullets.add(leftbullet)
							self.bullets.add(rightbullet)
							self.allSprites.add(self.bullets)
							self.sounds["shoot2"].play()
				elif e.key == K_LEFT:
					self.pressed += 1
					gameTimeCurr = time.get_ticks() - self.startTime
					self.logPlayer.append("Button: Left  Time: " + str(gameTimeCurr) + " X: " + str(self.player.rect.x))
				elif e.key == K_RIGHT:
					self.pressed += 1
					gameTimeCurr = time.get_ticks() - self.startTime
					self.logPlayer.append("Button: Right  Time: " + str(gameTimeCurr)  + " X: " + str(self.player.rect.x))
			if e.type == KEYUP:
				if self.keys[K_ESCAPE]:
					if self.startGame and len(self.enemies) > 0:
						self.timeSpent = time.get_ticks() - self.startTime
						self.likeScreen = True
						self.startGame = False
						self.RageQuit = True				
				elif e.key == K_LEFT:
					gameTimeCurr = time.get_ticks() - self.startTime
					self.logPlayer.append("Button release: Left  Time: " + str(gameTimeCurr) + " X: " + str(self.player.rect.x))
				elif e.key == K_RIGHT:
					gameTimeCurr = time.get_ticks() - self.startTime
					self.logPlayer.append("Button release: Right  Time: " + str(gameTimeCurr) + " X: " + str(self.player.rect.x))
				

	def make_enemies(self):
		enemies = sprite.Group()
		for row in range(5):
			## Changing amount of enemies
			for column in range(self.columnAmount):
				enemy = Enemy(row, column, self.enemySpeed, self.columnAmount)
				enemy.rect.x = 157 + (column * 50)
				enemy.rect.y = self.enemyPosition + (row * 45)
				enemies.add(enemy)
		
		self.enemies = enemies
		self.allSprites = sprite.Group(self.player, self.enemies, self.livesGroup, self.mysteryShip)

	def make_enemies_shoot(self, bulletSpeed):
		columnList = []
		for enemy in self.enemies:
			columnList.append(enemy.column)

		columnSet = set(columnList)
		columnList = list(columnSet)
		shuffle(columnList)
		column = columnList[0]
		enemyList = []
		rowList = []

		for enemy in self.enemies:
			if enemy.column == column:
				rowList.append(enemy.row)
		row = max(rowList)
		for enemy in self.enemies:
			if enemy.column == column and enemy.row == row:
				## Bullet speed
				if (time.get_ticks() - self.timer) > bulletSpeed:
					self.enemyBullets.add(Bullet(enemy.rect.x + 14, enemy.rect.y + 20, 1, 5, "enemylaser", "center"))
					self.allSprites.add(self.enemyBullets)
					self.timer = time.get_ticks() 
					logTime = time.get_ticks() - self.startTime
					self.logPlayer.append("Enemy bullet made  Time: " + str(logTime) + " X: " + str(enemy.rect.x) + " Y: " + str(enemy.rect.y) + " Row: " + str(row) + " Column: " + str(column))

	def calculate_score(self, row):
		scores = {0: 30,
				  1: 20,
				  2: 20,
				  3: 10,
				  4: 10,
				  5: choice([50, 100, 150, 300])
				 }
					  
		score = scores[row]
		self.score += score
		if(self.score >= 1000 and not self.reachDoubleBullet):
			self.reachDoubleBullet = True
			self.timeDoubleBullet = time.get_ticks() - self.startTime
		return score

	def create_main_menu(self,keys):
		self.enemy1 = IMAGES["enemy3_1"]
		self.enemy1 = transform.scale(self.enemy1 , (40, 40))
		self.enemy2 = IMAGES["enemy2_2"]
		self.enemy2 = transform.scale(self.enemy2 , (40, 40))
		self.enemy3 = IMAGES["enemy1_2"]
		self.enemy3 = transform.scale(self.enemy3 , (40, 40))
		self.enemy4 = IMAGES["mystery"]
		self.enemy4 = transform.scale(self.enemy4 , (80, 40))
		self.screen.blit(self.enemy1, (318, 270))
		self.screen.blit(self.enemy2, (318, 320))
		self.screen.blit(self.enemy3, (318, 370))
		self.screen.blit(self.enemy4, (299, 420))

		self.keys = key.get_pressed()

		for e in event.get():
			if e.type == QUIT:
				self.mainQuit = True
				self.mainScreen = False
				self.saveScreen = True
			if e.type == KEYDOWN:
				if e.key == K_ESCAPE:
					self.mainQuit = True
					self.mainScreen = False
					self.likeScreen = False
					self.moodScreen = False
					self.startGame = False
					self.saveScreen = True
				else:
					self.startGame = True
					self.mainScreen = False
					self.startTime = time.get_ticks()
					self.pressed_last = time.get_ticks()
	
	def update_enemy_speed(self):
		if (len(self.enemies) <= int((self.columnAmount * 5) * self.speedUp)) and not self.reachStage2:
			newSpeed = int(self.enemySpeed / 2)
			for enemy in self.enemies:
				enemy.moveTime = newSpeed
			self.reachStage2 = True
			
		#if len(self.enemies) == 1:
		#	for enemy in self.enemies:
		#		enemy.moveTime = 200
	
	def count_hit(self):
		self.bulletHit += 1
		if self.reachDoubleBullet:
			self.hitdouble += 1
		if self.reachStage2:
			self.hitStage2 += 1
	
	def check_collisions(self):
		collidedict = sprite.groupcollide(self.bullets, self.enemyBullets, True, False)
		if collidedict:
			for value in collidedict.values():
				for currentSprite in value:
					self.enemyBullets.remove(currentSprite)
					self.allSprites.remove(currentSprite)
					self.count_hit()
					collTimer = time.get_ticks() - self.startTime
					self.enemyBulletHit +=1
					self.logPlayer.append("Bullet collision  Time: " + str(collTimer) + " X: " + str(currentSprite.rect.x) + " Y: " + str(currentSprite.rect.y))

		enemiesdict = sprite.groupcollide(self.bullets, self.enemies, True, False)
		if enemiesdict:
			for value in enemiesdict.values():
				for currentSprite in value:
					self.sounds["invaderkilled"].play()
					self.killedRow = currentSprite.row
					self.killedColumn = currentSprite.column
					score = self.calculate_score(currentSprite.row)
					explosion = Explosion(currentSprite.rect.x, currentSprite.rect.y, currentSprite.row, False, False, score)
					self.explosionsGroup.add(explosion)
					self.allSprites.remove(currentSprite)
					self.enemies.remove(currentSprite)
					self.gameTimer = time.get_ticks()
					self.count_hit()
					collTimer = time.get_ticks() - self.startTime
					self.enemyHit +=1
					self.logPlayer.append("Enemy hit collision  Time: " + str(collTimer) + " Row: " + str(self.killedRow) + " Column: " + str(self.killedColumn) + " X: " + str(currentSprite.rect.x) + " Y: " + str(currentSprite.rect.y))					
					break
		
		mysterydict = sprite.groupcollide(self.bullets, self.mysteryGroup, True, True)
		if mysterydict:
			for value in mysterydict.values():
				for currentSprite in value:
					currentSprite.mysteryEntered.stop()
					self.sounds["mysterykilled"].play()
					score = self.calculate_score(currentSprite.row)
					explosion = Explosion(currentSprite.rect.x, currentSprite.rect.y, currentSprite.row, False, True, score)
					self.explosionsGroup.add(explosion)
					self.allSprites.remove(currentSprite)
					self.mysteryGroup.remove(currentSprite)
					newShip = Mystery()
					self.allSprites.add(newShip)
					self.mysteryGroup.add(newShip)
					self.count_hit()
					self.mysteryHit += 1
					collTimer = time.get_ticks() - self.startTime
					self.logPlayer.append("Mystery hit collision  Time: " + str(collTimer) + " X: " + str(currentSprite.rect.x))
					break

		bulletsdict = sprite.groupcollide(self.enemyBullets, self.playerGroup, True, False)     
		if bulletsdict:
			for value in bulletsdict.values():
				for playerShip in value:
					if self.lives == 5:
						self.lives -= 1
						self.livesGroup.remove(self.life5)
						self.allSprites.remove(self.life5)
					elif self.lives == 4:
						self.lives -= 1
						self.livesGroup.remove(self.life4)
						self.allSprites.remove(self.life4)
					elif self.lives == 3:
						self.lives -= 1
						self.livesGroup.remove(self.life3)
						self.allSprites.remove(self.life3)
					elif self.lives == 2:
						self.lives -= 1
						self.livesGroup.remove(self.life2)
						self.allSprites.remove(self.life2)
					elif self.lives == 1:
						self.lives -= 1
						self.livesGroup.remove(self.life1)
						self.allSprites.remove(self.life1)
					elif self.lives == 0:
						self.gameOver = True
						self.startGame = False
					self.sounds["shipexplosion"].play()
					explosion = Explosion(playerShip.rect.x, playerShip.rect.y, 0, True, False, 0)
					self.explosionsGroup.add(explosion)
					self.allSprites.remove(playerShip)
					self.playerGroup.remove(playerShip)
					self.makeNewShip = True
					self.shipTimer = time.get_ticks()
					self.shipAlive = False
					collTimer = time.get_ticks() - self.startTime
					self.logPlayer.append("Death  Time: " + str(collTimer) + " X: " + str(playerShip.rect.x))

		instakilldict = sprite.groupcollide(self.enemies, self.playerGroup, True, True)
		if instakilldict:
			for value in instakilldict.values():
				for currentSprite in value:
					self.gameOver = True
					self.startGame = False
					collTimer = time.get_ticks() - self.startTime
					self.logPlayer.append("Instant Death  Time: " + str(collTimer) + " X: " + str(currentSprite.rect.x))
					self.instakill = True

		selfblockdict = sprite.groupcollide(self.bullets, self.allBlockers, True, True)
		if selfblockdict:
			for value in selfblockdict.values():
				for currentSprite in value:
					self.count_hit()
					collTimer = time.get_ticks() - self.startTime
					self.logPlayer.append("Bullet hit blocker: " + str(collTimer) + " X: " + str(currentSprite.rect.x) + " Y: " + str(currentSprite.rect.y))
					self.blockerHit += 1
		enemyblockdict = sprite.groupcollide(self.enemyBullets, self.allBlockers, True, True)
		if enemyblockdict:
			for value in enemyblockdict.values():
				for currentSprite in value:	
					collTimer = time.get_ticks() - self.startTime
					self.logPlayer.append("Enemy bullet hit blocker: " + str(collTimer) + " X: " + str(currentSprite.rect.x) + " Y: " + str(currentSprite.rect.y))	
		enemybodyblockdict = sprite.groupcollide(self.enemies, self.allBlockers, False, True)
		if enemybodyblockdict:
			for value in enemybodyblockdict.values():
				for currentSprite in value:
					collTimer = time.get_ticks() - self.startTime
					self.logPlayer.append("Enemy hit blocker: " + str(collTimer) + " X: " + str(currentSprite.rect.x) + " Y: " + str(currentSprite.rect.y))	

	def create_new_ship(self, createShip, currentTime):
		if createShip and (currentTime - self.shipTimer > 900):
			self.player = Ship()
			self.allSprites.add(self.player)
			self.playerGroup.add(self.player)
			self.makeNewShip = False
			self.shipAlive = True

	def create_game_over(self, currentTime):
		self.screen.blit(self.background, (0,0))
		if currentTime - self.timer < 750:
			self.gameOverText.draw(self.screen)
		if currentTime - self.timer > 750 and currentTime - self.timer < 1500:
			self.screen.blit(self.background, (0,0))
		if currentTime - self.timer > 1500 and currentTime - self.timer < 2250:
			self.gameOverText.draw(self.screen)
		if currentTime - self.timer > 2250 and currentTime - self.timer < 2750:
			self.screen.blit(self.background, (0,0))
		if currentTime - self.timer > 3000:
			#self.mainScreen = True
			self.gameOver = False
			self.likeScreen = True
		
		#for e in event.get():
			#if e.type == QUIT:
				
	def create_like_screen(self, keys):
		while True:	
			self.screen.blit(self.background, (0,0))
			self.liketext.draw(self.screen)
			self.liketext1.draw(self.screen)
			self.liketext2.draw(self.screen)
			self.liketext3.draw(self.screen)
			display.update()
			#self.keys = key.get_pressed()
			for e in event.get():
				#if e.type == QUIT:
				if e.type == KEYUP:
					if self.keys[K_e]:
						self.likeScreen = False
						self.moodScreen = True
						return -1
					elif self.keys[K_h]:
						self.likeScreen = False
						self.moodScreen = True
						return 1
					elif self.keys[K_o]:
						self.likeScreen = False
						self.moodScreen = True
						return 0

	def create_mood_screen(self, keys):
		while True:	
			self.screen.blit(self.background, (0,0))
			self.moodImage = IMAGES["moods"]
			self.moodImage = transform.scale(self.moodImage , (640, 600))
			self.screen.blit(self.moodImage, (320,60))
			self.moodText1.draw(self.screen)
			self.moodText2.draw(self.screen)
			display.update()
			#self.keys = key.get_pressed()
			for e in event.get():
				#if e.type == QUIT:
				if e.type == KEYUP:
					if self.keys[K_1] or self.keys[K_KP1]:
						self.moodScreen = False
						if self.mainQuit or self.RageQuit:
							self.saveScreen = True
						else:
							self.end = True
						return 1
					elif self.keys[K_2] or self.keys[K_KP2]:
						self.moodScreen = False
						if self.mainQuit or self.RageQuit:
							self.saveScreen = True
						else:
							self.end = True
						return 2
					elif self.keys[K_3] or self.keys[K_KP3]:
						self.moodScreen = False
						if self.mainQuit or self.RageQuit:
							self.saveScreen = True
						else:
							self.end = True
						return 3
					elif self.keys[K_4] or self.keys[K_KP4]:
						self.moodScreen = False
						if self.mainQuit or self.RageQuit:
							self.saveScreen = True
						else:
							self.end = True
						return 4
					elif self.keys[K_5] or self.keys[K_KP5]:
						self.moodScreen = False
						if self.mainQuit or self.RageQuit:
							self.saveScreen = True
						else:
							self.end = True
						return 5
					elif self.keys[K_6] or self.keys[K_KP6]:
						self.moodScreen = False
						if self.mainQuit or self.RageQuit:
							self.saveScreen = True
						else:
							self.end = True
						return 6
					elif self.keys[K_7] or self.keys[K_KP7]:
						self.moodScreen = False
						if self.mainQuit or self.RageQuit:
							self.saveScreen = True
						else:
							self.end = True
						return 7
					elif self.keys[K_8] or self.keys[K_KP8]:
						self.moodScreen = False
						if self.mainQuit or self.RageQuit:
							self.saveScreen = True
						else:
							self.end = True
						return 8
					elif self.keys[K_9] or self.keys[K_KP9]:
						self.moodScreen = False
						if self.mainQuit or self.RageQuit:
							self.saveScreen = True
						else:
							self.end = True
						return 9

					
	def create_continue_screen(self, keys):
		while True:	
			self.screen.blit(self.background, (0,0))
			self.continueText.draw(self.screen)
			self.continueText2.draw(self.screen)
			self.continueText3.draw(self.screen)
			self.continueText4.draw(self.screen)
			display.update()
			self.keys = key.get_pressed()
			for e in event.get():
				#if e.type == QUIT:
				if e.type == KEYUP:
					if self.keys[K_y]:
						self.continueScreen = False
						self.end = True
						self.saveScreen = False
						return True
					elif self.keys[K_n]:
						self.continueScreen = False
						self.saveScreen = True
						return False

	def create_save_screen(self):
		while True:	
			self.screen.blit(self.background, (0,0))
			self.saveText.draw(self.screen)
			display.update()
			self.saveScreen = False
			self.end = True
			return 0

#############################################
#############################################			
#	SELF PLAYING AI					        #
#############################################
#############################################	

	def AIshoot(self):
		eventAI = event.Event(KEYDOWN, key = K_SPACE)
		eventAI2 = event.Event(KEYUP, key = K_SPACE)
		event.post(eventAI)
		event.post(eventAI2)

	def AIgoLeft(self):
		eventAI3 = event.Event(KEYDOWN, key= K_LEFT)
		listKeys = list(self.keys)
		listKeys[K_LEFT] = True
		self.keys = tuple(listKeys)
		event.post(eventAI3)
		
	def AIstopLeft(self):
		eventAI3 = event.Event(KEYUP, key= K_LEFT)
		listKeys = list(self.keys)
		listKeys[K_LEFT] = False
		self.keys = tuple(listKeys)
		event.post(eventAI3)	
	
	def AIgoRight(self):
		eventAI3 = event.Event(KEYDOWN, key= K_RIGHT)
		listKeys = list(self.keys)
		listKeys[K_RIGHT] = True
		self.keys = tuple(listKeys)
		event.post(eventAI3)
		
	def AIstopRight(self):
		eventAI3 = event.Event(KEYUP, key= K_RIGHT)
		listKeys = list(self.keys)
		listKeys[K_RIGHT] = False
		self.keys = tuple(listKeys)
		event.post(eventAI3)
	
	# AI 1: moves left and right and shoots	
	def AIevents(self):
		if not self.keys[K_LEFT] and not self.keys[K_RIGHT]:
			self.AIgoLeft()
		for plShip in self.playerGroup:
			if plShip.rect.x <= 10:
				self.AIstopLeft()
				self.AIgoRight()
			elif plShip.rect.x >= 1200:
				self.AIstopRight()
				self.AIgoLeft()
		if len(self.bullets) == 0:
			self.AIshoot()
	
	# AI 2
	def AIevents2(self):
		if len(self.bullets) == 0:
			self.AIshoot()
		dir = self.chooseDirectionBullet2()
		if dir == 0:
			dir = self.chooseDirectionEnemy2()
		if self.keys[K_LEFT]:
			if dir == 3:
				self.AIstopLeft()
				self.AIgoRight()
			elif not dir == 1:
				self.AIstopLeft()
		elif self.keys[K_RIGHT]:
			if dir == 1:
				self.AIstopRight()
				self.AIgoLeft()
			elif not dir == 3:
				self.AIstopRight()
		else:
			if dir == 1:
				self.AIgoLeft()
			elif dir == 3:
				self.AIgoRight()

	def chooseDirectionBullet2(self):
		if len(self.playerGroup) == 1:
			for player in self.playerGroup:
				bulletList = []
				for eBullet in self.enemyBullets:
					bulletList.append(eBullet.rect)
				rect1 = Rect(player.rect.x - 5, 300, 5, 420)
				rect2 = Rect(player.rect.x, 300, 25, 420)
				rect3 = Rect(player.rect.x + 25, 300, 25, 420 )
				rect4 = Rect(player.rect.x +50, 300, 5, 420)
				colbul1 = rect1.collidelistall(bulletList)
				colbul2 = rect2.collidelistall(bulletList)
				colbul3 = rect3.collidelistall(bulletList)
				colbul4 = rect4.collidelistall(bulletList)
				if len(colbul1) > 0:
					close1 = max([bulletList[i].y for i in colbul1])
				else:
					close1 = 0
				if len(colbul2) > 0:
					close2 = max([bulletList[i].y for i in colbul2])
				else:
					close2 = 0
				if len(colbul3) > 0:
					close3 = max([bulletList[i].y for i in colbul3])
				else:
					close3 = 0
				if len(colbul4) > 0:
					close4 = max([bulletList[i].y for i in colbul4])
				else:
					close4 = 0
				closest = max(close1, close2, close3, close4)
				furthest = min(close1, close2, close3, close4)
				if closest == 0:
					return 0
				elif closest == close2:
					return 3
				elif closest == close3:
					return 1
				elif closest == close1:
					if close4 >= close3 and close4 >= close2:
						return 2
					else:
						return 3
				elif closest == close4:
					if close1 >= close3 and close1 >= close2:
						return 2
					else:
						return 1
				
	
	def chooseDirectionEnemy2(self):
		if len(self.playerGroup) == 1:
			for player in self.playerGroup:
				rect1 = Rect(player.rect.x, 0, 50, 720)
				enemyListx = []
				enemyList = []
				for en in self.enemies:
					enemyListx.append(en.rect.x)
					enemyList.append(en.rect)
				colen1 = rect1.collidelistall(enemyList)
				if len(colen1) > 0:
					return 2			
				enemyListx = numpy.array(enemyListx)
				near = find_nearest(enemyListx, player.rect.x)
				if near < player.rect.x:
					return 1
				else:
					return 3
	
	def AIevents3(self):
		if self.score < 1000 and self.AI3shoot(self.player.rect.x+23):
			self.AIshoot()
		elif self.score >= 1000 and self.AI3shoot(self.player.rect.x+8):
			self.AIshoot()
		elif self.score >= 1000 and self.AI3shoot(self.player.rect.x+38):
			self.AIshoot()
		dir = self.chooseDirectionBullet2()
		if dir == 0:
			dir = self.chooseDirectionEnemy3()
		if self.keys[K_LEFT]:
			if dir == 3:
				self.AIstopLeft()
				self.AIgoRight()
			elif not dir == 1:
				self.AIstopLeft()
		elif self.keys[K_RIGHT]:
			if dir == 1:
				self.AIstopRight()
				self.AIgoLeft()
			elif not dir == 3:
				self.AIstopRight()
		else:
			if dir == 1:
				self.AIgoLeft()
			elif dir == 3:
				self.AIgoRight()
			
	
	def AI3shoot(self, bulletX):
		if len(self.bullets) == 0:
			testTime = time.get_ticks()
			for e in self.enemies:
				currMoveNumbers = e.moveNumber
				bullHeight = self.player.rect.y
				rectHeight = 5
				eTime = e.timer
				emoveTime = e.moveTime
				currentDir = e.direction
				remMoves = 0
				if e.direction == 1:
					remMoves = e.rightMoves
				else:
					remMoves = e.leftMoves
				rectList = []
				currBullX = bulletX
				while(bullHeight > 0):
					while(testTime - eTime < emoveTime):
						bullHeight -= 15
						rectHeight += 15
						testTime += 30
					rectList.append(Rect(currBullX, bullHeight, 1, rectHeight))
					rectHeight = 5
					eTime += emoveTime
					if currMoveNumbers >= remMoves:
						bullHeight -= 35
						currentDir *= -1
						currMoveNumbers = 0
					else:
						currBullX -= currentDir * 10
						currMoveNumbers +=1
				for e2 in self.enemies:
					if len(e2.rect.collidelistall(rectList)) > 0:
						return True
		##if self.moveNumber >= self.rightMoves and self.direction == 1:
				break
		return False
		
	def chooseDirectionEnemy3(self):
		bulletX = self.player.rect.x
		hgt = max([i.rect.y for i in self.enemies])
		enemyList = []
		for i in self.enemies:
			enemyList.append(i)
		if self.score > 1000:
			if enemyList[0].direction == 1:
				bulletX += 8
			else:
				bulletX += 38
		else:
			bulletX += 23
		if hgt > 500:
			lowest = [i for i, element in enumerate(enemyList) if hgt == element.rect.y]
			lowestList = [enemyList[j] for j in lowest]
			closest = (numpy.abs(numpy.array([k.rect.x for k in lowestList]) - self.player.rect.x)).argmin()
			return self.chooseDirectionp2Enemy3(bulletX, [lowestList[closest]])
		else:
			width = 0
			if enemyList[0].direction == 1:
				width = min([i.rect.x for i in self.enemies])
			else:
				width = max([i.rect.x for i in self.enemies])
			lowest = [i for i, element in enumerate(enemyList) if width == element.rect.x]
			lowestList = [enemyList[j] for j in lowest]
			return self.chooseDirectionp2Enemy3(bulletX, lowestList)
    ##idx = (np.abs(array-value)).argmin()
			
	def chooseDirectionp2Enemy3(self, bulletX, enemyToFind):
		testTime = time.get_ticks()
		for e in self.enemies:
			currMoveNumbers = e.moveNumber
			bullHeight = self.player.rect.y
			rectHeight = 15
			eTime = e.timer
			emoveTime = e.moveTime
			currentDir = e.direction
			remMoves = 0
			if e.direction == 1:
				remMoves = e.rightMoves
			else:
				remMoves = e.leftMoves
			rectList = []
			currBullX = bulletX
			while(bullHeight > 0):
				while(testTime - eTime < emoveTime):
					bullHeight -= 15
					rectHeight += 15
					testTime += 30
				rectList.append(Rect(currBullX, bullHeight, 1, rectHeight))
				eTime += emoveTime
				rectHeight = 5
				if currMoveNumbers >= remMoves:
					bullHeight -= 35
					currentDir *= -1
					currMoveNumbers = 0
				else:
					currBullX -= currentDir * 10
					currMoveNumbers +=1
			for e2 in enemyToFind:
				if len(e2.rect.collidelistall(rectList)) > 0:
					return 2
				else:
					checkRec = Rect(-100, enemyToFind[0].rect.y, 1500, enemyToFind[0].rect.height)
					indexRect = checkRec.collidelist(rectList)
					if indexRect == -1:
						return 2
					else:
						if rectList[indexRect].x > enemyToFind[0].rect.x:
							return 1
						else:
							return 3
	##if self.moveNumber >= self.rightMoves and self.direction == 1:
			break
		return 2
					
	def AIchooseMood(self):
		eventMood = event.Event(KEYUP, key= K_KP9)
		listKeys = list(self.keys)
		listKeys[K_KP9] = True
		listKeys[K_e] = False
		listKeys[K_o] = False
		listKeys[K_h] = False
		self.keys = tuple(listKeys)
		event.post(eventMood)	
	
	
	def AIchooseStart(self):
		eventMood = event.Event(KEYDOWN, key= K_KP9)
		event.post(eventMood)
		
	def AIchooseDiff(self):
		if self.won == 1:
			if self.distanceEnd > 500:
				self.AIchooseOK()
			if self.timeSpent < 60000:
				self.AIchooseEASY()
			elif self.livesStart / self.lives < 2:
				self.AIchooseEASY()
			else:
				self.AIchooseOK()
		else:
			if float(len(self.enemies)) / float(5 * self.columnAmount) <= 0.2:
				self.AIchooseOK()			
			elif self.instakill:
				self.AIchooseHARD()
			else:
				self.AIchooseOK()
	
			
	def AIchooseEASY(self):
		eventdiff = event.Event(KEYUP, key= K_e)
		listKeys = list(self.keys)
		listKeys[K_e] = True
		self.keys = tuple(listKeys)
		event.post(eventdiff)
	def AIchooseOK(self):
		eventdiff = event.Event(KEYUP, key= K_o)
		listKeys = list(self.keys)
		listKeys[K_o] = True
		self.keys = tuple(listKeys)
		event.post(eventdiff)	
	def AIchooseHARD(self):
		eventdiff = event.Event(KEYUP, key= K_h)
		listKeys = list(self.keys)
		listKeys[K_h] = True
		self.keys = tuple(listKeys)
		event.post(eventdiff)

			
	def main(self):
		self.saveScreen = False
		while True:
			if self.mainScreen:
				self.reset(0, self.lives, True)
				self.screen.blit(self.background, (0,0))
				self.titleText.draw(self.screen)
				self.titleText2.draw(self.screen)
				self.enemy1Text.draw(self.screen)
				self.enemy2Text.draw(self.screen)
				self.enemy3Text.draw(self.screen)
				self.enemy4Text.draw(self.screen)
				self.mainText.draw(self.screen)
				self.keys = key.get_pressed()
				self.AIchooseStart()
				self.create_main_menu(self.keys)

			elif self.startGame:
				if len(self.enemies) == 0:
					self.won = 1
					self.reachStage2 = True
					currentTime = time.get_ticks()
					self.timeSpent = currentTime - self.startTime
					if currentTime - self.gameTimer < 3000:              
						self.screen.blit(self.background, (0,0))
						self.scoreText2 = Text(FONT, 20, str(self.score), GREEN, 85, 5)
						self.scoreText.draw(self.screen)
						self.scoreText2.draw(self.screen)
						self.nextRoundText.draw(self.screen)
						self.livesText.draw(self.screen)
						self.livesGroup.update(self.keys)
						self.check_input()
					if currentTime - self.gameTimer > 3000:
						# Move enemies closer to bottom
						#self.enemyPositionStart += 35
						#self.reset(self.score, self.lives)
						#self.make_enemies()
						#self.gameTimer += 3000
						self.startGame = False
						self.likeScreen = True
				else:
					currentTime = time.get_ticks()
					self.play_main_music(currentTime)              
					self.screen.blit(self.background, (0,0))
					self.allBlockers.update(self.screen)
					self.scoreText2 = Text(FONT, 20, str(self.score), GREEN, 85, 5)
					self.scoreText.draw(self.screen)
					self.scoreText2.draw(self.screen)
					self.livesText.draw(self.screen)
					self.check_input()
					#self.pressed = self.pressed + sum(self.keys)
					if self.artificial == 0:
						self.AIevents()
					else:
						self.AIevents3()
					self.allSprites.update(self.keys, currentTime, self.killedRow, self.killedColumn, self.killedArray)
					self.explosionsGroup.update(self.keys, currentTime)
					self.check_collisions()
					self.create_new_ship(self.makeNewShip, currentTime)
					self.update_enemy_speed()

					if len(self.enemies) > 0:
						self.make_enemies_shoot(self.bulletSpeed)
						for en in self.enemies:
							self.distanceEnd = en.distanceAdded + self.enemyPositionDefault
							break
					if self.distanceEnd >= 900 or currentTime - self.startTime >= 600000:
						self.startGame = False
						self.gameOver = True
	
			elif self.gameOver:
				self.won = 0
				currentTime = time.get_ticks()
				self.timeSpent = currentTime - self.startTime
				# Reset enemy starting position
				self.enemyPositionStart = self.enemyPositionDefault
				self.create_game_over(currentTime)
				#return 0
			
			elif self.likeScreen:
				self.screen.blit(self.background, (0,0))
				self.AIchooseDiff()
				self.liked = self.create_like_screen(self.keys)
				
			elif self.moodScreen:
				self.screen.blit(self.background, (0,0))
				self.AIchooseMood()
				self.mood = self.create_mood_screen(self.keys)
			
#			elif self.continueScreen:
#				self.screen.blit(self.background, (0,0))
#				self.check_input()
#				self.continueGame = self.create_continue_screen(self.keys)			
#				
			elif self.saveScreen:
				self.screen.blit(self.background, (0,0))
				self.create_save_screen()
			
			elif self.end:
				if self.mainQuit:
					self.state = False
				else:
#					self.state = PlayerState(self.won, self.timeSpent, self.bulletShot, self.bulletHit, self.pressed, self.liked, self.mood, self.distanceEnd, self.lives, len(self.enemies), self.continueGame, self.mysteryHit, self.reachStage2, self.reachDoubleBullet, self.timeDoubleBullet, self.shotStage2, self.shotdouble, self.hitStage2, self.hitdouble, self.RageQuit, self.instakill, self.enemyBulletHit, self.enemyHit, self.blockerHit)
					self.state = PlayerState(self.won, self.timeSpent, self.bulletShot, self.bulletHit, self.pressed, self.liked, self.mood, self.distanceEnd, self.lives, len(self.enemies), self.mysteryHit, self.reachStage2, self.reachDoubleBullet, self.timeDoubleBullet, self.shotStage2, self.shotdouble, self.hitStage2, self.hitdouble, self.RageQuit, self.instakill, self.enemyBulletHit, self.enemyHit, self.blockerHit)
				return self.state
				
			display.update()
			self.clock.tick(60)
#############################################
#############################################			
# REINFORCEMENT LEARNING ALGORITHM          #
# TEMPORAL DIFFERNCE LEARNING               #
#############################################
#############################################				
	
class GameState(object):
	def __init__(self, startDistance, enemySpeed, bulletSpeed, columnAmount, speedUpPerc, livesStart):
		self.startDistance = startDistance
		self.enemySpeed = enemySpeed
		self.bulletSpeed = bulletSpeed
		self.columnAmount = columnAmount
		self.speedUpPerc = speedUpPerc	
		self.livesStart = livesStart
	
class PlayerState(object):
	def __init__(self, win, Time, shot, hit, pressed, like, gameMood, distance, lives, enemies, mysteryShot, stage2, doubleBullets, timeDoubleBullet, shotStage2, shotdouble, hitStage2, hitdouble, rageQuit, instakill, enemyBulletHit, enemyHit, blockerHit):
		self.win = win #1 if win 0 if loss
		self.Time = Time # time spent in game
		self.shot = shot #amount of bullets shot
		self.hit = hit # amount of hits
		self.pressed = pressed # buttons pressed
		self.like = like #did the player like
		self.gameMood = gameMood
		self.distance = distance #ending distance of enemy
		self.lives = lives #amount of ending lives
		self.enemies = enemies #remaining enemies
		#self.continueGame = continueGame #for script
		
		self.mysteryShot = mysteryShot
		self.stage2 = stage2
		self.doubleBullets = doubleBullets
		self.timeDoubleBullet = timeDoubleBullet
		
		self.shotStage2 = shotStage2
		self.shotdouble = shotdouble
		self.hitStage2 = hitStage2
		self.hitdouble = hitdouble
		
		self.rageQuit = rageQuit
		
		self.instakill = instakill
		self.enemyBulletHit = enemyBulletHit
		self.enemyHit = enemyHit
		self.blockerHit = blockerHit

def selectGameState(fileName, prevGame):
	plState = setupPlayerState(fileName)
	statsPlayer = setupArray(plState)
	#matrixSetup = setupMatrix(statsPlayer, prevGame)
	prevGameState = [prevGame[0],prevGame[1],prevGame[2],prevGame[3],prevGame[4],prevGame[5]]
	prevGameState.extend(statsPlayer)
	print(prevGameState)
	prevGameState = scaler.transform([prevGameState])
	optimalGame = dqnnetwork.inference(prevGameState)
	print(dqnnetwork.inferenceQValue(prevGameState))
	return GameState(int(prevGame[0]),var2[optimalGame],int(prevGame[2]),int(prevGame[3]),float(prevGame[4]),int(prevGame[5]))
	#return valueToGameState(optimalGame, [var1, var2, var3, var4, var5, var6])
	
def valueToGameState(value, poss):
	rem = value
	state = []
	for i in range(len(poss) - 1, -1, -1):
		rem, par = divmod(rem, len(poss[i]))
		state.insert(0, poss[i][par])
	print(state)
	return GameState(state[0],state[1],state[2],state[3],state[4],state[5])
		
		

def find_nearest(array, value):
	idx = (numpy.abs(array-value)).argmin()
	return array[idx]
	
def findBestState(matrix):
	model = joblib.load('trainedModelAI1to6001.pkl')
	scaler = joblib.load('scalerAI1to6001.pkl')
	with open("matrix.txt", "w") as m:
		m.write(str(matrix))
	smatrix = scaler.transform(matrix)
	new_matrix = poly.fit_transform(smatrix)
	predictions = model.predict(new_matrix)
	with open("predictions.txt", "w") as m:
		m.write(str(list(predictions)))
	index, value = max(enumerate(predictions), key=operator.itemgetter(1))
	bestState = matrix[index]
	print(new_matrix[index])
	variables = len(bestState)
	return GameState(bestState[variables-6],bestState[variables-5],bestState[variables-4],bestState[variables-3],bestState[variables-2],bestState[variables-1])
	
def setupMatrix(statsArray, gameState):
	array1 = [gameState[0],gameState[1],gameState[2],gameState[3],gameState[4],gameState[5]]
	ii = []
	for i in itertools.product(var1,var2,var3,var4,var5,var6):
		newArr = []
		newArr.extend(array1)
		newArr.extend(statsArray)
		newArr.extend(list(i))
		ii.append(newArr)
	return ii

def setupArray(currentPlayer):	
	i = find_nearest(Acc_win,sum(currentPlayer.win)/len(currentPlayer.win)) #winratio
	sumShot = sum(currentPlayer.shot)
	if sumShot == 0.:
		j = 0.
		u = 0.
		v = 0.
		w = 0.
	else:
		j = find_nearest(Acc_win, sum(currentPlayer.hit)/sumShot) #general accuracy
		u = find_nearest(Acc_win, sum(currentPlayer.enemyBulletHit)/sumShot) #general accuracy
		v = find_nearest(Acc_win, sum(currentPlayer.enemyHit)/sumShot) #general accuracy
		w = find_nearest(Acc_win, sum(currentPlayer.blockerHit)/sumShot) #general accuracy
		
	k = find_nearest(timeposs, sum(currentPlayer.Time)/len(currentPlayer.Time)) #avg time played
	l = find_nearest(but, sum(currentPlayer.pressed)/len(currentPlayer.pressed)) #avg buttons pushed
	m = find_nearest(distdone, sum(currentPlayer.distance)/len(currentPlayer.distance)) #ending distance of enemy
	n = find_nearest(mystery_arr, sum(currentPlayer.mysteryShot)/len(currentPlayer.mysteryShot)) #avg mysteries shot
	o = find_nearest(Acc_win, sum(currentPlayer.stage2)/len(currentPlayer.stage2)) #avg times gotten to stage 2
	p = find_nearest(Acc_win, sum(currentPlayer.doubleBullets)/len(currentPlayer.doubleBullets)) #avg times gotten to 1k points
	sumShot2 = sum(currentPlayer.shotStage2)
	if sumShot2 == 0.:
		q = 0.
	else:
		q = find_nearest(Acc_win, sum(currentPlayer.hitStage2)/sumShot2) #acc in stage 2
	sumShotdouble = sum(currentPlayer.shotdouble)
	if sumShotdouble == 0.:
		r = 0.
	else:
		r = find_nearest(Acc_win, sum(currentPlayer.hitdouble)/sumShotdouble) #acc after 1k points
	s = find_nearest(timeposs, sum(currentPlayer.timeDoubleBullet)/len(currentPlayer.timeDoubleBullet))
	t = find_nearest(Acc_win, sum(currentPlayer.instakill)/len(currentPlayer.instakill))
	return [i,j,k,l,m,n,o,p,q,r,s,t,u,v,w]

def setupPlayerState(fileName):
	currentPlayer = PlayerState([],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[])
	if os.path.isfile(fileName):	
		with open(fileName, "r") as file:
			lines = file.readlines()
			experiments = len(lines)
			values = []
			for line in lines:
				values.append(line.split())
			for val in range(0, experiments):
				current = values[val]
				current = [w.replace('False', '0').replace('True', '1') for w in current]
				current = [float(i) for i in current]
				currentPlayer.win.append(current[6]) #1 if win 0 if loss
				currentPlayer.Time.append(current[7]) # time spent in game
				currentPlayer.shot.append(current[8]) #amount of bullets shot
				currentPlayer.hit.append(current[9]) # amount of hits
				currentPlayer.pressed.append(current[10]) # buttons pressed
				currentPlayer.like.append(current[11]) #did the player like
				currentPlayer.gameMood.append(current[12])
				currentPlayer.distance.append(current[13]) #ending distance of enemy
				currentPlayer.lives.append(current[14]) #amount of ending lives
				currentPlayer.enemies.append(current[15]) #remaining enemies
				
				currentPlayer.mysteryShot.append(current[16])
				currentPlayer.stage2.append(current[17])
				currentPlayer.doubleBullets.append(current[18])
				currentPlayer.timeDoubleBullet.append(current[19])
				
				currentPlayer.shotStage2.append(current[20])
				currentPlayer.shotdouble.append(current[21])
				currentPlayer.hitStage2.append(current[22])
				currentPlayer.hitdouble.append(current[23])
				
				currentPlayer.rageQuit.append(current[24])
				currentPlayer.instakill.append(current[25])
				currentPlayer.enemyBulletHit.append(current[26])
				currentPlayer.enemyHit.append(current[27])
				currentPlayer.blockerHit.append(current[28])
	return currentPlayer
	
def setupGameState(fileName):
	if os.path.isfile(fileName):
		with open(fileName) as file:
			FileNameList = file.readlines()
			return FileNameList[len(FileNameList) - 1].split()
		

		
		
		
if __name__ == '__main__':
	logFileNameList = []
	#enemyStart = int(sys.argv[1])
	#enemySpeed = int(sys.argv[2])
	#bulletSpeed = int(sys.argv[3])
	#columnAmount = int(sys.argv[4])
	logID = uuid.uuid4()
	run = True
	logFilename = os.path.join(os.getcwd(), 'logs', 'logfile2.txt') 
	fullLogFileName = os.path.join(os.getcwd(), 'logs', 'fulllogfile2.txt')
	#logFilename = ".\\logs\\logfile" + str(logID) + ".txt"
	#with open(logFilename, "a") as logging_file:
	#	logging_file.write(str(datetime.datetime.today()) + "\n")
	#my_file = glob.glob('./logfile*.txt')
	if os.path.isfile(logFilename):
		nextGameState = setupGameState(logFilename)
	
	while(run):
		if os.path.isfile(logFilename):
			with open(logFilename) as logfilenamefile:
				logFileNameList = logfilenamefile.readlines()
			nextGameState = selectGameState(logFilename, logFileNameList[len(logFileNameList)- 1].split())
		else: 
			nextGameState = GameState(150, 500, 500, 11, 0., 3)
		#my_file.append('.\\logfile' + str(uuid.uuid4()) + '.txt' )
		game = SpaceInvaders(nextGameState.startDistance, nextGameState.enemySpeed, nextGameState.bulletSpeed, nextGameState.columnAmount, nextGameState.speedUpPerc, nextGameState.livesStart, logID)
		print([nextGameState.startDistance, nextGameState.enemySpeed, nextGameState.bulletSpeed, nextGameState.columnAmount, nextGameState.speedUpPerc, nextGameState.livesStart])
		currentState = game.main()
		if not currentState:
			run = False
		else:
			#with open(logFilename, "a") as logging_file:
				#logging_file.write(str(var1) + " " + str(var2) + " " + str(var3) + " " + str(var4) + " " + str(var5) + " " + str(var6) + " " + str(currentState.win) + " " + str(currentState.Time) + " " + str(currentState.shot) + " " + str(currentState.hit) + " " + str(currentState.pressed) + " " + str(currentState.like) + " " + str(currentState.gameMood) + " " + str(currentState.distance) + " " +  str(currentState.lives) + " " + str(currentState.enemies)+ " " + str(currentState.continueGame) + " " + str(currentState.mysteryShot) + " " + str(currentState.stage2) + " " + str(currentState.doubleBullets) + " " + str(currentState.timeDoubleBullet) + " " + str(currentState.shotStage2) + " " + str(currentState.shotdouble) + " " + str(currentState.hitStage2) + " " + str(currentState.hitdouble) + " " + str(currentState.rageQuit) + " " + str(currentState.instakill) + " " + str(currentState.enemyBulletHit) + " " + str(currentState.enemyHit) + " " + str(currentState.blockerHit) + "\n")
			#	logging_file.write(str(var1) + " " + str(var2) + " " + str(var3) + " " + str(var4) + " " + str(var5) + " " + str(var6) + " " + str(currentState.win) + " " + str(currentState.Time) + " " + str(currentState.shot) + " " + str(currentState.hit) + " " + str(currentState.pressed) + " " + str(currentState.like) + " " + str(currentState.gameMood) + " " + str(currentState.distance) + " " +  str(currentState.lives) + " " + str(currentState.enemies)+ " " + str(currentState.mysteryShot) + " " + str(currentState.stage2) + " " + str(currentState.doubleBullets) + " " + str(currentState.timeDoubleBullet) + " " + str(currentState.shotStage2) + " " + str(currentState.shotdouble) + " " + str(currentState.hitStage2) + " " + str(currentState.hitdouble) + " " + str(currentState.rageQuit) + " " + str(currentState.instakill) + " " + str(currentState.enemyBulletHit) + " " + str(currentState.enemyHit) + " " + str(currentState.blockerHit) + "\n")
			run = not currentState.rageQuit
			logFileNameList.append(str(nextGameState.startDistance) + " " + str(nextGameState.enemySpeed) + " " + str(nextGameState.bulletSpeed) + " " + str(nextGameState.columnAmount) + " " + str(nextGameState.speedUpPerc) + " " + str(nextGameState.livesStart) + " " + str(currentState.win) + " " + str(currentState.Time) + " " + str(currentState.shot) + " " + str(currentState.hit) + " " + str(currentState.pressed) + " " + str(currentState.like) + " " + str(currentState.gameMood) + " " + str(currentState.distance) + " " +  str(currentState.lives) + " " + str(currentState.enemies)+ " " + str(currentState.mysteryShot) + " " + str(currentState.stage2) + " " + str(currentState.doubleBullets) + " " + str(currentState.timeDoubleBullet) + " " + str(currentState.shotStage2) + " " + str(currentState.shotdouble) + " " + str(currentState.hitStage2) + " " + str(currentState.hitdouble) + " " + str(currentState.rageQuit) + " " + str(currentState.instakill) + " " + str(currentState.enemyBulletHit) + " " + str(currentState.enemyHit) + " " + str(currentState.blockerHit) + "\n")
			with open(fullLogFileName, "a") as full_logging_file:
				full_logging_file.write(str(nextGameState.startDistance) + " " + str(nextGameState.enemySpeed) + " " + str(nextGameState.bulletSpeed) + " " + str(nextGameState.columnAmount) + " " + str(nextGameState.speedUpPerc) + " " + str(nextGameState.livesStart) + " " + str(currentState.win) + " " + str(currentState.Time) + " " + str(currentState.shot) + " " + str(currentState.hit) + " " + str(currentState.pressed) + " " + str(currentState.like) + " " + str(currentState.gameMood) + " " + str(currentState.distance) + " " +  str(currentState.lives) + " " + str(currentState.enemies)+ " " + str(currentState.mysteryShot) + " " + str(currentState.stage2) + " " + str(currentState.doubleBullets) + " " + str(currentState.timeDoubleBullet) + " " + str(currentState.shotStage2) + " " + str(currentState.shotdouble) + " " + str(currentState.hitStage2) + " " + str(currentState.hitdouble) + " " + str(currentState.rageQuit) + " " + str(currentState.instakill) + " " + str(currentState.enemyBulletHit) + " " + str(currentState.enemyHit) + " " + str(currentState.blockerHit) + "\n")
			if len(logFileNameList) > FRAME_RL:
				del logFileNameList[0]
			with open(logFilename, "w") as logging_file:
				for i in logFileNameList:
					logging_file.write(i)
		nextGameState = logFileNameList[len(logFileNameList)-1].split()