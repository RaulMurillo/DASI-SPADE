#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from agents import ChatAgent, ImageAgent, CheffAgent
from spade import quit_spade
import telegramBot
from config import APP_CONFIG as CONFIG
from multiprocessing import Process, Pipe
import time
import logging


def main():
    # Creating a pipe for bot-agent communication
    parent_conn, child_conn = Pipe()

    # Create and start agents
    # chatAgent = ChatAgent("dasi2020chat@616.pub", "123456")
    chat = ChatAgent(CONFIG['CHAT_JID'], CONFIG['CHAT_PASS'], pipe=parent_conn)
    cheff = CheffAgent(CONFIG['CHEFF_JID'], CONFIG['CHEFF_PASS'])
    image = ImageAgent(CONFIG['IMAGE_JID'], CONFIG['IMAGE_PASS'])

    f_img = image.start()
    f_chf = cheff.start()
    f_cht = chat.start()
    f_img.result()
    f_cht.result()
    f_chf.result()

    # Telegram Bot
    bot_process = Process(target=telegramBot.start_bot, args=(
        CONFIG['telegram_token'], child_conn,))
    bot_process.start()

    time.sleep(0.5)	# Assert message is displayed after logs
    print("\n---\nWait until user interrupts with ctrl+C\n")
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
    logging.root.setLevel(logging.INFO)
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    main()
