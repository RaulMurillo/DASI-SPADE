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


import os
# dirname = os.path.dirname(__file__)
CNN_DIR = os.path.join('imageClassifier', 'dnn')


class CheffAgent(Agent):

    class AddIngredBehav(CyclicBehaviour):
        async def on_start(self):
            pass

        async def on_end(self):
            pass

        async def run(self):
            self.agent.count += 1
            time.sleep(0.5)

    class CookBehav(PeriodicBehaviour):
        async def on_start(self):
            # self.agent.count = 0
            self.receipes = csc_matrix(
                np.load(os.path.join(CHEFF_DIR, 'recipes.npy')))
            pass

        async def on_end(self):
            pass

        async def run(self):
            print(self.agent.count)

    async def setup(self):
        logging.info("Cheff Agent starting . . .")
        self.count = 0
        self.CLASS_NAMES = np.genfromtxt(
            os.path.join(CNN_DIR, 'classes.csv'), delimiter=',', dtype=str)
        self.list_ingred = csc_matrix((1, len(self.CLASS_NAMES)), dtype=int8)
        # self.preferences = np.load(os.path.join(CHEFF_DIR, 'prefs.npy'))

        i = self.AddIngredBehav()
        c = self.CookBehav(period=1)
        self.add_behaviour(c)
        self.add_behaviour(i)


if __name__ == "__main__":

    a = CheffAgent("cheff@localhost", "user01")
    a.start()

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break

    a.stop()

    print("Agents finished")
    quit_spade()
