#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

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
import os
import dialogflow
import json

from google.api_core.exceptions import InvalidArgument
from telegram import ReplyKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Telegram States
CHOOSING, TYPING_REPLY, PHOTO, TYPING_CHOICE = range(4)

reply_keyboard = [['Quiero cocinar'],
                  ['Preferencias','Alergias'],
                  ['Finalizar']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

# DialogFlow Credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'private_key.json'

DIALOGFLOW_PROJECT_ID = 'PROJECT_ID'
DIALOGFLOW_LANGUAGE_CODE = 'es'
SESSION_ID = 'me'

# Valores respuesta DialogFlow
fulfillment = ""
intent = ""
fields = ""

# Llamada a DialogFlow sin fields
def callToDialogFlow(text):
    text_to_be_analyzed = text

    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(DIALOGFLOW_PROJECT_ID, SESSION_ID)
    text_input = dialogflow.types.TextInput(text=text_to_be_analyzed, language_code=DIALOGFLOW_LANGUAGE_CODE)
    query_input = dialogflow.types.QueryInput(text=text_input)
    try:
        response = session_client.detect_intent(session=session, query_input=query_input)
    except InvalidArgument:
        raise
    
    print("Query text:", response.query_result.query_text)
    print("Detected intent:", response.query_result.intent.display_name)
    print("Detected intent confidence:", response.query_result.intent_detection_confidence)
    print("Fulfillment text:", response.query_result.fulfillment_text)
    print("Response:", response)
    global fulfillment
    global intent
    fulfillment = response.query_result.fulfillment_text
    intent = response.query_result.intent.display_name

#Llamada a DialogFlow que devuelve los fileds identificados
def callToDialogFlowFields(text):
    text_to_be_analyzed = text

    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(DIALOGFLOW_PROJECT_ID, SESSION_ID)
    text_input = dialogflow.types.TextInput(text=text_to_be_analyzed, language_code=DIALOGFLOW_LANGUAGE_CODE)
    query_input = dialogflow.types.QueryInput(text=text_input)
    try:
        response = session_client.detect_intent(session=session, query_input=query_input)
    except InvalidArgument:
        raise

    valorFields = None
    if(response.query_result.intent.display_name == "GuardarGusto"):
        valorFields = "gustos"
    elif(response.query_result.intent.display_name == "GuardarAlergia"):
        valorFields = "Alergias"
    print("Query text:", response.query_result.query_text)
    print("Detected intent:", response.query_result.intent.display_name)
    print("Detected intent confidence:", response.query_result.intent_detection_confidence)
    print("Fulfillment text:", response.query_result.fulfillment_text)
    print("fields:", response.query_result.parameters.fields[valorFields].list_value.values[0].string_value)  
    print("Response:", response)
    global fulfillment
    global intent
    fulfillment = response.query_result.fulfillment_text
    intent = response.query_result.intent.display_name

    return response.query_result.parameters.fields[valorFields].list_value.values[0].string_value

def facts_to_str(user_data):
    facts = list()

    for key, value in user_data.items():
        facts.append('{} - {}'.format(key, value))

    return "\n".join(facts).join(['\n', '\n'])


def start(update, context):
    update.message.reply_text(
        'Hola! Me llamo DASIChef_bot pero puedes llamarme Chef_bot. '
        'Puedo ayudarte a proponerte una receta con los ingredientes que me mandes en una imagen. '
 	'Tambien puedes indicar tus preferencias y alergias. '
	'Selecciona la opción de que desees y pulsa finalizar cuando hayas terminado\n\n',
        reply_markup=markup)

    return CHOOSING


def regular_choice(update, context):
    text = update.message.text
    context.user_data['choice'] = text
    print("Valor seleccionado:", text)
    #Llamada a DialogFlow
    callToDialogFlow(text)
    global fulfillment
    update.message.reply_text(
        fulfillment.format(text.lower()))

    return TYPING_REPLY


def custom_choice(update, context):
    text = update.message.text
    callToDialogFlow(text)
    global fulfillment
    update.message.reply_text(
        fulfillment.format(text.lower()))

    return PHOTO

def photo(update, context):
    user = update.message.from_user
    photo_file = update.message.photo[-1].get_file()
    photo_file.download('user_photo.jpg')
    logger.info("Image of %s: %s", user.first_name, 'user_photo.jpg')
    text = "SendImage"
    callToDialogFlow(text)
    update.message.reply_text(fulfillment.format(text.lower()),reply_markup=markup)

    return CHOOSING

def received_information(update, context):
    user_data = context.user_data
    text = update.message.text
    print("Valor introducido:", text)
    #Llamada a DialogFlow
    filds = callToDialogFlowFields(text)

    category = user_data['choice']
    user_data[category] = filds
    del user_data['choice']

    update.message.reply_text(fulfillment.format(facts_to_str(user_data)),
                              reply_markup=markup)

    return CHOOSING


def done(update, context):
    user_data = context.user_data
    if 'choice' in user_data:
        del user_data['choice']

    update.message.reply_text("I learned these facts about you:"
                              "{}"
                              "Until next time!".format(facts_to_str(user_data)))

    user_data.clear()
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

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            CHOOSING: [MessageHandler(Filters.regex('^(Preferencias|Alergias)$'),
                                      regular_choice),
                        MessageHandler(Filters.regex('^Quiero cocinar$'),
                                      custom_choice)
                       ],
            PHOTO: [MessageHandler(Filters.photo,
                                           photo)
                            ],
            TYPING_REPLY: [MessageHandler(Filters.text,
                                          received_information),
                           ],
        },

        fallbacks=[MessageHandler(Filters.regex('^Finalizar$'), done)]
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
