# SPADE modules
from spade.agent import Agent
from spade import quit_spade
from spade.behaviour import CyclicBehaviour, PeriodicBehaviour
from spade.message import Message
from spade.template import Template
import asyncio

import numpy as np
import json
import csv
from multiprocessing import Pipe
from pathlib import Path
import logging

try:
    from config import APP_CONFIG as CONFIG

    CHEFF_JID = CONFIG['CHEFF_JID']
    IMAGE_JID = CONFIG['IMAGE_JID']
    COMMON_DIR = CONFIG['COMMON_DIR']
except:
    logger.warning('Exception raised when importing config.')

    project_folder = Path(__file__).parent.absolute()
    COMMON_DIR = project_folder / 'common'
    CHEFF_JID = 'cheff@localhost'
    IMAGE_JID = 'image@localhost'


logger = logging.getLogger(__name__)


class ChatAgent(Agent):
    """Agent which interacts with the Telegram bot and other system agents."""

    def __init__(self, jid, password, verify_security=False, pipe=None):
        """Start the Agent.
        """
        super().__init__(jid, password, verify_security)
        self.pipe = pipe

    class DispatcherBehav(PeriodicBehaviour):
        async def on_start(self):
            """Executed when the behavior starts.
            """
            logger.info("Starting DispatcherBehav . . .")
            with open((COMMON_DIR / 'recipes.json'), 'r') as json_file:
                self.recipe_book = json.load(json_file)
            # self.counter = 0

        async def on_end(self):
            """Executed when the behavior ends.
            """
            logger.info("DispatcherBehav finished")
            self.agent.pipe.close()

        async def run(self):
            """Behavior main function. 
            Send messages to ChatAgent or ImageAgent.
            """
            logger.debug("DispatcherBehav running")
            if self.agent.pipe.poll():  # Avoid blocking thread
                bot_msg = self.agent.pipe.recv()  # Blocking
                logger.info(
                    "[DispatcherBehav] Received msg from DASI Bot: {}".format(bot_msg))
                assert type(bot_msg) == dict
                t = 10
                if 'Image' in bot_msg:
                    # Notify to ImageAgent
                    msg = Message(to=IMAGE_JID)
                    msg.set_metadata("performative", "request")
                    msg.body = bot_msg['Image']
                    await self.send(msg)

                    # Recive ImageAgent's response
                    response = await self.receive(timeout=3)
                    # Pass response to bot - notify to user
                    if response:
                        ingred = self.agent.INGREDIENTS[int(response.body)]
                        self.agent.pipe.send(ingred)
                    # else:
                    #     self.agent.pipe.send('Lo siento, el servidor tiene problemas. Prueba más tarde')
                elif 'CU-001' in bot_msg:
                    # Notify CheffAgent
                    msg = Message(to=CHEFF_JID)
                    msg.set_metadata("performative", "request")
                    msg.body = 'Start cooking!'
                    await self.send(msg)

                    # Recive cheff's response
                    response = await self.receive(timeout=t)
                    # Pass response to bot - notify to user
                    if response:
                        all_menus = np.array(json.loads(response.body))
                        if all_menus.max() > 0:
                            # # JSON with best recipe
                            # menu = {
                            #     'Title': self.recipe_book[all_menus.argmax()]['Title'],
                            #     'Ingredients': self.recipe_book[all_menus.argmax()]['Ingredients'],
                            #     'Directions': self.recipe_book[all_menus.argmax()]['Steps'],
                            # }
                            # List with 5 best recipes
                            menu = []
                            N = 5
                            best_menu = all_menus.argsort()[-N:][::-1]
                            for m in best_menu:
                                if all_menus[m] > 0:
                                    menu.append(self.recipe_book[m]['Title'])
                                else:
                                    break

                        else:
                            menu = None
                        self.agent.pipe.send(menu)
                    else:
                        self.agent.pipe.send(
                            'Lo siento, el servidor tiene problemas. Prueba más tarde')
                elif 'CU-002' in bot_msg:
                    # Notify cheff
                    msg = Message(to=CHEFF_JID)
                    msg.set_metadata("performative", "query_ref")
                    msg.body = str(
                        self.agent.RECIPES.index(bot_msg['CU-002'])
                        )
                    logger.info(f"[DispatcherBehav] {bot_msg['CU-002']} - {msg.body}")
                    await self.send(msg)

                    # Recive cheff's response
                    response = await self.receive(timeout=t)
                    # Pass response to bot - notify to user
                    if response:
                        lst = json.loads(response.body)
                        self.agent.pipe.send(lst)
                    else:
                        self.agent.pipe.send(
                            'Lo siento, el servidor tiene problemas. Prueba más tarde')
                elif 'CU-003' in bot_msg:
                    prefs = bot_msg['CU-003']
                    f = bot_msg['factor']
                    logger.info(
                        f'[DispatcherBehav] Message containing {len(prefs)} preferences')
                    logger.info(f'[DispatcherBehav] Factor of prefs is {f}')

                    msg = Message(to=CHEFF_JID)
                    msg.set_metadata("performative", "inform_ref")
                    v = -10 if f == 'GuardarAlergia' else 5
                    msgs = []
                    for i in prefs:
                        logger.info(i)
                        msgs.append(
                            {'Ingredient': self.agent.INGREDIENTS.index(i), 'Value': v})
                    msg.body = json.dumps(msgs)
                    await self.send(msg)
                    logger.info(
                        f"[DispatcherBehav] Message sent: {msg.body}")

                elif 'CU-004' in bot_msg:
                    choice = self.agent.RECIPES.index(bot_msg['CU-004'])

                    menu = {
                                'Title': self.recipe_book[choice]['Title'],
                                'Ingredients': self.recipe_book[choice]['Ingredients'],
                                'Directions': self.recipe_book[choice]['Steps'],
                            }
                    self.agent.pipe.send(menu)
                    
                else:   # bad message
                    logger.warning(
                        f'[DispatcherBehav] Message recived: {bot_msg}')
                    # self.kill()

    async def setup(self):
        """Executed when the agent starts.
        Read the ingredientes and recipes lists.
        """
        logger.info("ChatAgent starting . . .")
        logger.info(f"[ChatAgent] Connection mechanism: {self.pipe}")
        with open((COMMON_DIR / 'ingredients_es.csv'), 'r') as f:
            self.INGREDIENTS = list(csv.reader(f))[0]
        
        with open((COMMON_DIR / 'recipes.csv'), 'r') as f:
            self.RECIPES = list(csv.reader(f))[0]

        dispatch = self.DispatcherBehav(period=1.5)
        self.add_behaviour(dispatch)


if __name__ == "__main__":
    import time

    logging.basicConfig()
    logging.root.setLevel(logging.INFO)
    logging.basicConfig(level=logging.INFO)

    # creating a pipe
    parent_conn, child_conn = Pipe()

    chatAgent = ChatAgent("chat@localhost", "user01", pipe=parent_conn)

    future = chatAgent.start()
    future.result()

    print("Wait until user interrupts with ctrl+C")
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break
    chatAgent.stop()
    print("Agents finished")
    quit_spade()
