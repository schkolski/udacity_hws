# These are all the modules we'll be using later. Make sure you can import them
# before proceeding further.
from __future__ import print_function
import numpy as np
import tensorflow as tf
from six.moves import cPickle as pickle
from sklearn.linear_model import LogisticRegression

pickle_file = 'notMNIST.pickle'

with open(pickle_file, 'rb') as f:
    save = pickle.load(f)
    train_dataset = save['train_dataset']
    train_labels = save['train_labels']
    valid_dataset = save['valid_dataset']
    valid_labels = save['valid_labels']
    test_dataset = save['test_dataset']
    test_labels = save['test_labels']
    del save  # hint to help gc free up memory
    print('Training set', train_dataset.shape, train_labels.shape)
    print('Validation set', valid_dataset.shape, valid_labels.shape)
    print('Test set', test_dataset.shape, test_labels.shape)

image_size = 28
num_labels = 10

def reformat(dataset, labels):
    dataset = dataset.reshape((-1, image_size * image_size)).astype(np.float32)
    # Map 2 to [0.0, 1.0, 0.0 ...], 3 to [0.0, 0.0, 1.0 ...]
    labels = (np.arange(num_labels) == labels[:,None]).astype(np.float32)
    return dataset, labels
train_lbls, valid_lbls, test_lbls =train_labels[:], valid_labels[:], test_labels[:]
train_dataset, train_labels = reformat(train_dataset, train_labels)
valid_dataset, valid_labels = reformat(valid_dataset, valid_labels)
test_dataset, test_labels = reformat(test_dataset, test_labels)
print('Training set', train_dataset.shape, train_labels.shape)
print('Validation set', valid_dataset.shape, valid_labels.shape)
print('Test set', test_dataset.shape, test_labels.shape)


beta = 5e-4
batch_size = 128

graph = tf.Graph()
with graph.as_default():

    # Input data. For the training data, we use a placeholder that will be fed
    # at run time with a training minibatch.
    tf_train_dataset = tf.placeholder(tf.float32,
                                    shape=(batch_size, image_size * image_size))
    tf_train_labels = tf.placeholder(tf.float32, shape=(batch_size, num_labels))
    tf_valid_dataset = tf.constant(valid_dataset)
    tf_test_dataset = tf.constant(test_dataset)

    # Variables.
    weights1 = tf.Variable(
        tf.truncated_normal([image_size * image_size, 1024], stddev=np.sqrt(2.0 / (image_size * image_size))))
    biases1 = tf.Variable(tf.zeros([1024]))
    
    weights2 = tf.Variable(
        tf.truncated_normal([1024, 300], stddev=np.sqrt(2.0 / (1024 * 1024))))
    biases2 = tf.Variable(tf.zeros([300]))
    
    weights3 = tf.Variable(
        tf.truncated_normal([300, 50], stddev=np.sqrt(2.0 / (300 * 300))))
    biases3 = tf.Variable(tf.zeros([50]))
    
    out_layer = tf.Variable(
        tf.truncated_normal([50, num_labels], stddev=np.sqrt(2.0/ (50 * 50))))
    out_biases = tf.Variable(tf.zeros([num_labels]))
    
    hidden1 = tf.nn.relu(tf.matmul(tf_train_dataset, weights1) + biases1)
    hidden1 = tf.nn.dropout(hidden1, 0.8) * 1.25
    hidden2 = tf.nn.relu(tf.matmul(hidden1, weights2) + biases2)
    hidden2 = tf.nn.dropout(hidden2, 0.5) * 2.0
    hidden3 = tf.nn.relu(tf.matmul(hidden2, weights3) + biases3)
    hidden3 = tf.nn.dropout(hidden3, 0.8) * 1.25
    
    
    # Training computation.
    logits = tf.matmul(hidden3, out_layer) + out_biases
    loss = tf.reduce_mean(
        tf.nn.softmax_cross_entropy_with_logits(logits, tf_train_labels))
    loss += (tf.nn.l2_loss(weights1) + tf.nn.l2_loss(weights2) +
            tf.nn.l2_loss(weights3)) * beta
    
    # Optimizer.
    global_step = tf.Variable(0)  # count the number of steps taken.
    learning_rate = tf.train.exponential_decay(0.5, global_step, 4000, 0.65, staircase=True)
    optimizer = tf.train.GradientDescentOptimizer(learning_rate).minimize(loss, global_step=global_step)
    
    # Predictions for the training, validation, and test data.
    train_prediction = tf.nn.softmax(logits)
    
    hidden1v = tf.nn.relu(tf.matmul(tf_valid_dataset, weights1) + biases1)
    hidden2v = tf.nn.relu(tf.matmul(hidden1v, weights2) + biases2)
    hidden3v = tf.nn.relu(tf.matmul(hidden2v, weights3) + biases3)
    valid_prediction = tf.nn.softmax(tf.matmul(hidden3v, out_layer) + out_biases)
        
    hidden1t = tf.nn.relu(tf.matmul(tf_test_dataset, weights1) + biases1)
    hidden2t = tf.nn.relu(tf.matmul(hidden1t, weights2) + biases2)
    hidden3t = tf.nn.relu(tf.matmul(hidden2t, weights3) + biases3)
    test_prediction = tf.nn.softmax(tf.matmul(hidden3t, out_layer) + out_biases)
#     test_prediction = tf.nn.softmax(tf.matmul(tf_test_dataset, weights) + biases)

num_steps = 700001

with tf.Session(graph=graph) as session:
    tf.initialize_all_variables().run()
    print("Initialized")
    for step in range(num_steps):
        # Pick an offset within the training data, which has been randomized.
        # Note: we could use better randomization across epochs.
        offset = (step * batch_size) % (train_labels.shape[0] - batch_size)
        # Generate a minibatch.
        batch_data = train_dataset[offset:(offset + batch_size), :]
        batch_labels = train_labels[offset:(offset + batch_size), :]
        # Prepare a dictionary telling the session where to feed the minibatch.
        # The key of the dictionary is the placeholder node of the graph to be fed,
        # and the value is the numpy array to feed to it.
        feed_dict = {tf_train_dataset : batch_data, tf_train_labels : batch_labels}
        _, l, predictions = session.run(
          [optimizer, loss, train_prediction], feed_dict=feed_dict)
        if (step % 10000 == 0):
            print("Minibatch loss at step %d: %f" % (step, l))
            print("Minibatch accuracy: %.1f%%" % accuracy(predictions, batch_labels))
            print("Validation accuracy: %.1f%%" % accuracy(
                valid_prediction.eval(), valid_labels))
    print("Test accuracy: %.1f%%" % accuracy(test_prediction.eval(), test_labels))