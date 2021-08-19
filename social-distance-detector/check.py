# -*- coding: utf-8 -*-
"""
Created on Thu Jan 14 10:55:39 2021

@author: User
"""

import tensorflow as tf
if tf.test.gpu_device_name():
    print('Default GPU Device: {}'.format(tf.test.gpu_device_name()))
else:
    print("Please install GPU version of TF")


print('asdf')
print(tf.config.list_physical_devices('GPU'))