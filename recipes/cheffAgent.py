#!/usr/bin/env python
# -*- coding: UTF-8 -*-
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
import logging

import numpy as np
import scipy as sp
from scipy.sparse import csc_matrix
from scipy.sparse import csr_matrix
from scipy.sparse import lil_matrix
import json

import os
dirname = os.path.dirname(__file__)
CNN_DIR = os.path.join('imageClassifier', 'dnn')
CHEFF_DIR = os.path.join(dirname, '')


class SenderAgent(Agent):
    """Agent for testing `CheffAgent`
    Sends messages to `CheffAgent`.
    """
    class SendBehav(PeriodicBehaviour):
        async def on_start(self):
            self.counter = 1

        async def run(self):
            logging.debug("SendBehav running")

            msg = Message(to="cheff@localhost")     # Instantiate the message
            # Set the corresponding FIPA performative
            # http://www.fipa.org/specs/fipa00037/SC00037J.html
            if self.counter % 5:
                # A new ingredient is present
                msg.set_metadata("performative", "inform")
                # Set the message content
                msg.body = str(self.counter-1)
            else:
                # # Start cooking
                # msg.set_metadata("performative", "request")
                # # Set the message content
                # msg.body = 'Start cooking!'
                msg.set_metadata("performative", "query_ref")
                msg.body = str(3)

            # msg.body = f"Message {self.counter}"

            await self.send(msg)
            logging.info("[Sender] Message sent!")

            self.counter += 1
            if self.counter >= 6:
                # stop agent from behaviour
                await self.agent.stop()

    async def setup(self):
        logging.info("SenderAgent started")
        b = self.SendBehav(period=1)
        self.add_behaviour(b)


class CheffAgent(Agent):

    class AddIngredBehav(CyclicBehaviour):
        async def on_start(self):
            logging.debug("AddIngredBehav starting . . .")
            pass

        async def on_end(self):
            pass

        async def run(self):
            logging.debug("AddIngredBehav running . . .")
            # wait for a message for t seconds
            t = 10000
            msg = await self.receive(timeout=t)
            if msg:
                logging.info(
                    "[AddIngred] Message received with content: {}".format(msg.body))
                self.agent.list_ingred[0, int(msg.body)] = True
                logging.info(self.agent.list_ingred)
            else:
                logging.info(
                    f"[AddIngred] Did not received any message after {t} seconds")

    class MissingBehav(CyclicBehaviour):
        """Behaviour for dealing with use case 2

        Receives a receipe identifier and checks which ingredients are missing 
        from the user ingredients list.
        """
        async def on_start(self):
            logging.debug("Missing Behaviour starting . . .")
            pass

        async def on_end(self):
            pass

        async def run(self):
            logging.debug("Missing Behaviour running . . .")
            # wait for a message for t seconds
            t = 10000
            msg = await self.receive(timeout=t)
            if msg:
                logging.info(
                    "[Missing] Message received with content: {}".format(msg.body))
                # TODO: Change presence notification
                recipe = self.agent.ingreds_recipes[:, int(
                    msg.body)].transpose()
                logging.debug(recipe.get_shape())
                # assert recipe.get_shape() == (1, len(self.agent.CLASS_NAMES))

                missing = csc_matrix(recipe.multiply(csc_matrix(
                    np.logical_not(self.agent.list_ingred.toarray()))),
                    dtype=bool)

                logging.debug(missing.toarray()[0, :])
                logging.info(self.agent.CLASS_NAMES[missing.toarray()[0, :]])

            else:
                logging.info(
                    f"[Missing] Did not received any message after {t} seconds")

    class CookBehav(CyclicBehaviour):
        async def on_start(self):
            logging.debug("Cooking Behaviour starting . . .")
            # self.ingreds_recipes = csc_matrix(
            #     np.load(os.path.join(CHEFF_DIR, 'recipes.npy')))
            with open(os.path.join(CHEFF_DIR, 'recipes.json'), 'r') as json_file:
                self.recipe_book = json.load(json_file)

            pass

        async def on_end(self):
            pass

        async def run(self):
            logging.debug("Cooking Behaviour running . . .")
            # wait for a message for t seconds
            t = 10000
            msg = await self.receive(timeout=t)
            if msg:
                logging.info(
                    "[Cooking] Message received with content: {}".format(msg.body))
                logging.info("[Cooking] Gonna start cooking...")
                # TODO: Change presence notification

                logging.info(self.agent.list_ingred)

                menu = csc_matrix(self.agent.list_ingred).dot(
                    self.agent.ingreds_recipes)
                logging.debug(menu.get_shape())
                logging.info(menu)

                logging.info('The recipe that best matches is {}'.format(
                    self.recipe_book['Title'][menu.argmax()]))
                logging.info(self.recipe_book['Ingredients'][menu.argmax()])
                logging.info(self.recipe_book['Directions'][menu.argmax()])

            else:
                logging.info(
                    f"[Cooking] Did not received any message after {t} seconds")

    async def setup(self):
        logging.info("Cheff Agent starting . . .")
        # Ingredients names
        self.CLASS_NAMES = np.genfromtxt(
            os.path.join(CNN_DIR, 'classes.csv'), delimiter=',', dtype=str)
        # User list of ingredients
        self.list_ingred = lil_matrix((1, len(self.CLASS_NAMES)), dtype=bool)
        logging.debug(self.CLASS_NAMES)
        # Matrix of ingreds_recipes
        self.ingreds_recipes = csc_matrix(np.genfromtxt(os.path.join(
            CHEFF_DIR, 'ingreds_recipes.csv'), dtype=int, delimiter=','))
        logging.debug(type(self.ingreds_recipes[0]))
        # self.preferences = np.load(os.path.join(CHEFF_DIR, 'prefs.npy'))

        i = self.AddIngredBehav()
        c = self.CookBehav()
        m = self.MissingBehav()
        t_i = Template()
        t_i.set_metadata("performative", "inform")
        t_c = Template()
        t_c.set_metadata("performative", "request")
        t_m = Template()
        t_m.set_metadata("performative", "query_ref")
        self.add_behaviour(i, t_i)
        self.add_behaviour(m, t_m)
        self.add_behaviour(c, t_c)


if __name__ == "__main__":

    logging.basicConfig()
    logging.root.setLevel(logging.INFO)
    logging.basicConfig(level=logging.INFO)

    a = CheffAgent("cheff@localhost", "user01")
    a.start()

    sender = SenderAgent("sender@localhost", "user01")
    sender.start()

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break

    a.stop()
    sender.stop()

    print("Agents finished")
    quit_spade()
