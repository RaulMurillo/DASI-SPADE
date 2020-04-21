from telegramBot.chatAgent import ChatAgent
from telegramBot.telegramBot_2 import start_bot
from spade import quit_spade

from multiprocessing import Process, Pipe
import logging
import time
import asyncio


if __name__ == "__main__":

    logging.basicConfig()
    logging.root.setLevel(logging.INFO)
    logging.basicConfig(level=logging.INFO)

    # creating a pipe
    parent_conn, child_conn = Pipe()

    # chatAgent = ChatAgent("dasi2020chat@616.pub", "123456")
    chatAgent = ChatAgent("akjncakj@616.pub", "123456", pipe=parent_conn)

    p = Process(target=start_bot, args=(child_conn,))
    p.start()

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

