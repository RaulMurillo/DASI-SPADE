#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 

"""
First, a few callback functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

PRE_REQUEST, REQUEST, PHOTO, LOCATION, PREFERENCIAS, ALERGIAS, FIN = range(7)


def start(update, context):
    reply_keyboard = [['Indicar preferencias', 'Peticion al Chef']]

    update.message.reply_text(
        'Hola! ME llamo DASIChef_bot pero puedes llamarme Chef_bot. '
        'Puedo ayudarte a decirte una receta con los ingredientes que tienes. '
        'Por cierto, escribe /cancel si quieres dejar de hablar conmigo.\n\n'
        'Pulsa una tecla para continuar')

    return PRE_REQUEST

def pre_request(update, context):
    user = update.message.from_user
    logger.info("Request for the user %s: %s", user.first_name, update.message.text)
    update.message.reply_text('Ya veo el que quieres hacer, '
                              'Que petición tienes para mi?, '
                              'Puedo proponerte platos para cocinar o preguntarme que ingredientes necesitas para un plato en concreto',
                              reply_markup=ReplyKeyboardRemove())

    return REQUEST


def request(update, context):
    user = update.message.from_user
    logger.info("Request for the user %s: %s", user.first_name, update.message.text)
    update.message.reply_text('Fantastico!, '
                              'Mandame una imagen para que pueda ver con que ingredientes cuentas.')

    return PHOTO

def photo(update, context):
    user = update.message.from_user
    photo_file = update.message.photo[-1].get_file()
    photo_file.download('user_photo.jpg')
    logger.info("Image of %s: %s", user.first_name, 'user_photo.jpg')
    update.message.reply_text('Una imagen explendida, Ya estoy identificando que se encuentra en ella. '
                              'Si quieres introducir alguna preferencia o alergeno, Introduce una tecla para continuar')

    return PREFERENCIAS


def skip_photo(update, context):
    user = update.message.from_user
    logger.info("User %s did not send a photo.", user.first_name)
    update.message.reply_text('No puedo ayudarte si no me mandas ninguna imagen! Ve a buscarla que aquí espero, '
                              'intenta no escribir /skip.')

    return PHOTO


def preferencias(update, context):
    user = update.message.from_user
    user_location = update.message.location
    logger.info("El usuario %s ha seleccionado: %s", user.first_name, update.message.text)
    update.message.reply_text('¿Que tipo de platos te gustan más? '
                              '¿Dulce o salados? Escribe /skip si no te decantas por ninguna')

    return ALERGIAS


def skip_preferencias(update, context):
    user = update.message.from_user
    logger.info("User %s did not send a location.", user.first_name)
    update.message.reply_text('You seem a bit paranoid! '
                              'At last, tell me something about yourself.')

    return ALERGIAS

def alergias(update, context):
    user = update.message.from_user
    user_location = update.message.location
    logger.info("El usuario %s ha introducido la preferencia: %s", user.first_name, update.message.text)
    update.message.reply_text('¡Oido cocina! Importante, ¿Eres alergico a algún alimento? '
                              'Escribe todos ellos o escribe /skip si puedes comer de todo')

    return FIN


def skip_alergias(update, context):
    user = update.message.from_user
    logger.info("User %s did not send a location.", user.first_name)
    update.message.reply_text('Perfecto, no tienes alergia a nada, Me alegro.')

    return FIN

def fin(update, context):
    user = update.message.from_user
    user_location = update.message.location
    logger.info("El usuario %s ha tiene alergia a: %s", user.first_name, update.message.text)
    update.message.reply_text('¡Listo! Información guardada. '
                              'Podemos volver a hablar cuando lo desees')

    return ConversationHandler.END


def cancel(update, context):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Bye! I hope we can talk again some day.',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater("TOKEN", use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            PRE_REQUEST: [MessageHandler(Filters.text, pre_request)],

            REQUEST: [MessageHandler(Filters.text, request)],

            PHOTO: [MessageHandler(Filters.photo, photo)],

            PREFERENCIAS: [MessageHandler(Filters.text, preferencias),
                       CommandHandler('skip', skip_preferencias)],

            ALERGIAS: [MessageHandler(Filters.text, alergias),
                       CommandHandler('skip', skip_alergias)],
            FIN: [MessageHandler(Filters.text, fin)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()