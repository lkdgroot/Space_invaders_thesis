import spaceinvadersNNRB
import dqnRB
import os
import random
import numpy as np
from sklearn.externals import joblib


var1 = [i for i in range(75, 251, 50)] #startDistance
var2 = [i for i in range(50, 1001, 50)] #enemySpeed
var3 = [i for i in range(200, 801, 100)] #bulletSpeed
var4 = [i for i in range(8, 21, 3)] #columnAmount
var5 = [i for i in np.arange(0,0.51,0.10)] #stage2 Cutoff
var6 = [i for i in range(0,6,1)] #lives

rewards = [-100,100,-100]

timeposs = np.array([0, 15000,30000,45000,60000,75000,90000, 105000, 120000, 135000, 150000], dtype=float)
but = np.array([0, 1000,2000, 3000,4000, 5000,6000, 7000,8000,9000,10000], dtype=float)
Acc_win = np.array([0.0, 0.1, 0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0], dtype=float)
mystery_arr = np.array([0,1,2,3,4,5], dtype=float)
distdone = np.array([200,250,300,350,400,450,500,550,600], dtype=float)

class Environment(object):
	def __init__(self, switch, epsilon, frame, batchSize, rbuffFile, dqnFile, games):
		self.switch = switch #after how many games do we switch AI
		self.epsilon = epsilon #epsilon for exploration of the problem
		self.frame = frame #How many games we keep in memory for state space
		self.batchSize = batchSize #Amount of games to get out of the replay buffer every time
		self.games = games #Amount of games before we stop
		
		self.deep = dqnRB.DQN(len(var2), dqnFile)
		
		self.buffer = []
		if rbuffFile is not None:
			self.buffer = joblib.load(rbuffFile)
		self.bufferCount = len(self.buffer)
		
		self.fullCurrentState = []
		
		self.Artificial = random.choice([0,1])
		
	def runEnvironment(self):
	#Get 'frame' games
		run = True
		fullLogFileName = os.path.join(os.getcwd(), 'logs', 'fulllogfile.txt')
		open(fullLogFileName, 'a').close()
		while(run):
			nextGameState = None
			nextFullState = None
			logFileList = None
			logState = None
			action = 0
			if len(self.fullCurrentState) < 23 * self.frame:
				nextGameState = spaceinvadersNNRB.GameState(100, random.choice(var2), 500, 14, 0.25, 3)
			else:
				nextGameState, action = self.selectGameState(self.fullCurrentState)
			game = spaceinvadersNNRB.SpaceInvaders(nextGameState.startDistance, nextGameState.enemySpeed, nextGameState.bulletSpeed, nextGameState.columnAmount, nextGameState.speedUpPerc, nextGameState.livesStart, self.Artificial)
			currentState = spaceinvadersNNRB.startGame(game)
			if len(self.fullCurrentState) == 23 * self.frame:
				nextFullState = self.trainDeep(self.fullCurrentState, currentState, nextGameState, action)
			else:
				nextFullState = self.fullCurrentState
				nextFullState.extend(self.getCurrentState(self.gameAndPlayertoString(nextGameState, currentState)))
			
			if not currentState:
				run = False
			else:
				run = not currentState.rageQuit
				#logFileList.append(str(nextGameState.startDistance) + " " + str(nextGameState.enemySpeed) + " " + str(nextGameState.bulletSpeed) + " " + str(nextGameState.columnAmount) + " " + str(nextGameState.speedUpPerc) + " " + str(nextGameState.livesStart) + " " + str(currentState.win) + " " + str(currentState.Time) + " " + str(currentState.shot) + " " + str(currentState.hit) + " " + str(currentState.pressed) + " " + str(currentState.like) + " " + str(currentState.gameMood) + " " + str(currentState.distance) + " " +  str(currentState.lives) + " " + str(currentState.enemies)+ " " + str(currentState.mysteryShot) + " " + str(currentState.stage2) + " " + str(currentState.doubleBullets) + " " + str(currentState.timeDoubleBullet) + " " + str(currentState.shotStage2) + " " + str(currentState.shotdouble) + " " + str(currentState.hitStage2) + " " + str(currentState.hitdouble) + " " + str(currentState.rageQuit) + " " + str(currentState.instakill) + " " + str(currentState.enemyBulletHit) + " " + str(currentState.enemyHit) + " " + str(currentState.blockerHit) + "\n")
				with open(fullLogFileName, "a") as full_logging_file:
					full_logging_file.write(str(nextGameState.startDistance) + " " + str(nextGameState.enemySpeed) + " " + str(nextGameState.bulletSpeed) + " " + str(nextGameState.columnAmount) + " " + str(nextGameState.speedUpPerc) + " " + str(nextGameState.livesStart) + " " + str(currentState.win) + " " + str(currentState.Time) + " " + str(currentState.shot) + " " + str(currentState.hit) + " " + str(currentState.pressed) + " " + str(currentState.like) + " " + str(currentState.gameMood) + " " + str(currentState.distance) + " " +  str(currentState.lives) + " " + str(currentState.enemies)+ " " + str(currentState.mysteryShot) + " " + str(currentState.stage2) + " " + str(currentState.doubleBullets) + " " + str(currentState.timeDoubleBullet) + " " + str(currentState.shotStage2) + " " + str(currentState.shotdouble) + " " + str(currentState.hitStage2) + " " + str(currentState.hitdouble) + " " + str(currentState.rageQuit) + " " + str(currentState.instakill) + " " + str(currentState.enemyBulletHit) + " " + str(currentState.enemyHit) + " " + str(currentState.blockerHit) + "\n")
				#if len(fullCurrentState) > 23 * self.frame:
				#	for i in range(0,23):
				#		del fullCurrentState[0]
				#with open(logFileName, "w") as logging_file:
				#	for i in logFileList:
				#		logging_file.write(i)
				self.fullCurrentState = nextFullState
			if self.bufferCount - self.batchSize > 0 and(self.bufferCount - self.batchSize) % self.switch == 0:
				self.Artificial = random.choice([0,1])
				self.deep.save(self.bufferCount - self.batchSize)
				joblib.dump(self.buffer, 'buffer' + str(self.bufferCount - self.batchSize) + '.pkl')
			if self.bufferCount - self.batchSize == self.games:
				run = False
	
	def filetoState(self,logfile):
		state = []
		for i in logfile:
			state.extend(self.getCurrentState(i))
		return state
	
	def selectGameState(self, logstate):
		action = self.epsilongreedy(logstate)
		return spaceinvadersNNRB.GameState(100, var2[action], 500, 14, 0.25, 3), action
		
	def getCurrentState(self,logline):
		values = logline.split()
		state = [find_nearest(np.array(var1), int(values[0]))/max(var1),find_nearest(np.array(var2), int(values[1]))/max(var2),find_nearest(np.array(var3), int(values[2]))/max(var3),find_nearest(np.array(var4), int(values[3]))/max(var4),find_nearest(np.array(var5), float(values[4]))/max(var5),find_nearest(np.array(var6), int(values[5]))/max(var6)]
		state.append(float(values[6])) #win/loss
		if(int(values[8]) == 0):
			state.extend([0.0,0.0,0.0,0.0])
		else:
			state.append(find_nearest(Acc_win, float(values[9])/float(values[8]))) #general accuracy
			state.append(find_nearest(Acc_win, float(values[26])/float(values[8]))) #accuracy bullets hit
			state.append(find_nearest(Acc_win, float(values[27])/float(values[8]))) #accuracy enemies hit
			state.append(find_nearest(Acc_win, float(values[28])/float(values[8]))) #accuracy blockers hit
		state.append(float(find_nearest(timeposs, float(values[7])))/max(timeposs)) #time played
		state.append(find_nearest(but, float(values[10])) / max(but)) #buttons pressed
		state.append(find_nearest(distdone, float(values[13])) / max(distdone)) #final distance
		state.append(float(values[14])/float(max(var6))) #final lives
		state.append(float(values[15])/(float(max(var4))*5.0)) #final enemies
		state.append(find_nearest(mystery_arr, float(values[16])) / max(mystery_arr)) #mysteries shot
		state.append(float(bool(values[17]))) #reached stage2
		state.append(float(bool(values[18]))) #got double bullets / 1k points
		state.append(float(find_nearest(timeposs, float(values[19])))/max(timeposs)) #time till double bullets / if not reached = time played
		if int(values[20]) == 0:
			state.append(0.0)
		else:
			state.append(find_nearest(Acc_win, float(values[22])/float(values[20]))) #Accuracy state 2
		if int(values[21]) == 0:
			state.append(0.0)
		else:
			state.append(find_nearest(Acc_win, float(values[23])/float(values[21]))) #Accuracy double bullets
		state.append(float(bool(values[25]))) #instakilled
		return state
		
	def epsilongreedy(self,state):
		if np.random.choice([True, False], p=[self.epsilon, 1-self.epsilon]):
			return random.randrange(len(var2))
		else:
			return self.deep.inference([state])
			
	def trainDeep(self, currentState, currentPlayer,currentGame, action): #returns next state for usage
		nextState = [currentState[i] for i in range(int(len(currentState)/self.frame), len(currentState), 1)]
		nextState.extend(self.getCurrentState(self.gameAndPlayertoString(currentGame, currentPlayer)))
		buffElement = replay_buffer(currentState, nextState, action, rewards[int(currentPlayer.like) + 1])
		self.buffer.append(buffElement)
		self.bufferCount += 1
		if self.bufferCount >= self.batchSize:
			self.deep.train(self.makeBatches(), self.bufferCount - self.batchSize, 0, 0)
		return nextState
		
		
		
	def gameAndPlayertoString(self, game, player):
		return str(game.startDistance) + " " + str(game.enemySpeed) + " " + str(game.bulletSpeed) + " " + str(game.columnAmount) + " " + str(game.speedUpPerc) + " " + str(game.livesStart) + " " + str(player.win) + " " + str(player.Time) + " " + str(player.shot) + " " + str(player.hit) + " " + str(player.pressed) + " " + str(player.like) + " " + str(player.gameMood) + " " + str(player.distance) + " " +  str(player.lives) + " " + str(player.enemies)+ " " + str(player.mysteryShot) + " " + str(player.stage2) + " " + str(player.doubleBullets) + " " + str(player.timeDoubleBullet) + " " + str(player.shotStage2) + " " + str(player.shotdouble) + " " + str(player.hitStage2) + " " + str(player.hitdouble) + " " + str(player.rageQuit) + " " + str(player.instakill) + " " + str(player.enemyBulletHit) + " " + str(player.enemyHit) + " " + str(player.blockerHit) + "\n"
	
	def makeBatches(self):
		elements = np.random.choice(self.buffer, self.batchSize, replace = False)
		batches = []
		for i in elements:
			batches.append(Batch(i.state1, i.state2, i.action, False, i.reward))
		return batches
		
	
def find_nearest(array, value):
	idx = (np.abs(array-value)).argmin()
	return array[idx]
	
class replay_buffer(object):
	def __init__(self, state1, state2, action, reward):
		self.state1 = state1
		self.state2 = state2
		self.action = action
		self.reward = reward
		
class Batch(object):
	def __init__(self, state1, state2, action, terminal, reward):
		self.state1 = state1
		self.state2 = state2
		self.action = action
		self.terminal = terminal
		self.reward = reward
		
if __name__ == '__main__':
	env = Environment(500, 0.5, 5, 10, None, None, 10000)
	env.runEnvironment()