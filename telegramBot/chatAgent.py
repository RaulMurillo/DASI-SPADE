import time
import asyncio
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.behaviour import PeriodicBehaviour
from spade.behaviour import OneShotBehaviour
from spade.message import Message
from spade.template import Template
from spade import quit_spade

from multiprocessing import Pipe
import logging


# class ChatAgent(Agent):
#     def __init__(self, jid, password, verify_security=False, conn=None):
#         super().__init__(jid, password, verify_security)
#         self.conn = conn

#     class DispatcherBehav(CyclicBehaviour):

#         async def on_start(self):
#             print("[ChatAgent] Starting behaviour . . .")
#             # self.counter = 0

#         async def on_end(self):
#             # self.agent.conn.close()
#             pass

#         async def run(self):
#             #msg = self.agent.conn.recv()
#             msg = 1
#             print("[ChatAgent] Received msg from DASI Bot: {}".format(msg))
#             # self.counter += 1
#             await asyncio.sleep(1)
#             if msg == '5':
#                 self.kill()

#     async def setup(self):
#         logging.info("ChatAgent starting . . .")
#         logging.info("[ChatAgent] Connection mechanism:", self.conn)
#         dispatch = self.DispatcherBehav()
#         self.add_behaviour(dispatch)


class ChatAgent(Agent):
    def __init__(self, jid, password, verify_security=False, pipe=None):
        super().__init__(jid, password, verify_security)
        self.pipe = pipe

    class DispatcherBehav(CyclicBehaviour):
        async def on_start(self):
            logging.info("[ChatAgent] Starting behaviour . . .")
            # self.counter = 0

        async def on_end(self):
            self.agent.pipe.close()

        async def run(self):
            msg = self.agent.pipe.recv() # Blocking
            logging.info("[ChatAgent] Received msg from DASI Bot: {}".format(msg))
            assert type(msg) == dict
            # time.sleep(1)
            if 'Image' in msg:
                pass
            elif 'CU-001' in msg:
                self.agent.pipe.send('[CU-001] Obtener recetas')
            elif 'CU-002' in msg:
                self.agent.pipe.send('[CU-002] Obtener ingredientes restantes')
            elif 'CU-003' in msg:
                prefs = msg['CU-003']
                f = msg['factor']
                logging.info(f'[ChatAgent] Message containing {len(prefs)} preferences')
                logging.info(f'[ChatAgent] Factor of prefs is {f}')
            else:   # bad message
                self.kill()
            # self.counter += 1
            # await asyncio.sleep(1)
            # if msg == '5':
            #     self.kill()

    async def setup(self):
        logging.info("ChatAgent starting . . .")
        logging.info(f"[ChatAgent] Connection mechanism: {self.pipe}")
        dispatch = self.DispatcherBehav()
        self.add_behaviour(dispatch)

if __name__ == "__main__":

    logging.basicConfig()
    logging.root.setLevel(logging.INFO)
    logging.basicConfig(level=logging.INFO)

    # creating a pipe 
    parent_conn, child_conn = Pipe() 

    # chatAgent = ChatAgent("dasi2020chat@616.pub", "123456")
    chatAgent = ChatAgent("akjncakj@616.pub", "123456", pipe=parent_conn)

    future = chatAgent.start()
    future.result()

    print("Wait until user interrupts with ctrl+C")
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break
    chatAgent.stop()
    logging.info("Agents finished")
    quit_spade()
