import tensorflow as tf
import numpy as np
import random
from ai.nn_constants import MOVING_INPUT, MOVING_HLAYER1, \
    MUTATION_RATE, MUTATION_RANGE, CROSS_OVER_RATE
x = tf.placeholder("float", [None, MOVING_INPUT])
flatten = np.ndarray.flatten

class MovingAgent:

    ID = 0

    def __init__(self, sess):
        self.sess = sess
        self.layer = None
        self.uid = MovingAgent.ID
        MovingAgent.ID += 1

    def copy(self):
        new_agent = MovingAgent(self.sess)
        new_agent.layer = tf.identity(self.layer)
        return new_agent

    def randomize(self):
        self.b1 = tf.Variable(tf.random_normal([MOVING_HLAYER1]))
        # self.b2 = tf.Variable(tf.random_normal([MOVING_HLAYER2]))
        self.b_out = tf.Variable(tf.random_normal([1]))

        self.h1 = tf.Variable(tf.random_normal([MOVING_INPUT, MOVING_HLAYER1]))
        # self.h2 = tf.Variable(tf.random_normal([MOVING_HLAYER1, MOVING_HLAYER2]))
        self.h_out = tf.Variable(tf.random_normal([MOVING_HLAYER1, 1]))
        self.build_layers()

    def build_layers(self):
        self.layer = tf.nn.sigmoid(tf.add(tf.matmul(x, self.h1), self.b1))
        # self.layer = tf.nn.sigmoid(tf.add(tf.matmul(self.layer, self.h2), self.b2))
        self.layer = tf.nn.sigmoid(tf.add(tf.matmul(self.layer, self.h_out), self.b_out))
        self.sess.run(tf.global_variables_initializer())

    def predict(self, array):
        return self.layer.eval(feed_dict={x:[array]}, session=self.sess)

    def get_weights(self):
        if not hasattr(self, "h1"):
            self.randomize()
        with self.sess.as_default():
            b1_weights = flatten(self.b1.eval())
            # b2_weights = flatten(self.b2.eval())
            b_out_weights = flatten(self.b_out.eval())
            h1_weights = flatten(self.h1.eval())
            # h2_weights = flatten(self.h2.eval())
            h_out_weights = flatten(self.h_out.eval())

        return np.concatenate((b1_weights, b_out_weights,
            h1_weights, h_out_weights))

    def set_weights(self, weights: list):
        if not hasattr(self, "h1"):
            self.randomize()
        # Read weights
        offset = 0
        b1_weights = weights[:MOVING_HLAYER1]
        offset += MOVING_HLAYER1
        # b2_weights = weights[offset:offset + MOVING_HLAYER2]
        # offset += MOVING_HLAYER2
        b_out_weights = weights[offset:offset + 1]
        offset += 1
        h1_weights = weights[offset: offset + MOVING_INPUT * MOVING_HLAYER1]
        offset += MOVING_INPUT * MOVING_HLAYER1
        # h2_weights = weights[offset: offset + MOVING_HLAYER1 * MOVING_HLAYER2]
        # offset += MOVING_HLAYER1 * MOVING_HLAYER2
        h_out_weights = weights[offset: offset + MOVING_HLAYER1]
        offset += MOVING_HLAYER1

        if len(weights) != offset:
            print(len(weights), offset)
            exit(1)

        # Set weights
        ops = [\
        self.h1.assign(np.reshape(h1_weights, (MOVING_INPUT, MOVING_HLAYER1))),
        # self.h2.assign(np.reshape(h2_weights, (MOVING_HLAYER1, MOVING_HLAYER2))),
        self.h_out.assign(np.reshape(h_out_weights, (MOVING_HLAYER1, 1))),

        # Set bias
        self.b1.assign(np.reshape(b1_weights, (MOVING_HLAYER1))),
        # self.b2.assign(np.reshape(b2_weights, (MOVING_HLAYER2))),
        self.b_out.assign(np.reshape(b_out_weights, (1)))]

        for op in ops:
            self.sess.run(op)
