# -*- coding: utf-8 -*-
# @Author: shubham
# @Date:   2016-05-20 11:27:32
# @Last Modified by:   shubham
# @Last Modified time: 2016-05-20 21:30:37

import cv2
import numpy as np
import tensorflow as tf
from random import random, randint
from game.FlappyBird import FlappyBird

# Global parameters
IMAGE_SIZE = 80
ACTIONS = 2
NFLAP = 0
FLAP = 1

# Network parameters
STRIDE_1 = 4
STRIDE_2 = 2
STRIDE_3 = 1
HIDDEN_1 = 32
HIDDEN_2 = 64
HIDDEN_3 = 64
HIDDEN_4 = 512
PATCH_SIZE_1 = 8
PATCH_SIZE_2 = 4
PATCH_SIZE_3 = 3

# Hyper parameters
HISTORY_LENGTH = 4
LEARNING_RATE = 1e-6
EPSILON = 0.1

# Deep Neural Network helper functions
def weight_variable(shape):
	initial = tf.truncated_normal(shape, stddev=0.1)
	return tf.Variable(initial)

def bias_variable(shape):
	initial = tf.constant(0.1, shape=shape)
	return tf.Variable(initial)

def conv2d(x, W, b, stride):
	return tf.nn.relu(tf.nn.conv2d(x, W, strides=[1, stride, stride, 1], padding='SAME') + b)

def max_pool_2x2(x):
	return tf.nn.max_pool(x, ksize=[1, 2, 2, 1],strides=[1, 2, 2, 1], padding='SAME')

def matmul(x, W, b):
	return tf.nn.relu(tf.matmul(x, W) + b)

def accuracy(predictions, labels):
	correct_prediction = tf.equal(tf.argmax(predictions, 1), tf.argmax(labels, 1))
	return tf.reduce_mean(tf.cast(correct_prediction, "float"))
	# return(100.0 * np.sum(np.argmax(predictions, 1) == np.argmax(labels, 1)) / predictions.shape[0])


# Image resize
def image_reshape(image_data, prev=None, first=False):
	image_data = cv2.cvtColor(cv2.resize(image_data, (80, 80)), cv2.COLOR_BGR2GRAY)
	_, image_data = cv2.threshold(image_data,1,255,cv2.THRESH_BINARY)
	
	if first:
		return np.stack((image_data, image_data, image_data, image_data), axis=2)
	else:
		image_data = np.reshape(image_data, (80, 80, 1))
		return np.append(image_data, prev[:, :, :3], axis=2)

# Create network
def create_network():
	
	weights = {
		'c1': weight_variable([PATCH_SIZE_1, PATCH_SIZE_1, HISTORY_LENGTH, HIDDEN_1]),
		'c2': weight_variable([PATCH_SIZE_2, PATCH_SIZE_2, HIDDEN_1,  HIDDEN_2]),
		'c3': weight_variable([PATCH_SIZE_3, PATCH_SIZE_3, HIDDEN_2,  HIDDEN_3]),
		'fc1': weight_variable([(5*5)*HIDDEN_3, HIDDEN_4]),
		'fc2': weight_variable([HIDDEN_4, ACTIONS])
	}
	
	biases = {
		'c1': bias_variable([HIDDEN_1]),
		'c2': bias_variable([HIDDEN_2]),
		'c3': bias_variable([HIDDEN_3]),
		'fc1': bias_variable([HIDDEN_4]),
		'fc2': bias_variable([ACTIONS])
	}

	# Input image
	image_data = tf.placeholder("float", shape=[None, IMAGE_SIZE, IMAGE_SIZE, HISTORY_LENGTH])
	
	# Convolution Layers and max-pooling
	conv_1 = conv2d(image_data, weights['c1'], biases['c1'], STRIDE_1)
	conv_1 = max_pool_2x2(conv_1)
	# conv_1 = tf.nn.dropout(conv_1, dropout)

	conv_2 = conv2d(conv_1, weights['c2'], biases['c2'], STRIDE_2)
	# conv_2 = max_pool_2x2(conv_2)
	# conv_2 = tf.nn.dropout(conv_2, dropout)

	conv_3 = conv2d(conv_2, weights['c3'], biases['c3'], STRIDE_3)
	# conv_3 = max_pool_2x2(conv_3)
	# conv_3 = tf.nn.dropout(conv_3, dropout)

	# Fully connected layer
	fcl_1 = tf.reshape(conv_3, [-1 ,(5*5)*HIDDEN_3])
	fcl_1 = matmul(fcl_1, weights['fc1'], biases['fc1'])
	# fcl_1 = tf.nn.dropout(fcl_1, dropout)

	# Output, actions prediction
	readout = tf.matmul(fcl_1, weights['fc2'])+ biases['fc2']
	return image_data, readout
 
# Form tensorflow graphs
def tfGraph():
	
	# tf Graph input
	a = tf.placeholder("float", [None, ACTIONS])
	y = tf.placeholder("float", [None])
		
	x, readout = create_network()
	readout_action = tf.reduce_sum(tf.mul(readout, a), reduction_indices = 1)
	cost = tf.reduce_mean(tf.square(y - readout_action))
		
	optimizer = tf.train.AdamOptimizer(LEARNING_RATE).minimize(cost)
	tf.initialize_all_variables().run()

	return x, readout, optimizer


def train_bird(image_data, readout, optimizer, session):
	
	
	# start game
	fbird = FlappyBird()
	
	a_t = np.zeros([ACTIONS])
	a_t[NFLAP] = 1
	s_t, r_t, terminal = fbird.flapOnce(a_t)
	s_t = image_reshape(s_t, first=True)
	
	while True:

		# choose an action with (1-epsilon) probability 

		a_t = np.zeros([ACTIONS])
		if random() < EPSILON:
			action_index = randint(NFLAP,FLAP)
		else:
			readout_t = readout.eval(feed_dict = {image_data: [s_t]})		
			action_index = np.argmax(readout_t)
		a_t[action_index] = 1
		
		print(readout_t)

		# perform the action
		s_t1, reward, terminal = fbird.flapOnce(a_t)
		s_t1 = image_reshape(s_t1, prev=s_t)
		print(s_t1)
		
		# s_t1 = cv2.cvtColor(cv2.resize(s_t1, (80, 80)), cv2.COLOR_BGR2GRAY)
		# ret, s_t1 = cv2.threshold(s_t1, 1, 255, cv2.THRESH_BINARY)
		# s_t1 = np.reshape(s_t1, (80, 80, 1))
		# #s_t1 = np.append(x_t1, s_t[:,:,1:], axis = 2)
		# s_t1 = np.append(s_t1, s_t[:, :, :3], axis=2)


		# if not s_t.tolist() == s_t1.tolist():
			# print(s_t.tolist() == s_t1.tolist())
		s_t = s_t1


def main():
	session = tf.InteractiveSession()
	image_data, readout, optimizer = tfGraph()
	train_bird(image_data, readout, optimizer, session)

if __name__ == '__main__':
	main()


