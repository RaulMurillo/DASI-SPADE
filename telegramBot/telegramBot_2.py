# SPADE libs
from functools import wraps
from multiprocessing import Process, Pipe
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
from telegram import ReplyKeyboardMarkup, ParseMode, ChatAction
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler, CallbackQueryHandler)


import csv
CNN_DIR = os.path.join('imageClassifier', 'dnn')

# messageAlergia = None
# messagePreferencia = None
# messageImage = None
# messageReceta = None


# class SenderAgent(Agent):

#     class SendBehav(PeriodicBehaviour):
#         async def on_start(self):
#             print("Starting behaviour . . .")

#         async def run(self):
#             logging.debug("SendBehav running")
#             print("SenderAgent running . . .")

#             global messageAlergia
#             global messagePreferencia
#             global messageImage
#             global messageReceta
#             print("Estado de messagePreferencia" + str(messagePreferencia))
#             if(messageAlergia != None):

#                 # "akjncakj1@616.pub")     # Instantiate the message
#                 msg = Message(to="dasi2020cheff@616.pub")
#                 # Alergia o Preferencia
#                 msg.set_metadata("performative", "inform_ref")
#                 # Set the message content
#                 # msg.body = str(messageAlergia)
#                 logging.info(f"[ALERGIAS] {str(messageAlergia)}")
#                 # for k in str(messageAlergia).split(','):
#                 #     msg.body = k + ',-10'
#                 #     await self.send(msg)

#                 msg.body = '8,-10'
#                 await self.send(msg)
#                 messageAlergia = None
#             elif(messagePreferencia != None):

#                 # Instantiate the message
#                 msg = Message(to="dasi2020cheff@616.pub")
#                 # Alergia o Preferencia
#                 msg.set_metadata("performative", "inform_ref")
#                 logging.info(f"[PREFERENCIAS] {str(messagePreferencia)}")
#                 # msg.body = str(messagePreferencia)
#                 msg.body = '20,5'
#                 await self.send(msg)
#                 messagePreferencia = None
#             elif(messageImage != None):

#                 # "akjncakj1@616.pub")
#                 msg = Message(to="dasi2020image@616.pub")
#                 # Start cooking
#                 msg.set_metadata("performative", "request")  # "inform_ref")
#                 msg.body = str(messageImage)
#                 await self.send(msg)
#                 messageImage = None
#             elif(messageReceta != None):

#                 msg = Message(to="akjncakj1@616.pub")
#                 # Start cooking
#                 msg.set_metadata("performative", "inform_ref")
#                 msg.body = str(messageReceta)
#                 await self.send(msg)
#                 messageReceta = None
#             else:
#                 print("Nothing to send")
#                 pass
#             pass
#             # await asyncio.sleep(1)

#     async def setup(self):
#         print("SenderAgent starting . . .")
#         b = self.SendBehav(period=1.0)
#         self.add_behaviour(b)


# class ReceiveAgent(Agent):
#     """Agent for testing
#     Receive message to this agent
#     """
#     class ReceiveAlergia(PeriodicBehaviour):
#         async def on_start(self):
#             print("Starting behaviour . . .")

#         async def run(self):
#             logging.debug("ReceivePref running")
#             t = 100
#             msg = await self.receive(timeout=t)
#             if msg:
#                 logging.info(
#                     "[Alergia] Message received with content: {}".format(msg.body))
#             else:
#                 logging.info(
#                     f"[Alergia] Did not receive any message after {t} seconds")
#                 # self.kill()
#                 return

#     class ReceiveFoto(PeriodicBehaviour):
#         async def on_start(self):
#             print("Starting behaviour . . .")

#         async def run(self):
#             logging.debug("ReceivePref running")
#             t = 10
#             msg = await self.receive(timeout=t)
#             if msg:
#                 logging.info(
#                     "[Foto] Message received with content: {}".format(msg.body))
#             else:
#                 logging.info(
#                     f"[Foto] Did not receive any message after {t} seconds")
#                 # self.kill()
#                 return
#             pass

#     class ReceivePref(PeriodicBehaviour):
#         async def on_start(self):
#             print("Starting behaviour . . .")

#         async def run(self):
#             logging.debug("ReceivePref running")
#             t = 100
#             msg = await self.receive(timeout=t)
#             if msg:
#                 print(
#                     "[Preferences] Message received with content: {}".format(msg.body))
#                 logging.info(
#                     "[Preferences] Message received with content: {}".format(msg.body))
#             else:
#                 print(
#                     "[Preferences] Did not receive any message after {t} seconds")
#                 logging.info(
#                     f"[Preferences] Did not receive any message after {t} seconds")
#                 return
#             pass

#     async def setup(self):
#         print("ReceiveAgent starting . . .")
#         b = self.ReceiveAlergia(period=0.1)
#         c = self.ReceiveFoto(period=0.1)
#         d = self.ReceivePref(period=0.1)
#         t_b = Template()
#         t_b.set_metadata("performative", "inform")
#         t_c = Template()
#         t_c.set_metadata("performative", "inform_ref")
#         t_d = Template()
#         t_d.set_metadata("performative", "request")
#         self.add_behaviour(b, t_b)
#         self.add_behaviour(c, t_c)
#         self.add_behaviour(d, t_d)

class Agent2(Agent):
    def __init__(self, jid, password, verify_security=False, pipe=None):
        super().__init__(jid, password, verify_security)
        self.pipe = pipe

    class MyBehav(CyclicBehaviour):
        async def on_start(self):
            print("[A2] Starting behaviour . . .")
            # self.counter = 0

        async def on_end(self):
            self.agent.pipe.close()

        async def run(self):
            msg = self.agent.pipe.recv()
            print("[A2] Received msg from DASI Bot: {}".format(msg))
            # self.counter += 1
            # await asyncio.sleep(1)
            if msg == '5':
                self.kill()

    async def setup(self):
        print("Agent2 starting . . .")
        print("My pipe is", self.pipe)
        b = self.MyBehav()
        self.add_behaviour(b)


## ---------------------------------- START DIALOGFLOW -----------------------------------------##
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# DialogFlow Credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'private_key.json'

DIALOGFLOW_PROJECT_ID = 'dasibot-pfrrfb'
DIALOGFLOW_LANGUAGE_CODE = 'es'
SESSION_ID = 'me'

photo_dir = os.path.join(os.getcwd(), 'uploads')


def call2dialogflow(input_text):
    # Init API
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(DIALOGFLOW_PROJECT_ID, SESSION_ID)
    text_input = dialogflow.types.TextInput(
        text=input_text, language_code=DIALOGFLOW_LANGUAGE_CODE)
    query_input = dialogflow.types.QueryInput(text=text_input)

    try:
        response = session_client.detect_intent(
            session=session, query_input=query_input)
    except InvalidArgument:
        raise Exception('Dialogflow request failed')

    r = {
        'fulfillment': response.query_result.fulfillment_text,
        'intent': response.query_result.intent.display_name,
    }
    # and (r['intent']!= 'Default Fallback Intent')
    if (response.query_result.all_required_params_present):
        # There is no need to ask again
        valorFields = None
        if(r['intent'] == "GuardarGusto") or (r['intent'] == "GuardarAlergia"):
            valorFields = "Ingredientes"
        elif(r['intent'] == "GuardarReceta"):
            valorFields = "Receta"
        else:
            # raise ValueError
            return r

        r['fields'] = response.query_result.parameters.fields[valorFields]
    else:
        logging.debug('[Dialogflow] - Missing required params')
    return r


## ---------------------------------- END DIALOGFLOW -------------------------------------------##
## ---------------------------------- START TELEGRAM -------------------------------------------##


def send_action(action):
    """Sends `action` while processing func command."""

    def decorator(func):
        @wraps(func)
        def command_func(update, context, *args, **kwargs):
            context.bot.send_chat_action(
                chat_id=update.effective_message.chat_id, action=action)
            return func(update, context,  *args, **kwargs)
        return command_func

    return decorator


def start_bot(conn):
    # State definitions for Telegram Bot
    (SELECTING_ACTION, ADD_RECIPE, ADD_PHOTO,
     ASK_CHEFF, ADD_PREFS) = map(chr, range(5))
    # Shortcut for ConversationHandler.END
    END = ConversationHandler.END

    # Different constants for this example
    (START_OVER, RECIPE, INTENT, FULFILLMENT, FIELDS) = map(chr, range(10, 15))

    with open(os.path.join(CNN_DIR, 'ingredients_es.csv'), 'r') as f:
        INGREDIENTS = list(csv.reader(f))[0]

    def start(update, context):
        """Select an action: query by recipes/ingredients or add preferences."""
        text = 'Puedo ayudarte a proponerte una receta con los ingredientes que me mandes en una imagen.\n' + \
            'Tambien puedes indicar tus preferencias y alergias.\n' + \
            'Selecciona la opción de que desees y pulsa <code>/exit</code> cuando hayas terminado\n\n'

        buttons = [['Quiero cocinar algo, pero no se me ocurre nada', 'Quiero preparar una receta concreta'],
                   ['Añadir preferencia', 'Añadir alergia'],
                   ['/exit']]
        keyboard = ReplyKeyboardMarkup(buttons, one_time_keyboard=True)

        # If we're starting over we don't need do send a new message
        if not context.user_data.get(START_OVER):
            update.message.reply_text(
                'Hola! Me llamo DASI-Chef Bot pero puedes llamarme Chef Bot.')
        update.message.reply_text(
            text=text, resize_keyboard=True, reply_markup=keyboard, parse_mode=ParseMode.HTML)

        # Clear Dialogflow context
        call2dialogflow('Hola DASI-Chef Bot')
        # Clear user context
        context.user_data.clear()
        context.user_data[START_OVER] = True
        return SELECTING_ACTION

    def display_info(update, context):
        """Show software user manual in GUI"""
        # TODO
        text = 'Información actualmente no disponible :('
        update.message.reply_text(text=text)
        return SELECTING_ACTION

    # TODO: ChatAgent
    def done(update, context):
        update.message.reply_text('Hasta la próxima!')
        conn.send({'Finish': None})

        context.user_data.clear()
        return ConversationHandler.END

    def error(update, context):
        """Log Errors caused by Updates."""
        logger.warning('Update "%s" caused error "%s"', update, context.error)

    def detect_intention(update, context):
        """Detect user's intention from input text."""
        # Use Dialogflow to detect user's intention (use case)
        response = call2dialogflow(update.message.text)
        # Store values
        try:
            context.user_data[FULFILLMENT] = response['fulfillment']
            context.user_data[INTENT] = response['intent']

            logging.info(f'INTENT: {context.user_data[INTENT]}')
        except KeyError:
            update.message.reply_text('Error with Dialogflow server')
            exit(1)

        try:
            context.user_data[FIELDS] = response['fields']

            logging.info(f'FIELDS: {context.user_data[FIELDS]}')
        except KeyError:
            logging.debug('No fields in Dialogflow response')

        if context.user_data[INTENT] == 'ConsultarPlatoAElaborar':  # CU01
            return adding_images(update, context)
        elif context.user_data[INTENT] == 'GuardarReceta':  # CU02
            return adding_recipe(update, context)
        elif (context.user_data[INTENT] == 'GuardarGusto') or (context.user_data[INTENT] == 'GuardarAlergia'):  # CU03
            return adding_prefs(update, context)
        # elif context.user_data[INTENT] == 'GuardarAlergia':
        #     return adding_allergies(update, context)
        else:
            # context.user_data[INTENT] == 'Default Fallback Intent'
            update.message.reply_text(context.user_data[FULFILLMENT])
            # context.user_data.clear()
            context.user_data[INTENT] = None

        return SELECTING_ACTION

    def adding_images(update, context):
        """Add the images of ingredients."""
        update.message.reply_text(context.user_data[FULFILLMENT])
        info_text = 'Introduce todas las fotos de los ingredientes que tengas.\n' + \
            'Avísame cuando hayas terminado de introducir fotos.\n'
        # 'Procura que aparezca un alimento por imagen.\n' + \
        keyboard = ReplyKeyboardMarkup(
            [['Ya!']], resize_keyboard=True, one_time_keyboard=True)
        update.message.reply_text(info_text, reply_markup=keyboard)

        return ADD_PHOTO

    @send_action(ChatAction.TYPING)
    def save_image(update, context):
        """Save the input images."""
        user = update.message.from_user
        photo_file = update.message.photo[-1].get_file()
        currentDT = datetime.datetime.now()

        # try:
        #     os.mkdir(photo_dir, )
        #     print("Directory ", photo_dir, " created")
        # except FileExistsError:
        #     print("Directory ", photo_dir, " already exists")
        photo_name = 'user_photo' + \
            currentDT.strftime("%Y-%m-%d-%H-%M-%S") + '.jpg'
        photo_path = os.path.join(photo_dir, photo_name)
        photo_file.download(photo_path)
        logger.info("Image of %s: %s", user.first_name, photo_name)

        logger.info("Image updated at %s", photo_path)

        conn.send({'Image': photo_path})

        # Receive answer from Chat Agent
        response = 'Foto recibida!'  # f'Uploaded image as {photo_name}!'
        if conn.poll(timeout=5):
            ingred = conn.recv()
            response = 'Veo que tienes ' + ingred.lower()
        update.message.reply_text(response)

        return ADD_PHOTO

    @send_action(ChatAction.TYPING)
    def get_cheff_response(update, context):
        # Send message to Chat Agent
        if not context.user_data.get(RECIPE):
            # CU-001
            conn.send({'CU-001': None})
        else:
            # CU-002
            conn.send({'CU-002': context.user_data.get(RECIPE)})
            # update.message.reply_text()

        # Receive answer from Chat Agent
        response = 'Lo siento, el servidor está teniendo problemas, Vuelve a probar más tarde'
        if conn.poll(timeout=5):
            r = conn.recv()
            if not context.user_data.get(RECIPE):
                # CU-001
                if (type(r) == dict):
                    update.message.reply_text(
                        'Te sugiero preparar {}'.format(r['Title']))
                    response = '<b><u>Ingredientes</u></b>'
                    for i in r['Ingredients']:
                        response += '\n\u2022 ' + i
                    response += '\n\n<b><u>Instrucciones</u></b>'
                    for n, i in enumerate(r['Directions']):
                        response += '\n' + str(n+1) + '. ' + i
                elif (r == None):
                    response = 'Lo siento, no hay recetas disponibles con lo que me has indicado'
            else:
                # CU-002
                if (type(r) == list):
                    if len(r):
                        ingred_list = ''
                        for i in r:
                            ingred_list += '\n\u2022 ' + i.capitalize()

                        response = 'Te faltan los siguientes ingredientes clave: ' + ingred_list
                    else:
                        response = f'¡Tienes todos los ingredientes clave para cocinar {context.user_data.get(RECIPE).to_lower()}!'
        update.message.reply_text(response, parse_mode=ParseMode.HTML)

    def stop_images(update, context):
        update.message.reply_text(
            'Genial! Voy a ver qué puedo hacer con todos estos ingredientes...')

        get_cheff_response(update, context)

        buttons = [['Sí', 'No']]
        keyboard = ReplyKeyboardMarkup(
            buttons, resize_keyboard=True, one_time_keyboard=True)

        update.message.reply_text(
            text='¿Quieres realizar alguna consulta más?', reply_markup=keyboard)
        context.user_data[START_OVER] = True

        return ASK_CHEFF

    def adding_recipe(update, context):
        """Add the recipe you would like to cook."""
        if FIELDS in context.user_data:
            # Recipe already introduced by the user
            return save_recipe(update, context)
        else:
            update.message.reply_text(context.user_data[FULFILLMENT])
            return ADD_RECIPE
        # Unreachable
        return END

    def save_recipe(update, context):
        """Save input for recipe and return to next state."""
        # Get recipe, if not introduced previously
        if FIELDS not in context.user_data:
            # Validate with Dialogflow
            response = call2dialogflow(update.message.text)

            try:
                context.user_data[FULFILLMENT] = response['fulfillment']
                # context.user_data[INTENT] = response['intent'] # Should be already set

                # logging.info(context.user_data[INTENT])
            except KeyError:
                update.message.reply_text('Error with Dialogflow server')
                exit(1)

            keyboard = ReplyKeyboardMarkup(
                [['salir']], resize_keyboard=True, one_time_keyboard=True)
            try:
                context.user_data[FIELDS] = response['fields']
                if len(context.user_data[FIELDS].list_value.values) > 1:
                    update.message.reply_text(
                        'Por favor, introduce una sola receta, o escribe \'salir\' para volver', reply_markup=keyboard)
                    return ADD_RECIPE
            except KeyError:
                update.message.reply_text(
                    'Lo siento, no conozco esa receta.\nPrueba con otra, o escribe \'salir\' para volver', reply_markup=keyboard)
                return ADD_RECIPE

        # Save recipe to cook
        context.user_data[RECIPE] = context.user_data[FIELDS].list_value.values[0].string_value
        context.user_data[FIELDS] = None
        logging.info(context.user_data[RECIPE])
        return adding_images(update, context)

    def adding_prefs(update, context):
        """Add likes or allergies to the system."""
        if FIELDS in context.user_data:
            # Allergies already introduced by the user
            return save_prefs(update, context)

        else:
            update.message.reply_text(context.user_data[FULFILLMENT])
            return ADD_PREFS
        return END  # Unreachable

    def save_prefs(update, context):
        """Save detected likes or allergies into system."""

        # Fake ingreds list
        # INGREDIENTS = ['AJO', 'JUDÍAS', 'PERA', 'LIMÓN', 'TOMATE']
        # Get ingredients, if not introduced previously
        if FIELDS not in context.user_data:
            # Validate with Dialogflow
            response = call2dialogflow(update.message.text)

            try:
                context.user_data[FULFILLMENT] = response['fulfillment']
                # context.user_data[INTENT] = response['intent'] # Should be already set
            except KeyError:
                update.message.reply_text('Error with Dialogflow server')
                exit(1)

            try:
                context.user_data[FIELDS] = response['fields']
            except KeyError:
                update.message.reply_text(
                    'Lo siento, no conozco ninguno de esos alimentos')
        # Save ingredients preferences
        if FIELDS in context.user_data:
            update.message.reply_text(context.user_data.get(FULFILLMENT))

            # Detect all possible ingreds in user message
            unknowns = []
            knowns = []
            for i in context.user_data[FIELDS].list_value.values:
                ingredient = i.string_value
                if ingredient not in INGREDIENTS:
                    unknowns.append(ingredient)
                else:
                    knowns.append(ingredient)
            # Pass ingredients to chat agent
            if len(knowns) > 0:
                # f = -10 if context.user_data[INTENT] == 'GuardarAlergia' else 5
                conn.send(
                    {'CU-003': knowns, 'factor': context.user_data.get(INTENT)})

            if len(unknowns) > 0:
                my_string = ', '.join(unknowns)
                update.message.reply_text(
                    f'Lo siento, no conozco estos alimentos: {my_string}.\nPrueba con otros.')
        # Ask for more ingredients or leave
        buttons = [['Sí', 'No']]
        keyboard = ReplyKeyboardMarkup(
            buttons, resize_keyboard=True, one_time_keyboard=True)

        prefs_text = 'que no puedas tomar' if context.user_data[
            INTENT] == 'GuardarAlergia' else 'que te guste especialmente'

        update.message.reply_text(
            f'¿Hay algún otro alimento {prefs_text}?', reply_markup=keyboard)
        # Next state's FULFILLMENT
        prefs_list = 'alergias' if context.user_data[INTENT] == 'GuardarAlergia' else 'preferencias'
        context.user_data[
            FULFILLMENT] = f'¿Qué más alimentos quieres introducir en tu lista de {prefs_list}?'
        context.user_data[START_OVER] = True
        context.user_data.pop(FIELDS, None)  # Delete fields
        return ADD_PREFS

    def telegramBot_main():
        # Create the Updater and pass it your bot's token.
        # Make sure to set use_context=True to use the new context based callbacks
        # Post version 12 this will no longer be necessary
        updater = Updater(
            "1109746327:AAEfk6ivUvhR23M6z1BBOHvKKb5pHHwSGlQ", use_context=True)
        # Get the dispatcher to register handlers
        dp = updater.dispatcher

        # Add conversation handler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],

            states={
                SELECTING_ACTION: [
                    CommandHandler('info', display_info),
                    CommandHandler('exit', done),
                    # MessageHandler(Filters.regex('^CU01$'), adding_images),
                    # MessageHandler(Filters.regex('^CU02$'), adding_recipe),
                    # MessageHandler(Filters.regex('^CU03A$'), adding_prefs),
                    # MessageHandler(Filters.regex('^CU03B$'), adding_prefs),
                    MessageHandler(Filters.text, detect_intention),
                ],
                ADD_RECIPE: [
                    MessageHandler(Filters.regex('^salir$'), start),
                    MessageHandler(Filters.text, save_recipe),
                ],
                ADD_PHOTO: [
                    MessageHandler(Filters.photo, save_image),
                    MessageHandler(Filters.text, stop_images),
                ],
                ASK_CHEFF: [
                    MessageHandler(Filters.regex(r'^[Ss][IiÍí]$'), start),
                    MessageHandler(Filters.regex(r'^[Nn][Oo]$'), done),
                ],
                ADD_PREFS: [
                    MessageHandler(Filters.regex(
                        r'^[Ss][IiÍí]$'), adding_prefs),
                    MessageHandler(Filters.regex(r'^[Nn][Oo]$'), start),
                    MessageHandler(Filters.text, save_prefs),
                ],
            },

            fallbacks=[
                CommandHandler('exit', done),
                MessageHandler(Filters.regex('^Finalizar$'), done),
            ]
        )

        dp.add_handler(conv_handler)

        # log all errors
        dp.add_error_handler(error)

        # Pictures folder
        if not os.path.exists(photo_dir):
            os.makedirs(photo_dir)

        # Start the Bot
        updater.start_polling()

        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        updater.idle()

    logging.debug(f'My connection is {conn}')
    telegramBot_main()
## ---------------------------------- END TELEGRAM -----------------------------------------------##


if __name__ == "__main__":

    logging.basicConfig()
    logging.root.setLevel(logging.INFO)
    logging.basicConfig(level=logging.INFO)

    # senderAgent = SenderAgent("akjncakj@616.pub", "123456")
    # future = senderAgent.start()
    # future.result()

    # receiver = ReceiveAgent("akjncakj1@616.pub", "123456")
    # receiver.start()

    # telegramBot_main()

    # creating a pipe
    parent_conn, child_conn = Pipe()
    p = Process(target=start_bot, args=(child_conn,))
    p.start()

    a2 = Agent2("a2@localhost", "user01", pipe=parent_conn)
    a2.start()

    print("Wait until user interrupts with ctrl+C")
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break
    # senderAgent.stop()
    # receiver.stop()
    a2.stop()
    logging.info("Agents finished")
    quit_spade()
