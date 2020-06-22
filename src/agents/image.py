# SPADE modules
from spade.agent import Agent
from spade import quit_spade
from spade.behaviour import CyclicBehaviour, PeriodicBehaviour
from spade.message import Message
from spade.template import Template
import asyncio

import numpy as np
import tensorflow as tf
import csv
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

try:
    from config import APP_CONFIG as CONFIG

    CHEFF_JID = CONFIG['CHEFF_JID']
    CHAT_JID = CONFIG['CHAT_JID']
    CNN_DIR = CONFIG['CNN_DIR']
except:
    logger.warning('Exception raised when importing config.')

    project_folder = Path(__file__).parent.absolute()
    CNN_DIR = project_folder / 'cnn_model'
    CHEFF_JID = 'cheff@localhost'
    CHAT_JID = 'chat@localhost'


class SenderAgent(Agent):
    """Agent for testing `ImageAgent`

    Sends messages with image paths to `ImageAgent`. 
    """

    class SendBehav(PeriodicBehaviour):
        """SendBehav behavior is repeted periodic."""

        async def on_start(self):
            """Executed when the behavior starts."""

            logger.info("Starting SendBehav . . .")
            self.counter = 0
            self.imgs = ['IMG_20200321_181344.jpg', 'IMG_20200321_181528.jpg',
                         'IMG_20200322_193347.jpg', 'IMG_20200321_181521.jpg',
                         'IMG_20200321_181538.jpg', 'IMG_20200322_193356.jpg',
                         'IMG_20200321_181524.jpg', 'IMG_20200322_193316.jpg']

        async def run(self):
            """Behavior main function. 

            Sends messages to `ImageAgent`.
            """

            logger.debug("SendBehav running")

            msg = Message(to="image01@localhost")     # Instantiate the message
            # Set the "request" FIPA performative
            msg.set_metadata("performative", "request")
            # Set the message content
            msg.body = str(CNN_DIR / 'test_imgs' / self.imgs[self.counter])

            await self.send(msg)
            logger.info("[SenderAgent - SendBehav] Message sent!")

            self.counter += 1
            if self.counter >= len(self.imgs):
                # stop agent from behaviour
                await self.agent.stop()

    async def setup(self):
        """Executed when the agent starts."""

        logger.info("SenderAgent starting . . .")
        b = self.SendBehav(period=2)
        self.add_behaviour(b)


def decode_img(img):
    """Decodes an image according to the TF model specifications.

    Parameters
    ----------
    img : str
        Image path.

    Returns
    -------
    tensor    
        a TensorFlow tensor of size `224x224x3` corresponding with the given `img`.
    """

    # Convert the compressed string to a 3D uint8 tensor
    img = tf.image.decode_jpeg(img, channels=3)
    # Use `convert_image_dtype` to convert to floats in the [0,1] range
    img = tf.image.convert_image_dtype(img, tf.float32)
    # Resize the image to the desired size
    h, w, _ = tf.shape(img).numpy()
    if h != w:  # Central cropping
        target_size = min(h, w)
        img = tf.image.resize_with_crop_or_pad(img, target_size, target_size)
    return tf.image.resize(img, [224, 224])


class ImageAgent(Agent):
    """Agent for cover CU-001 and CU-002.

    Passes the image to the CNN to classify it.
    """

    class ClassifyBehaviour(CyclicBehaviour):
        """Main behavior, which classifies food images.
        
        ClassifyBehaviour behavior is repeted cyclically.  
        """

        async def on_start(self):
            """Executed when the behavior starts."""

            logger.info("Starting ClassifyBehaviour . . .")

            self.cnn_model = tf.keras.models.load_model(
                CNN_DIR / 'saved_model' / 'my_model.h5')

        async def run(self):
            """Behavior main function. 

            Analyze the image on the CNN network to classify it.
            """

            logger.debug("ClassifyBehaviour running")
            t = 10000

            # wait for a message for t seconds
            msg = await self.receive(timeout=t)
            if msg:
                logger.info(
                    "[ClassifyBehaviour] Message received with content: {}".format(msg.body))
                img = tf.io.read_file(msg.body)
                img = decode_img(img)
                img = tf.expand_dims(img, axis=0)
                pred = self.cnn_model.predict_classes(img)[0]
                logger.info(
                    f"[ClassifyBehaviour] Image is of class {self.agent.CLASS_NAMES[pred]}")

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
                logger.info(
                    "[ClassifyBehaviour] Did not received any message after 10 seconds")

        # async def on_end(self):
        #     logger.info("ClassifyBehaviour finished")

    async def setup(self):
        """Executed when the agent starts."""

        logger.info("ImageAgent starting . . .")
        # Ingredients names
        with open((CNN_DIR / 'classes.csv'), 'r') as f:
            self.CLASS_NAMES = list(csv.reader(f))[0]

        # Uncomment if TensorFlow for GPU is enabled.
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
    import time

    logging.basicConfig()
    logging.root.setLevel(logging.INFO)
    logging.basicConfig(level=logging.INFO)

    imageagent = ImageAgent("image01@localhost", "user01")

    future = imageagent.start()
    future.result()  # Wait until the start method is finished

    senderagent = SenderAgent("sender@localhost", "user01")
    senderagent.start()

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break

    senderagent.stop()
    imageagent.stop()

    print("Agents finished")
    quit_spade()
