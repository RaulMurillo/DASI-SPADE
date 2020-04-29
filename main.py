#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from agents import ChatAgent, ImageAgent, CheffAgent
from spade import quit_spade
import telegramBot
from config import APP_CONFIG as CONFIG
from multiprocessing import Process, Pipe
import logging
import time


def main():
    # Creating a pipe for bot-agent communication
    parent_conn, child_conn = Pipe()

    # Create and start agents
    # chatAgent = ChatAgent("dasi2020chat@616.pub", "123456")
    chat = ChatAgent(CONFIG['CHAT_JID'], CONFIG['CHAT_PASS'], pipe=parent_conn)
    cheff = CheffAgent(CONFIG['CHEFF_JID'], CONFIG['CHEFF_PASS'])
    image = ImageAgent(CONFIG['IMAGE_JID'], CONFIG['IMAGE_PASS'])

    image.start()
    cheff.start()
    future = chat.start()
    future.result()

    # Telegram Bot
    bot_process = Process(target=telegramBot.start_bot, args=(
        CONFIG['telegram_token'], child_conn,))
    bot_process.start()

    print("Wait until user interrupts with ctrl+C")
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break
    chat.stop()
    cheff.stop()
    image.stop()
    logging.info("Agents finished")
    quit_spade()


if __name__ == "__main__":

    logging.basicConfig()
    logging.root.setLevel(logging.INFO)
    logging.basicConfig(level=logging.INFO)

    main()
