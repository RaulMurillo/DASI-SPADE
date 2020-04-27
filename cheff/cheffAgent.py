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
import csv

import os
dirname = os.path.dirname(__file__)
CNN_DIR = os.path.join('imageClassifier', 'dnn')
CHEFF_DIR = os.path.join(dirname, '')

CHAT_JID = 'akjncakj@616.pub'


class SenderAgent(Agent):
    """Agent for testing `CheffAgent`
    Sends messages to `CheffAgent`.
    """

    class SendBehav(PeriodicBehaviour):
        async def on_start(self):
            self.counter = 0

        async def run(self):
            logging.debug("SendBehav running")

            msg = Message(to="cheff@localhost")     # Instantiate the message
            # Set the corresponding FIPA performative
            # http://www.fipa.org/specs/fipa00037/SC00037J.html
            if self.counter < 15:
                # A new ingredient is present
                msg.set_metadata("performative", "inform")
                # Set the message content
                msg.body = str(self.counter)
            elif self.counter < 16:
                # Add preferences
                msg.set_metadata("performative", "inform_ref")
                msg.body = str(13) + ',-100'

            else:
                # Start cooking
                msg.set_metadata("performative", "request")
                msg.body = 'Start cooking!'
                # msg.set_metadata("performative", "query_ref")
                # msg.body = str(3)

            # msg.body = f"Message {self.counter}"

            await self.send(msg)
            logging.info("[Sender] Message sent!")

            self.counter += 1
            if self.counter > 16:
                # stop agent from behaviour
                await self.agent.stop()

    async def setup(self):
        logging.info("SenderAgent started")
        b = self.SendBehav(period=0.1)
        self.add_behaviour(b)


class CheffAgent(Agent):

    def reset_list_ingred(self):
        """Restores the user list of ingredients."""

        self.list_ingred = lil_matrix((1, len(self.INGREDIENTS)), dtype=bool)

    class AddIngredBehaviour(CyclicBehaviour):
        async def on_start(self):
            logging.debug("AddIngredBehaviour starting . . .")
            pass

        async def on_end(self):
            pass

        async def run(self):
            logging.debug("AddIngredBehaviour running . . .")
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

    class PreferencesBehaviour(CyclicBehaviour):
        async def on_start(self):
            logging.debug("PreferencesBehaviour starting . . .")

            prefs_file = os.path.join(CHEFF_DIR, 'prefs.npz')
            if os.path.isfile(prefs_file):
                logging.debug("Preferences file exist")

                self.agent.preferences = sp.sparse.load_npz(
                    prefs_file)  # Expected np.int8 type
                assert self.agent.preferences.dtype == np.int8
                assert self.agent.preferences.shape == (
                    1, len(self.agent.INGREDIENTS))
            else:
                logging.debug("Preferences file does not exist")

                self.agent.preferences = csc_matrix(
                    np.zeros((1, len(self.agent.INGREDIENTS)), dtype=np.int8)
                )
            pass

        async def on_end(self):
            save_prefs()
            pass

        def save_prefs(self):
            logging.info("[Preferences] Vector:\n{}".format(
                self.agent.preferences))
            sp.sparse.save_npz(os.path.join(
                CHEFF_DIR, 'prefs.npz'), self.agent.preferences)
            pass

        async def run(self):
            logging.debug("PreferencesBehaviour running . . .")
            # wait for a message for t seconds
            t = 10000
            msg = await self.receive(timeout=t)
            if msg:
                logging.info(
                    "[Preferences] Message received with content: {}".format(msg.body))
                # ingred, pref = msg.body.split(',')
                list_prefs=json.loads(msg.body)
                for d in list_prefs:
                    ingred = d['Ingredient']
                    pref = d['Value']
                    self.agent.preferences[0, ingred] = pref
                # logging.info(f"[Preferences]\n{self.agent.preferences}")
                self.save_prefs()
            else:
                logging.info(
                    f"[Preferences] Did not received any message after {t} seconds")
                # self.kill()
                # return

    class MissingBehaviour(CyclicBehaviour):
        """Behaviour for dealing with use case 2

        Receives a receipe identifier and checks which ingredients are missing 
        from the user ingredients list.
        """
        async def on_start(self):
            logging.debug("MissingBehaviour starting . . .")
            pass

        async def on_end(self):
            pass

        async def run(self):
            logging.debug("MissingBehaviour running . . .")
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
                # assert recipe.get_shape() == (1, len(self.agent.INGREDIENTS))

                missing = csc_matrix(recipe.multiply(csc_matrix(
                    np.logical_not(self.agent.list_ingred.toarray()))),
                    dtype=bool)

                b_list = missing.toarray()[0, :]
                logging.debug(b_list)

                m_list = [i for (i, v) in zip(self.agent.INGREDIENTS, b_list) if v]
                logging.info(m_list)

                # Notify chat/user
                msg = Message(to=CHAT_JID)
                msg.set_metadata("performative", "confirm")
                msg.body = json.dumps(m_list)
                await self.send(msg)

            else:
                logging.info(
                    f"[Missing] Did not received any message after {t} seconds")

    class CookBehaviour(CyclicBehaviour):

        async def on_start(self):
            logging.debug("CookBehaviour starting . . .")
            # self.ingreds_recipes = csc_matrix(
            #     np.load(os.path.join(CHEFF_DIR, 'recipes.npy')))
            with open(os.path.join(CHEFF_DIR, 'recipes.json'), 'r') as json_file:
                self.recipe_book = json.load(json_file)

            pass

        async def on_end(self):
            pass

        async def run(self):
            logging.debug("CookBehaviour running . . .")
            # wait for a message for t seconds
            t = 10000
            msg = await self.receive(timeout=t)
            if msg:
                logging.info(
                    "[Cook] Message received with content: {}".format(msg.body))
                logging.info("[Cook] Gonna start cooking...")

                logging.info(
                    f"[Cook] Ingredients list:\n{self.agent.list_ingred}")
                # Menu according user available ingredients
                menu_avail = csc_matrix(self.agent.list_ingred).dot(
                    self.agent.ingreds_recipes)
                logging.debug(menu_avail.get_shape())
                logging.info(f"[Cook] Available menu:\n{menu_avail}")
                # Menu according user preferences
                menu_pref = self.agent.preferences.dot(
                    self.agent.ingreds_recipes)
                logging.debug(menu_pref.get_shape())
                logging.info(f"[Cook] Preferred menu:\n{menu_pref}")

                menu = menu_avail.multiply(menu_avail + menu_pref)

                logging.info('[Cook] The recipe that best matches is: {}'.format(
                    self.recipe_book['Title'][menu.argmax()]))
                logging.debug(self.recipe_book['Ingredients'][menu.argmax()])
                logging.debug(self.recipe_book['Directions'][menu.argmax()])

                # Notify chat/user
                msg = Message(to=CHAT_JID)
                msg.set_metadata("performative", "confirm")
                msg.body = json.dumps(menu.toarray()[0, :].tolist())
                await self.send(msg)
                self.agent.reset_list_ingred()


            else:
                logging.info(
                    f"[Cook] Did not received any message after {t} seconds")

    async def setup(self):
        print('CHEFF')
        logging.info("Cheff Agent starting . . .")
        # Ingredients names
        with open(os.path.join(CNN_DIR, 'ingredients_es.csv'), 'r') as f: #classes
            self.INGREDIENTS = list(csv.reader(f))[0]
        logging.debug(self.INGREDIENTS)
        # User list of ingredients
        # self.list_ingred = lil_matrix((1, len(self.INGREDIENTS)), dtype=bool)
        self.reset_list_ingred()
        # Matrix of ingreds_recipes
        self.ingreds_recipes = csc_matrix(np.genfromtxt(os.path.join(
            CHEFF_DIR, 'ingreds_recipes.csv'), dtype=np.int8, delimiter=','))
        # # sp.sparse.save_npz(os.path.join(
        # #     CHEFF_DIR, 'ingreds_recipes'), self.ingreds_recipes)
        # self.ingreds_recipes = sp.sparse.load_npz(
        #     os.path.join(CHEFF_DIR, 'ingreds_recipes.npz'))  # Expected np.int8 type
        # assert self.ingreds_recipes.dtype == np.int8

        logging.debug(type(self.ingreds_recipes[0]))
        # User preferences on ingredients
        self.preferences = None

        i = self.AddIngredBehaviour()
        c = self.CookBehaviour()
        m = self.MissingBehaviour()
        p = self.PreferencesBehaviour()
        t_i = Template()
        t_i.set_metadata("performative", "inform")
        t_c = Template()
        t_c.set_metadata("performative", "request")
        t_m = Template()
        t_m.set_metadata("performative", "query_ref")
        t_p = Template()
        t_p.set_metadata("performative", "inform_ref")
        self.add_behaviour(i, t_i)
        self.add_behaviour(m, t_m)
        self.add_behaviour(c, t_c)
        self.add_behaviour(p, t_p)


if __name__ == "__main__":

    logging.basicConfig()
    logging.root.setLevel(logging.INFO)
    logging.basicConfig(level=logging.INFO)

    # a = CheffAgent("cheff@localhost", "user01")
    a = CheffAgent("dasi2020cheff@616.pub", "123456")
    
    future = a.start()
    future.result()  # Wait until the start method is finished

    # sender = SenderAgent("sender@localhost", "user01")
    # sender.start()

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break

    a.stop()
    # sender.stop()

    print("Agents finished")
    quit_spade()
