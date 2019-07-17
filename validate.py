from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import tensorflow as tf
import numpy as np
import tensorflow.contrib.slim as slim
import argparse
from nets import nets_factory
from preprocessing import preprocessing_factory
import time
from data_processing import prepare_data
from data_processing import load_data
from model import predict_model
from data_processing import CLASS_NUM
SAVE_MODEL_PATH = './tmp_data/train_model.ckpt'
RES_v1_50_MODEL_PATH = './tmp_data/resnet_v1_50.ckpt'

#test model
def validate_model():
    data = prepare_data()
    #build graph
    with tf.Graph().as_default():
        image_preprocessing_fn = preprocessing_factory.get_preprocessing('resnet_v1_50', is_training=False)
        processed_image, score = load_data(data['val_image_names'],
                                              data['val_image_scores'],
                                              1,
                                              image_preprocessing_fn,
                                              128,
                                              False)
        score = tf.reshape(score, [-1, 1])

        logits = predict_model(processed_image, is_training=False)
        variables_to_use = slim.get_variables_to_restore()
        variables_restorer = tf.train.Saver(variables_to_use)
        #Loss
        with tf.name_scope('loss'):
            #MSE loss
            loss = tf.sqrt(tf.reduce_mean(tf.square(logits - score)))
 
        config = tf.ConfigProto()
        config.gpu_options.allow_growth = True

        with tf.Session(config=config) as sess:
            sess.run(tf.global_variables_initializer())
            sess.run(tf.local_variables_initializer())
            variables_restorer.restore(sess, SAVE_MODEL_PATH)

            coord = tf.train.Coordinator()
            threads = tf.train.start_queue_runners(coord=coord)
            sum_ls = 0.0
            steps = 0
            try:
                while not coord.should_stop():
                    ls = sess.run(loss)
                    sum_ls += ls
                    steps += 1

            except tf.errors.OutOfRangeError:
                print("Validating: mean loss %f"%( sum_ls / steps))
            finally:
                coord.request_stop()
            coord.join(threads)
    return sum_ls / steps