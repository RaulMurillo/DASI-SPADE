# -*- coding: utf-8 -*-

import numpy as np
# import matplotlib.pyplot as plt
import pathlib
import os
import time

# %matplotlib inline

# Commented out IPython magic to ensure Python compatibility.
# try:
#   # %tensorflow_version only exists in Colab.
# #   %tensorflow_version 2.x
# except Exception:
#   pass
import tensorflow as tf

gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        # Currently, memory growth needs to be the same across GPUs
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        logical_gpus = tf.config.experimental.list_logical_devices('GPU')
        print(len(gpus), "Physical GPUs,", len(logical_gpus), "Logical GPUs")
    except RuntimeError as e:
        # Memory growth must be set before GPUs have been initialized
        print(e)                                                                                    

print(tf.__version__)

model = tf.keras.models.load_model('saved_model/my_model.h5')

# Show the model architecture
model.summary()


def decode_img(img):
    # convert the compressed string to a 3D uint8 tensor
    img = tf.image.decode_jpeg(img, channels=3)
    # Use `convert_image_dtype` to convert to floats in the [0,1] range.
    img = tf.image.convert_image_dtype(img, tf.float32)
    # resize the image to the desired size.
    return tf.image.resize(img, [224,224])

N=8
imgs = np.empty((N,224,224,3))
directory = 'test_imgs'
for i, f in enumerate(os.listdir(directory)):#enumerate(['IMG_20200321_181344.jpg', 'IMG_20200321_181521.jpg', 'IMG_20200321_181528.jpg', 'IMG_20200321_181524.jpg', 'IMG_20200321_181538.jpg', 'IMG_20200322_193316.jpg', 'IMG_20200322_193347.jpg', 'IMG_20200322_193356.jpg']):
    if i >= N:
        break
    elif f.endswith(".jpg") or f.endswith(".jpeg") or f.endswith(".png"):
        # print(f)
        im_path = os.path.join(directory, f)
        img = tf.io.read_file(im_path)
        img = decode_img(img)
        # img = tf.image.rot90(tf.image.rot90(tf.image.rot90(img)))
        imgs[i]=img
    else:
        continue

CLASS_NAMES = np.genfromtxt('classes.csv', delimiter=',', dtype=str)
print(CLASS_NAMES, len(CLASS_NAMES))

tic = time.time()
c = model.predict(imgs)
toc = time.time()

print(c)
print(CLASS_NAMES[np.argmax(c, axis=1)])

print(f'Elapsed time: {toc-tic}')
