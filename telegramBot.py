from google.api_core.exceptions import InvalidArgument
from telegram import ReplyKeyboardMarkup, ParseMode, ChatAction
from telegram.ext import (Updater, CommandHandler,
                          MessageHandler, Filters, ConversationHandler)
from functools import wraps
from multiprocessing import Process, Pipe

import logging
import os
import dialogflow
import json
import datetime
import csv

try:
    from config import APP_CONFIG as CONFIG

    COMMON_DIR = CONFIG['COMMON_DIR']
    PHOTO_DIR = CONFIG['UPLOADS_DIR']
except:
    COMMON_DIR = os.path.join('common', '')
    PHOTO_DIR = os.path.join(os.getcwd(), 'uploads')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

## ---------------------------------- START DIALOGFLOW -----------------------------------------##


# DialogFlow Credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'private_key.json'

DIALOGFLOW_PROJECT_ID = 'dasibot-pfrrfb'
DIALOGFLOW_LANGUAGE_CODE = 'es'
SESSION_ID = 'me'


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
        logger.debug('[Dialogflow] - Missing required params')
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


def start_bot(token, conn):
    """Starts a Telegram Bot that pass messages to other process via `conn`."""

    # State definitions for Telegram Bot
    (SELECTING_ACTION, ADD_RECIPE, ADD_PHOTO,
     ASK_CHEFF, ADD_PREFS) = map(chr, range(5))
    # Shortcut for ConversationHandler.END
    END = ConversationHandler.END

    # Different constants for this example
    (START_OVER, RECIPE, INTENT, FULFILLMENT, FIELDS) = map(chr, range(10, 15))

    # List of ingredients available in the system
    with open(os.path.join(COMMON_DIR, 'ingredients_es.csv'), 'r') as f:
        INGREDIENTS = list(csv.reader(f))[0]

    # Pictures folder
    if not os.path.exists(PHOTO_DIR):
        os.makedirs(PHOTO_DIR)

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
            text=text, parse_mode=ParseMode.HTML, resize_keyboard=True, reply_markup=keyboard)

        # Clear Dialogflow context
        call2dialogflow('Hola DASI-Chef Bot')
        # Clear user context
        context.user_data.clear()
        context.user_data[START_OVER] = True
        return SELECTING_ACTION

    # TODO
    def display_info(update, context):
        """Show software user manual in GUI"""

        text = 'Información actualmente no disponible :('
        update.message.reply_text(text=text)
        return SELECTING_ACTION

    def done(update, context):
        """Closes user conversation."""

        update.message.reply_text('Hasta la próxima!')
        conn.send({'Finish': None})

        context.user_data.clear()
        return ConversationHandler.END

    def error(update, context):
        """Log Errors caused by Updates."""

        logger.error('Update "%s" caused error "%s"', update, context.error)

    def detect_intention(update, context):
        """Detects user's intention from input text."""

        # Use Dialogflow to detect user's intention (use case)
        response = call2dialogflow(update.message.text)
        # Store values
        try:
            context.user_data[FULFILLMENT] = response['fulfillment']
            context.user_data[INTENT] = response['intent']
            logger.info(f'INTENT: {context.user_data[INTENT]}')
        except KeyError:
            update.message.reply_text('Error with Dialogflow server')
            return error(update, context)

        try:
            context.user_data[FIELDS] = response['fields']
            logger.info(f'FIELDS: {context.user_data[FIELDS]}')
        except KeyError:
            logger.debug('No fields in Dialogflow response')
        # Check intention
        if context.user_data[INTENT] == 'ConsultarPlatoAElaborar':  # CU01
            return adding_images(update, context)
        elif context.user_data[INTENT] == 'GuardarReceta':  # CU02
            return adding_recipe(update, context)
        elif (context.user_data[INTENT] == 'GuardarGusto') or (context.user_data[INTENT] == 'GuardarAlergia'):  # CU03
            return adding_prefs(update, context)
        else:
            update.message.reply_text(context.user_data[FULFILLMENT])
            context.user_data[INTENT] = None

        return SELECTING_ACTION

    def adding_images(update, context):
        """Adds the images of ingredients."""

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
        """Saves the input images."""

        user = update.message.from_user
        photo_file = update.message.photo[-1].get_file()
        currentDT = datetime.datetime.now()

        photo_name = 'user_photo' + \
            currentDT.strftime("%Y-%m-%d-%H-%M-%S") + '.jpg'
        photo_path = os.path.join(PHOTO_DIR, photo_name)
        photo_file.download(photo_path)
        logger.debug("Image of %s: %s", user.first_name, photo_name)

        logger.debug("Image updated at %s", photo_path)

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
        """Sends data and receives according response.
           Uses the accesible pipe `conn` for sending/receiving messages.
        """

        # Send message to Chat Agent
        if not context.user_data.get(RECIPE):  # CU-001
            conn.send({'CU-001': None})
        else:   # CU-002
            conn.send({'CU-002': context.user_data.get(RECIPE)})

        # Receive answer from Chat Agent
        response = 'Lo siento, el servidor está teniendo problemas. Vuelve a probar más tarde'
        if conn.poll(timeout=5):
            r = conn.recv()
            if not context.user_data.get(RECIPE):  # CU-001
                if (type(r) == dict):
                    update.message.reply_text(
                        'Te sugiero preparar {}'.format(r['Title']))
                    # Full list of ingredients
                    response = '<b><u>Ingredientes</u></b>'
                    for i in r['Ingredients']:
                        response += '\n\u2022 ' + i
                    # Recipe instructions, step by step
                    response += '\n\n<b><u>Instrucciones</u></b>'
                    for n, i in enumerate(r['Directions']):
                        response += '\n' + str(n+1) + '. ' + i
                elif (r == None):
                    response = 'Lo siento, no hay recetas disponibles con lo que me has indicado'
            else:  # CU-002
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
        """Stops image reception and calls `get_cheff_response`."""

        update.message.reply_text(
            'Genial! Voy a ver qué puedo hacer con todos estos ingredientes...')

        get_cheff_response(update, context)
        # Ask for more interactions
        buttons = [['Sí', 'No']]
        keyboard = ReplyKeyboardMarkup(
            buttons, resize_keyboard=True, one_time_keyboard=True)

        update.message.reply_text(
            text='¿Quieres realizar alguna consulta más?', reply_markup=keyboard)
        context.user_data[START_OVER] = True

        return ASK_CHEFF

    def adding_recipe(update, context):
        """Adds the recipe you would like to cook."""

        if FIELDS in context.user_data:
            # Recipe already introduced by the user
            return save_recipe(update, context)
        else:
            update.message.reply_text(context.user_data[FULFILLMENT])
            return ADD_RECIPE
        # Unreachable
        return END

    def save_recipe(update, context):
        """Saves input for recipe and return to next state."""

        # Get recipe, if not introduced previously
        if FIELDS not in context.user_data:
            # Validate with Dialogflow
            response = call2dialogflow(update.message.text)

            try:
                context.user_data[FULFILLMENT] = response['fulfillment']
                # context.user_data[INTENT] = response['intent'] # Should be already set

                # logger.info(context.user_data[INTENT])
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
        logger.info(context.user_data[RECIPE])
        return adding_images(update, context)

    def adding_prefs(update, context):
        """Adds likes or allergies to the system."""

        if FIELDS in context.user_data:
            # Allergies already introduced by the user - skip this step
            return save_prefs(update, context)

        else:
            update.message.reply_text(context.user_data[FULFILLMENT])
            return ADD_PREFS
        return END  # Unreachable

    def save_prefs(update, context):
        """Saves detected likes or allergies into system."""

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

    def telegramBot_main(token):
        """Creates and launches the Telegram Bot."""

        # Create the Updater and pass it your bot's token.
        # Make sure to set use_context=True to use the new context based callbacks
        # Post version 12 this will no longer be necessary
        updater = Updater(
            token, use_context=True)
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

        # Start the Bot
        updater.start_polling()

        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        updater.idle()

    logger.debug(f'My connection is {conn}')
    telegramBot_main(token)
## ---------------------------------- END TELEGRAM -----------------------------------------------##


if __name__ == "__main__":

    logging.basicConfig()
    logging.root.setLevel(logging.INFO)
    logging.basicConfig(level=logging.INFO)

    # creating a pipe
    parent_conn, child_conn = Pipe()
    p = Process(target=start_bot, args=(child_conn,))
    p.start()
