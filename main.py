from telegramBot.chatAgent import ChatAgent
from telegramBot.telegramBot_2 import start_bot
from cheff.cheffAgent import CheffAgent
from imageClassifier.imageClassifier import ImageAgent
from spade import quit_spade

from multiprocessing import Process, Pipe
import logging
import time
import asyncio


if __name__ == "__main__":

    logging.basicConfig()
    logging.root.setLevel(logging.INFO)
    logging.basicConfig(level=logging.INFO)

    # def start_chat(conn):
    #     chatAgent = ChatAgent("akjncakj@616.pub", "123456", pipe=conn)
    #     chatAgent.start()


    # creating a pipe
    parent_conn, child_conn = Pipe()

    # chatAgent = ChatAgent("dasi2020chat@616.pub", "123456")
    chat = ChatAgent("akjncakj@616.pub", "123456", pipe=parent_conn)
    cheff = CheffAgent("dasi2020cheff@616.pub", "123456")
    image = ImageAgent("dasi2020image@616.pub", "123456")

    image.start()
    future = cheff.start()
    # future = chat.start()
    future.result()

    chat.start()
    # p2 = Process(target=start_chat, args=(parent_conn,))
    # p2.start()

    p = Process(target=start_bot, args=(child_conn,))
    p.start()

    print("Wait until user interrupts with ctrl+C")
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break
    chat.stop()
    cheff.stop()
    iamge.stop()
    logging.info("Agents finished")
    quit_spade()

