import time
import asyncio
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.behaviour import PeriodicBehaviour
from spade.behaviour import OneShotBehaviour
from spade.message import Message
from spade.template import Template
from spade import quit_spade


import logging
import os
import dialogflow
import json
import datetime

from google.api_core.exceptions import InvalidArgument
from telegram import ReplyKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)

messageAlergia = None
messagePreferencia = None
messageImage = None
messageReceta = None


class SenderAgent(Agent):

    class SendBehav(PeriodicBehaviour):
        async def on_start(self):
            print("Starting behaviour . . .")

        async def run(self):
            logging.debug("SendBehav running")
            print("SenderAgent running . . .")

            global messageAlergia
            global messagePreferencia
            global messageImage
            global messageReceta
            print("Estado de messagePreferencia" + str(messagePreferencia))
            if(messageAlergia != None):

                # "akjncakj1@616.pub")     # Instantiate the message
                msg = Message(to="dasi2020cheff@616.pub")
                # Alergia o Preferencia
                msg.set_metadata("performative", "inform_ref")
                # Set the message content
                # msg.body = str(messageAlergia)
                logging.info(f"[ALERGIAS] {str(messageAlergia)}")
                # for k in str(messageAlergia).split(','):
                #     msg.body = k + ',-10'
                #     await self.send(msg)

                msg.body = '8,-10'
                await self.send(msg)
                messageAlergia = None
            elif(messagePreferencia != None):

                # Instantiate the message
                msg = Message(to="dasi2020cheff@616.pub")
                # Alergia o Preferencia
                msg.set_metadata("performative", "inform_ref")
                logging.info(f"[PREFERENCIAS] {str(messagePreferencia)}")
                # msg.body = str(messagePreferencia)
                msg.body = '20,5'
                await self.send(msg)
                messagePreferencia = None
            elif(messageImage != None):

                # "akjncakj1@616.pub")
                msg = Message(to="dasi2020image@616.pub")
                # Start cooking
                msg.set_metadata("performative", "request")  # "inform_ref")
                msg.body = str(messageImage)
                await self.send(msg)
                messageImage = None
            elif(messageReceta != None):

                msg = Message(to="akjncakj1@616.pub")
                # Start cooking
                msg.set_metadata("performative", "inform_ref")
                msg.body = str(messageReceta)
                await self.send(msg)
                messageReceta = None
            else:
                print("Nothing to send")
                pass
            pass
            # await asyncio.sleep(1)

    async def setup(self):
        print("SenderAgent starting . . .")
        b = self.SendBehav(period=1.0)
        self.add_behaviour(b)


class ReceiveAgent(Agent):
    """Agent for testing
    Receive message to this agent
    """
    class ReceiveAlergia(PeriodicBehaviour):
        async def on_start(self):
            print("Starting behaviour . . .")

        async def run(self):
            logging.debug("ReceivePref running")
            t = 100
            msg = await self.receive(timeout=t)
            if msg:
                logging.info(
                    "[Alergia] Message received with content: {}".format(msg.body))
            else:
                logging.info(
                    f"[Alergia] Did not receive any message after {t} seconds")
                # self.kill()
                return

    class ReceiveFoto(PeriodicBehaviour):
        async def on_start(self):
            print("Starting behaviour . . .")

        async def run(self):
            logging.debug("ReceivePref running")
            t = 10
            msg = await self.receive(timeout=t)
            if msg:
                logging.info(
                    "[Foto] Message received with content: {}".format(msg.body))
            else:
                logging.info(
                    f"[Foto] Did not receive any message after {t} seconds")
                # self.kill()
                return
            pass

    class ReceivePref(PeriodicBehaviour):
        async def on_start(self):
            print("Starting behaviour . . .")

        async def run(self):
            logging.debug("ReceivePref running")
            t = 100
            msg = await self.receive(timeout=t)
            if msg:
                print(
                    "[Preferences] Message received with content: {}".format(msg.body))
                logging.info(
                    "[Preferences] Message received with content: {}".format(msg.body))
            else:
                print(
                    "[Preferences] Did not receive any message after {t} seconds")
                logging.info(
                    f"[Preferences] Did not receive any message after {t} seconds")
                return
            pass

    async def setup(self):
        print("ReceiveAgent starting . . .")
        b = self.ReceiveAlergia(period=0.1)
        c = self.ReceiveFoto(period=0.1)
        d = self.ReceivePref(period=0.1)
        t_b = Template()
        t_b.set_metadata("performative", "inform")
        t_c = Template()
        t_c.set_metadata("performative", "inform_ref")
        t_d = Template()
        t_d.set_metadata("performative", "request")
        self.add_behaviour(b, t_b)
        self.add_behaviour(c, t_c)
        self.add_behaviour(d, t_d)


## ---------------------------------- START TELEGRAM -------------------------------------------##
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Telegram States
CHOOSING, TYPING_REPLY, PHOTO, TYPING_CHOICE = range(4)

reply_keyboard = [['Subir imagen', 'Tu receta'],
                  ['Preferencias', 'Alergias'],
                  ['Finalizar']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

# DialogFlow Credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'private_key.json'

DIALOGFLOW_PROJECT_ID = 'dasibot-pfrrfb'
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
    text_input = dialogflow.types.TextInput(
        text=text_to_be_analyzed, language_code=DIALOGFLOW_LANGUAGE_CODE)
    query_input = dialogflow.types.QueryInput(text=text_input)
    try:
        response = session_client.detect_intent(
            session=session, query_input=query_input)
    except InvalidArgument:
        raise

    print("Query text:", response.query_result.query_text)
    print("Detected intent:", response.query_result.intent.display_name)
    print("Detected intent confidence:",
          response.query_result.intent_detection_confidence)
    print("Fulfillment text:", response.query_result.fulfillment_text)
    print("Response:", response)
    global fulfillment
    global intent
    fulfillment = response.query_result.fulfillment_text
    intent = response.query_result.intent.display_name

# Llamada a DialogFlow que devuelve los fileds identificados


def callToDialogFlowFields(text):
    text_to_be_analyzed = text

    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(DIALOGFLOW_PROJECT_ID, SESSION_ID)
    text_input = dialogflow.types.TextInput(
        text=text_to_be_analyzed, language_code=DIALOGFLOW_LANGUAGE_CODE)
    query_input = dialogflow.types.QueryInput(text=text_input)
    try:
        response = session_client.detect_intent(
            session=session, query_input=query_input)
    except InvalidArgument:
        raise

    valorFields = None
    if(response.query_result.intent.display_name == "GuardarGusto"):
        valorFields = "Gustos"
    elif(response.query_result.intent.display_name == "GuardarAlergia"):
        valorFields = "Alergias"
    elif(response.query_result.intent.display_name == "GuardarReceta"):
        valorFields = "Receta"

    print("Response:", response)
    print("Query text:", response.query_result.query_text)
    print("Detected intent:", response.query_result.intent.display_name)
    print("Detected intent confidence:",
          response.query_result.intent_detection_confidence)
    print("Fulfillment text:", response.query_result.fulfillment_text)
    print("fields:",
          response.query_result.parameters.fields[valorFields].list_value.values[0].string_value)
    global fulfillment
    global intent
    fulfillment = response.query_result.fulfillment_text
    intent = response.query_result.intent.display_name
    print("TAMAÑO FILEDS:", len(
        response.query_result.parameters.fields[valorFields].list_value.values))
    all_fields_response = ""
    for x in range(0, len(response.query_result.parameters.fields[valorFields].list_value.values)):

        all_fields_response = all_fields_response + \
            response.query_result.parameters.fields[valorFields].list_value.values[x].string_value
        if(x+1 != len(response.query_result.parameters.fields[valorFields].list_value.values)):
            all_fields_response = all_fields_response + ", "
    print("callToDialogFlowFields return: " + all_fields_response)
    return str(all_fields_response)


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
    # Llamada a DialogFlow
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
    currentDT = datetime.datetime.now()
    photo_name = 'user_photo' + \
        currentDT.strftime("%Y-%m-%d-%H-%M-%S") + '.jpg'
    # TODO: save photos in propper folder
    photo_file.download(photo_name)
    logger.info("Image of %s: %s", user.first_name, photo_name)
    cwd = os.getcwd()
    global messageImage
    messageImage = cwd + "/" + photo_name
    logger.info("messageInfo updated to: %s", messageImage)
    text = "SendImage"
    callToDialogFlow(text)
    update.message.reply_text(fulfillment.format(
        text.lower()), reply_markup=markup)

    return CHOOSING


def received_information(update, context):
    user_data = context.user_data
    text = update.message.text
    print("Valor introducido:", text)
    # Llamada a DialogFlow
    fields = callToDialogFlowFields(text)
    print("FIELDS: " + fields)
    category = user_data['choice']
    user_data[category] = fields
    del user_data['choice']
    global intent
    if(intent == "GuardarGusto"):
        global messagePreferencia
        messagePreferencia = fields
    elif(intent == "GuardarAlergia"):
        global messageAlergia
        messageAlergia = fields
    elif(intent == "RecepcionImagen"):
        # No se hace nada, ya que el mensaje de Imagen se actualiza cuando se sube la imagen en funcion photo
        pass
    elif(intent == "GuardarReceta"):
        global messageReceta
        # TODO Terminar la parte de la receta
        messageReceta = fields
    #print("Mensaje: " + fulfillment)
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


def telegramBot_main():
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(
        "1109746327:AAEfk6ivUvhR23M6z1BBOHvKKb5pHHwSGlQ", use_context=True)
    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            CHOOSING: [MessageHandler(Filters.regex('^(Preferencias|Alergias|Tu receta)$'),
                                      regular_choice),
                       MessageHandler(Filters.regex('^Subir imagen$'),
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
## ---------------------------------- END TELEGRAM -----------------------------------------------##


if __name__ == "__main__":

    logging.basicConfig()
    logging.root.setLevel(logging.INFO)
    logging.basicConfig(level=logging.INFO)

    senderAgent = SenderAgent("akjncakj@616.pub", "123456")
    future = senderAgent.start()
    future.result()

    receiver = ReceiveAgent("akjncakj1@616.pub", "123456")
    receiver.start()

    telegramBot_main()
    print("Wait until user interrupts with ctrl+C")
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break
    senderAgent.stop()
    receiver.stop()
    logging.debug("[INFO] Agents finished")
    quit_spade()
