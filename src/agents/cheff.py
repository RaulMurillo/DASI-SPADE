# SPADE modules
from spade.agent import Agent
from spade import quit_spade
from spade.behaviour import CyclicBehaviour, PeriodicBehaviour
from spade.message import Message
from spade.template import Template
import asyncio

import numpy as np
import scipy as sp
from scipy.sparse import csc_matrix, csr_matrix, lil_matrix
import json
import csv
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

try:
    from config import APP_CONFIG as CONFIG

    CHAT_JID = CONFIG['CHAT_JID']
    COMMON_DIR = CONFIG['COMMON_DIR']
except:
    logger.warning('Exception raised when importing config.')

    project_folder = Path(__file__).parent.absolute()
    COMMON_DIR = project_folder / 'common'
    CHAT_JID = 'chat@localhost'


class SenderAgent(Agent):
    """Agent for testing `CheffAgent`

    Sends messages to `CheffAgent`.
    """

    class SendBehav(PeriodicBehaviour):
        """SendBehav behavior is repeted periodic."""

        async def on_start(self):
            """Executed when the behavior starts."""

            logger.info("Starting SendBehav . . .")
            self.counter = 0

        async def run(self):
            """Behavior main function.

            Sends messages to `CheffAgent`.
            """

            logger.debug("SendBehav running")

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
            logger.info("[Sender] Message sent!")

            self.counter += 1
            if self.counter > 16:
                # stop agent from behaviour
                await self.agent.stop()

    async def setup(self):
        """Executed when the agent starts."""

        logger.info("SenderAgent started")
        b = self.SendBehav(period=0.1)
        self.add_behaviour(b)


class CheffAgent(Agent):
    """Agent for generating recommendations.

    Manages the comunication with other agents and analyzes the best choice of recipes.
    """

    def reset_list_ingred(self):
        """Restores the user list of ingredients."""

        self.list_ingred = lil_matrix((1, len(self.INGREDIENTS)), dtype=bool)

    class AddIngredBehaviour(CyclicBehaviour):
        """Includes an ingredient into user's list.

        AddIngredBehaviour behavior is repeted cyclically.        
        """
        async def on_start(self):
            """Executed when the behavior starts."""

            logger.info("AddIngredBehaviour starting . . .")
            pass

        async def on_end(self):
            """Executed when the behavior ends."""
            pass

        async def run(self):
            """Behavior main function. 

            Updates the ingredients list.
            """

            logger.debug("AddIngredBehaviour running . . .")
            # wait for a message for t seconds
            t = 10000
            msg = await self.receive(timeout=t)
            if msg:
                logger.info(
                    "[AddIngredBehaviour] Message received with content: {}".format(msg.body))
                self.agent.list_ingred[0, int(msg.body)] = True
                logger.info(self.agent.list_ingred)
            else:
                logger.info(
                    f"[AddIngredBehaviour] Did not received any message after {t} seconds")

    class PreferencesBehaviour(CyclicBehaviour):
        """Modifies user's preferences.

        PreferencesBehaviour behavior is repeted cyclically.        
        """
        async def on_start(self):
            """Executed when the behavior starts."""

            logger.info("PreferencesBehaviour starting . . .")

            prefs_file = COMMON_DIR / 'prefs.npz'
            if prefs_file.exists():
                logger.debug("Preferences file exist")

                self.agent.preferences = sp.sparse.load_npz(
                    prefs_file)  # Expected np.int8 type
                assert self.agent.preferences.dtype == np.int8
                assert self.agent.preferences.shape == (
                    1, len(self.agent.INGREDIENTS))
            else:
                logger.debug("Preferences file does not exist")

                self.agent.preferences = csc_matrix(
                    np.zeros((1, len(self.agent.INGREDIENTS)), dtype=np.int8)
                )
            pass

        def save_prefs(self):
            """Saves user preferences un disk."""

            logger.info("[PreferencesBehaviour] Vector:\n{}".format(
                self.agent.preferences))
            sp.sparse.save_npz(COMMON_DIR / 'prefs.npz',
                               self.agent.preferences)
            pass

        async def on_end(self):
            """Executed when the behavior ends."""

            save_prefs()
            pass

        async def run(self):
            """Behavior main function. 

            Updates the user preferences.
            """

            logger.debug("PreferencesBehaviour running . . .")
            # wait for a message for t seconds
            t = 10000
            msg = await self.receive(timeout=t)
            if msg:
                logger.info(
                    "[PreferencesBehaviour] Message received with content: {}".format(msg.body))
                # ingred, pref = msg.body.split(',')
                list_prefs = json.loads(msg.body)
                for d in list_prefs:
                    ingred = d['Ingredient']
                    pref = d['Value']
                    self.agent.preferences[0, ingred] = pref
                # logger.info(f"[Preferences]\n{self.agent.preferences}")
                self.save_prefs()
            else:
                logger.info(
                    f"[PreferencesBehaviour] Did not received any message after {t} seconds")
                # self.kill()
                # return

    class MissingBehaviour(CyclicBehaviour):
        """Behaviour for dealing with CU-002.

        Receives a receipe identifier and checks which ingredients are
        missing from the user ingredients list.
        """

        async def on_start(self):
            """Executed when the behavior starts."""

            logger.info("MissingBehaviour starting . . .")
            pass

        async def on_end(self):
            """Executed when the behavior ends."""

            pass

        async def run(self):
            """Behavior main function. 

            Checks which ingredients are missing.
            """

            logger.debug("MissingBehaviour running . . .")
            # wait for a message for t seconds
            t = 10000
            msg = await self.receive(timeout=t)
            if msg:
                logger.info(
                    "[MissingBehaviour] Message received with content: {}".format(msg.body))
                # TODO: Change presence notification
                recipe = self.agent.ingreds_recipes[:, int(
                    msg.body)].transpose()
                logger.debug(recipe.get_shape())
                # assert recipe.get_shape() == (1, len(self.agent.INGREDIENTS))

                missing = csc_matrix(recipe.multiply(csc_matrix(
                    np.logical_not(self.agent.list_ingred.toarray()))),
                    dtype=bool)

                b_list = missing.toarray()[0, :]
                logger.debug(b_list)

                m_list = [i for (i, v) in zip(
                    self.agent.INGREDIENTS, b_list) if v]
                logger.info(m_list)

                # Notify chat/user
                msg = Message(to=CHAT_JID)
                msg.set_metadata("performative", "confirm")
                msg.body = json.dumps(m_list)
                await self.send(msg)
                self.agent.reset_list_ingred()

            else:
                logger.info(
                    f"[MissingBehaviour] Did not received any message after {t} seconds")

    class CookBehaviour(CyclicBehaviour):
        """Behaviour for dealing with CU-001.

        Receives a list of ingredientes and checks which recipe fits better.
        """

        async def on_start(self):
            """Executed when the behavior starts."""

            logger.info("CookBehaviour starting . . .")
            with open((COMMON_DIR / 'recipes.json'), 'r') as json_file:
                self.recipe_book = json.load(json_file)

            pass

        async def on_end(self):
            """Executed when the behavior ends."""

            pass

        async def run(self):
            """Behavior main function. 

            Gets the recipe witch fits better with the user ingredients.
            """

            logger.debug("CookBehaviour running . . .")
            # wait for a message for t seconds
            t = 10000
            msg = await self.receive(timeout=t)
            if msg:
                logger.info(
                    "[CookBehaviour] Message received with content: {}".format(msg.body))
                logger.info("[CookBehaviour] Gonna start cooking...")

                logger.info(
                    f"[CookBehaviour] Ingredients list:\n{self.agent.list_ingred}")
                # Menu according user available ingredients
                menu_avail = csc_matrix(self.agent.list_ingred).dot(
                    self.agent.ingreds_recipes)
                logger.debug(menu_avail.get_shape())
                logger.info(f"[CookBehaviour] Available menu:\n{menu_avail}")
                # Menu according user preferences
                menu_pref = self.agent.preferences.dot(
                    self.agent.ingreds_recipes)
                logger.debug(menu_pref.get_shape())
                logger.info(f"[CookBehaviour] Preferred menu:\n{menu_pref}")

                menu = menu_avail.multiply(menu_avail + menu_pref)

                logger.info('[CookBehaviour] The recipe that best matches is: {}'.format(
                    self.recipe_book[menu.argmax()]['Title']))
                logger.debug(self.recipe_book[menu.argmax()]['Ingredients'])
                logger.debug(self.recipe_book[menu.argmax()]['Steps'])

                # Notify chat/user
                msg = Message(to=CHAT_JID)
                msg.set_metadata("performative", "confirm")
                msg.body = json.dumps(menu.toarray()[0, :].tolist())
                await self.send(msg)
                self.agent.reset_list_ingred()

            else:
                logger.info(
                    f"[CookBehaviour] Did not received any message after {t} seconds")

    async def setup(self):
        """Executed when the agent starts."""

        logger.info("CheffAgent starting . . .")
        # Ingredients names
        with open((COMMON_DIR / 'ingredients_es.csv'), 'r') as f:  # classes
            self.INGREDIENTS = list(csv.reader(f))[0]
        logger.debug(self.INGREDIENTS)
        # User list of ingredients
        # self.list_ingred = lil_matrix((1, len(self.INGREDIENTS)), dtype=bool)
        self.reset_list_ingred()
        # Matrix of ingreds_recipes
        self.ingreds_recipes = csc_matrix(np.genfromtxt(
            (COMMON_DIR / 'ingreds_recipes.csv'), dtype=np.int8, delimiter=','))
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
    import time

    logging.basicConfig()
    logging.root.setLevel(logging.INFO)
    logging.basicConfig(level=logging.INFO)

    cheff = CheffAgent("cheff@localhost", "user01")

    future = cheff.start()
    future.result()  # Wait until the start method is finished

    sender = SenderAgent("sender@localhost", "user01")
    sender.start()

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break

    cheff.stop()
    sender.stop()

    print("Agents finished")
    quit_spade()
