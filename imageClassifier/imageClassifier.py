import time
import asyncio
from spade.agent import Agent
from spade import quit_spade
import spade.behaviour
from spade.behaviour import CyclicBehaviour
from spade.behaviour import PeriodicBehaviour
from spade.behaviour import OneShotBehaviour
from spade.message import Message
from spade.template import Template
# from aioxmpp import PresenceState, PresenceShow
import csv

import numpy as np
import tensorflow as tf
import logging

import os
dirname = os.path.dirname(__file__)
CNN_DIR = os.path.join(dirname, 'dnn')

CHEFF_JID = 'dasi2020cheff@616.pub'
CHAT_JID = 'akjncakj@616.pub'


class SenderAgent(Agent):
    """Agent for testing `ImageAgent`

    Sends messages with image paths to `ImageAgent`. 
    """
    class SendBehav(PeriodicBehaviour):
        async def on_start(self):
            self.counter = 0
            self.imgs = ['IMG_20200321_181344.jpg', 'IMG_20200321_181528.jpg',
                         'IMG_20200322_193347.jpg', 'IMG_20200321_181521.jpg',
                         'IMG_20200321_181538.jpg', 'IMG_20200322_193356.jpg',
                         'IMG_20200321_181524.jpg', 'IMG_20200322_193316.jpg']

        async def run(self):
            print("SendBehav running")

            msg = Message(to="image01@localhost")     # Instantiate the message
            # Set the "request" FIPA performative
            msg.set_metadata("performative", "request")
            msg.body = os.path.join(CNN_DIR, 'test_imgs', self.imgs[self.counter]) # Set the message content
            # msg.body = f"Message {self.counter}"

            await self.send(msg)
            print("Message sent!")

            self.counter += 1
            if self.counter >= len(self.imgs):
                # stop agent from behaviour
                await self.agent.stop()

    async def setup(self):
        print("SenderAgent started")
        b = self.SendBehav(period=2)
        self.add_behaviour(b)


def decode_img(img):
    """Decodes an image according to the TF model specifications

    Returns a TensorFlow tensor of size `224x224x3` corresponding with the given `img`.
    """
    # convert the compressed string to a 3D uint8 tensor
    img = tf.image.decode_jpeg(img, channels=3)
    # Use `convert_image_dtype` to convert to floats in the [0,1] range.
    img = tf.image.convert_image_dtype(img, tf.float32)
    # resize the image to the desired size.
    return tf.image.resize(img, [224, 224])


class ImageAgent(Agent):

    class ClassifyBehaviour(CyclicBehaviour):
        async def on_start(self):
            print("Starting behaviour . . .")

            self.cnn_model = tf.keras.models.load_model(os.path.join(CNN_DIR, 'saved_model/my_model.h5'))

            # self.presence.approve_all=True
            # self.presence.set_presence(
            #                  state=PresenceState(True, PresenceShow.CHAT),  # available and interested in chatting
            #                  status="Waiting for messages...",
            #                  priority=2
            #                 )

        async def run(self):

            # print("Counter: {}".format(self.counter))
            # self.counter += 1
            # await asyncio.sleep(1)
            logging.info("ClassifyBehaviour running")
            t=10000

            # wait for a message for 10 seconds
            msg = await self.receive(timeout=t)
            # self.presence.set_available(show=PresenceShow.AWAY)
            if msg:
                print("Message received with content: {}".format(msg.body))
                img = tf.io.read_file(msg.body)
                img = decode_img(img)
                img = tf.expand_dims(img, axis=0)
                pred = self.cnn_model.predict_classes(img)[0]
                logging.info(f"Image is of class {self.agent.CLASS_NAMES[pred]}")

                msg = Message(to=CHAT_JID)
                # Send ingredient
                msg.body = str(pred)
                await self.send(msg)

                msg = Message(to=CHEFF_JID)
                # Send ingredient
                msg.set_metadata("performative", "inform")
                msg.body = str(pred)
                await self.send(msg)
            else:
                print("Did not received any message after 10 seconds")

            # stop agent from behaviour
            # await self.agent.stop()

            # self.presence.set_available(show=PresenceShow.CHAT)

        async def on_end(self):
            print("Behaviour finished")

    async def setup(self):
        print("Image Agent starting . . .")
        # Ingredients names
        with open(os.path.join(CNN_DIR, 'classes.csv'), 'r') as f:
            self.CLASS_NAMES = list(csv.reader(f))[0]

        # gpus = tf.config.experimental.list_physical_devices('GPU')
        # if gpus:
        #     try:
        #         # Currently, memory growth needs to be the same across GPUs
        #         for gpu in gpus:
        #             tf.config.experimental.set_memory_growth(gpu, True)
        #         logical_gpus = tf.config.experimental.list_logical_devices(
        #             'GPU')
        #         print(len(gpus), "Physical GPUs,", len(
        #             logical_gpus), "Logical GPUs")
        #     except RuntimeError as e:
        #         # Memory growth must be set before GPUs have been initialized
        #         print(e)

        b = self.ClassifyBehaviour()
        t = Template()
        t.set_metadata("performative", "request")
        self.add_behaviour(b, t)


if __name__ == "__main__":
    # imageagent = ImageAgent("image01@localhost", "user01")
    imageagent = ImageAgent("dasi2020image@616.pub", "123456")

    future = imageagent.start()
    future.result()  # Wait until the start method is finished

    # senderagent = SenderAgent("sender@localhost", "user01")
    # senderagent.start()

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break

    # senderagent.stop()
    imageagent.stop()

    print("Agents finished")
    quit_spade()
