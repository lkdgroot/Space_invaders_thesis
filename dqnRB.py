import tensorflow as tf
import numpy as np
import math
import os

LOAD_FROM = None
SAVING = False

gamma = .90

qvalFile = os.path.join(os.getcwd(), 'qvals.txt')

def clipped_error(x):
  # Huber loss
  try:
    return tf.select(tf.abs(x) < 1.0, 0.5 * tf.square(x), tf.abs(x) - 0.5)
  except:
    return tf.where(tf.abs(x) < 1.0, 0.5 * tf.square(x), tf.abs(x) - 0.5)

class DQN:
    def __init__(self, actions, load):
        # Variables
        self.numActions = actions
        self.normalizeWeights = True
        self.learning_rate = 0.0001
        self.targetModelUpdateFrequency = 150 # / 10
        self.saveFrequency = 10000 # / 10
        self.batchesTrained = 0
        self.batchesTrainedSave = 0
        global LOAD_FROM
        LOAD_FROM = load

        tf.set_random_seed(94318)

        self.baseDir = os.getcwd()

        self.sess = tf.Session()

        #assert (len(tf.global_variables()) == 0), "Expected zero variables"
        self.x, self.y = self.buildNetwork('policy', True)
        #assert (len(tf.trainable_variables()) == 10), "Expected 10 trainable_variables"
        #assert (len(tf.global_variables()) == 10), "Expected 10 total variables"
        self.x_target, self.y_target = self.buildNetwork('target', False)
        #assert (len(tf.trainable_variables()) == 10), "Expected 10 trainable_variables"
        #assert (len(tf.global_variables()) == 20), "Expected 20 total variables"

        # build the variable copy ops
        self.update_target = []
        trainable_variables = tf.trainable_variables()
        all_variables = tf.global_variables()
        for i in range(0, len(trainable_variables)):
            self.update_target.append(all_variables[len(trainable_variables) + i].assign(trainable_variables[i]))

        self.a = tf.placeholder(tf.float32, shape=[None, self.numActions])
        print('a %s' % (self.a.get_shape()))
        self.y_ = tf.placeholder(tf.float32, [None])
        print('y_ %s' % (self.y_.get_shape()))
        self.y_a = tf.reduce_sum(tf.multiply(self.y, self.a), reduction_indices=1)
        print('y_a %s' % (self.y_a.get_shape()))

        difference = tf.abs(self.y_a - self.y_)
        quadratic_part = tf.clip_by_value(difference, 0.0, 1.0)
        linear_part = difference - quadratic_part
        errors = (0.5 * tf.square(quadratic_part)) + linear_part
        self.loss = tf.reduce_sum(errors)

        #self.delta = self.y_target - self.y_a
        #self.loss = tf.reduce_mean(clipped_error(self.delta), name='loss')

        optimizer = tf.train.RMSPropOptimizer(self.learning_rate, decay=.98, epsilon=.01)
        self.train_step = optimizer.minimize(self.loss)

        # Initialize Saver
        self.saver = tf.train.Saver(max_to_keep=5)

        # Initialize variables
        self.sess.run(tf.global_variables_initializer())
        self.sess.run(self.update_target)

        # Load CNN if needed
        if LOAD_FROM is not None:
            print('Loading from model file')
            saver = tf.train.import_meta_graph(os.path.join(os.getcwd(), 'cnn_noise', LOAD_FROM))
            saver.restore(self.sess, tf.train.latest_checkpoint(os.path.join(os.getcwd(), 'cnn_noise')))
            #self.saver.restore(self.sess, LOAD_FROM)


    def buildNetwork(self, name, trainable):
        print("Building network for %s trainable=%s" % (name, trainable))

        # First layer takes a screen, and shrinks by 2x
        x = tf.placeholder(tf.float32, shape=[None, 115], name="screens")
        print(x)

        # Fifth layer is fully connected with 512 relu units
        with tf.variable_scope("fc1_" + name):
            W_fc1, b_fc1 = self.makeLayerVariables([115, 512], trainable, "fc1")

            h_fc1 = tf.nn.relu(tf.matmul(x, W_fc1) + b_fc1, name="h_fc1")
            print(h_fc1)

        #Sixth (Output) layer is fully connected linear layer
        with tf.variable_scope("fc2_" + name):
            W_fc2, b_fc2 = self.makeLayerVariables([512, 256], trainable, "fc2")
            h_fc2 = tf.nn.relu(tf.matmul(h_fc1, W_fc2) + b_fc2, name="h_fc2")
            print(h_fc2)
	
        with tf.variable_scope("fc3_" + name):
            W_fc3, b_fc3 = self.makeLayerVariables([256, 128], trainable, "fc3")

            h_fc3 = tf.nn.relu(tf.matmul(h_fc2, W_fc3) + b_fc3, name="h_fc3")
            print(h_fc3)
			
        with tf.variable_scope("fc4_" + name):
            W_fc4, b_fc4 = self.makeLayerVariables([128, self.numActions], trainable, "fc4")

            y = tf.nn.relu(tf.matmul(h_fc3, W_fc4) + b_fc4, name="y")
            print(y)
        return x, y

    def makeLayerVariables(self, shape, trainable, name_suffix):
        if self.normalizeWeights:
            # This is my best guess at what DeepMind does via torch's Linear.lua and SpatialConvolution.lua (see reset methods).
            # np.prod(shape[0:-1]) is attempting to get the total inputs to each node
            stdv = 1.0 / math.sqrt(np.prod(shape[0:-1]))
            weights = tf.Variable(tf.random_uniform(shape, minval=-stdv, maxval=stdv), trainable=trainable,
                                  name='W_' + name_suffix)
            biases = tf.Variable(tf.random_uniform([shape[-1]], minval=-stdv, maxval=stdv), trainable=trainable,
                                 name='W_' + name_suffix)
        else:
            weights = tf.Variable(tf.truncated_normal(shape, stddev=0.01), trainable=trainable, name='W_' + name_suffix)
            biases = tf.Variable(tf.fill([shape[-1]], 0.1), trainable=trainable, name='W_' + name_suffix)
        return weights, biases

    def inference(self, screens):
        y = self.sess.run([self.y], {self.x: screens})
        q_values = np.squeeze(y)
        return np.argmax(q_values)

    def inferenceQValue(self, screens):
        y = self.sess.run([self.y], {self.x: screens})
        q_values = np.squeeze(y)
        return np.argmax(q_values), np.max(q_values)

    def train(self, batch, stepNumber, epochNumber, steps):

        self.batchesTrained = self.batchesTrained + 1
        self.batchesTrainedSave = self.batchesTrainedSave + 1

        x2 = [b.state2 for b in batch]
        y2 = self.y_target.eval(feed_dict={self.x_target: x2}, session=self.sess)

        x = [b.state1 for b in batch]
        a = np.zeros((len(batch), self.numActions))
        y_ = np.zeros(len(batch))

        for i in range(0, len(batch)):
            a[i, batch[i].action] = 1
            if batch[i].terminal:
                y_[i] = batch[i].reward
            else:
                y_[i] = batch[i].reward + gamma * np.max(y2[i])
            with open(qvalFile, 'a') as file:
                file.write(str(x[i]) + "\t" + str(x2[i]) + "\t" + str(batch[i].action) + "\t" + str(batch[i].reward) + "\t" + str(y_[i]) + "\n")

        self.train_step.run(feed_dict={
            self.x: x,
            self.a: a,
            self.y_: y_
        }, session=self.sess)

        if self.batchesTrained == self.targetModelUpdateFrequency:
            self.batchesTrained = 0
            self.sess.run(self.update_target)

        if self.batchesTrainedSave == self.saveFrequency and SAVING:
            print("SAVED MODEL !!!!")
            self.batchesTrainedSave = 0
            dir = self.baseDir + '/cnn_noise'
            if not os.path.isdir(dir):
                os.makedirs(dir)
            number = stepNumber + epochNumber*steps
            savedPath = self.saver.save(self.sess, dir + '/00006d98eSpeedmodel', global_step=number)

    def save(self, i):
        print("SAVED MODEL !!!!")
        self.batchesTrainedSave = 0
        dir = self.baseDir + '/cnn_noise'
        if not os.path.isdir(dir):
            os.makedirs(dir)
        savedPath = self.saver.save(self.sess, dir + '/scaledmodeleSPeed00006d98', global_step=i)
