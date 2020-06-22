from telegram import ReplyKeyboardMarkup, ParseMode, ChatAction
from telegram.ext import (Updater, CommandHandler,
                          MessageHandler, Filters, ConversationHandler)
from functools import wraps
from google.api_core.exceptions import InvalidArgument
from multiprocessing import Process, Pipe

import os
import dialogflow
import json
import datetime
import csv
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

try:
    from config import APP_CONFIG as CONFIG

    COMMON_DIR = CONFIG['COMMON_DIR']
    PHOTO_DIR = CONFIG['UPLOADS_DIR']
    # DialogFlow Credentials
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CONFIG['DIALOGFLOW']['CREDENTIALS']
    PROJECT_ID = CONFIG['DIALOGFLOW']['PROJECT_ID']
    LANGUAGE_CODE = CONFIG['DIALOGFLOW']['LANGUAGE_CODE']
    SESSION_ID = CONFIG['DIALOGFLOW']['SESSION_ID']
except:
    logger.warning('Exception raised when importing config.')

    project_folder = Path(__file__).parent.absolute()
    COMMON_DIR = project_folder / 'common'
    PHOTO_DIR = project_folder / 'uploads'
    # DialogFlow Credentials
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = ''
    PROJECT_ID = ''
    LANGUAGE_CODE = ''
    SESSION_ID = ''


## ---------------------------------- START DIALOGFLOW -----------------------------------------##


def call2dialogflow(input_text):
    """Calls to Dialogflow API. Receives the text to analyze.

    Parameters
    ----------
    input_text : str
    	The text introduced by the user in the chat.

    Returns
    -------
	dict
		a dictionary with the fulfillment and the intent as keys.
    """

    # Init API
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(PROJECT_ID, SESSION_ID)
    text_input = dialogflow.types.TextInput(
        text=input_text, language_code=LANGUAGE_CODE)
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
        elif(r['intent'] == "GuardarReceta") or (r['intent'] == "MostrarReceta"):
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
    """Decorator for user's feedback while processing.

    Parameters
    ----------
    action : ChatAction
        Sends `action` while processing func command.
    """

    def decorator(func):
        @wraps(func)
        def command_func(update, context, *args, **kwargs):
            context.bot.send_chat_action(
                chat_id=update.effective_message.chat_id, action=action)
            return func(update, context,  *args, **kwargs)
        return command_func

    return decorator


def start_bot(token, conn):
    """Starts a Telegram Bot that pass messages to other process via `conn`.

    Parameters
    ----------
    token : str
        Bot token secret identifier.
    conn : Pipe
        One of the two connection objects returned by multiprocessing.Pipe().
    """

    # State definitions for Telegram Bot
    (SELECTING_ACTION, ADD_RECIPE, ADD_PHOTO,
     ASK_CHEFF, ADD_PREFS, SHOW_RECIPE, CONTINUE) = map(chr, range(7))
    # Shortcut for ConversationHandler.END
    END = ConversationHandler.END

    # Different constants for this example
    (START_OVER, RECIPE, INTENT, FULFILLMENT, FIELDS) = map(chr, range(10, 15))

    # List of ingredients available in the system
    with open((COMMON_DIR / 'ingredients_es.csv'), 'r') as f:
        INGREDIENTS = list(csv.reader(f))[0]

    # Pictures folder
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)

    def start(update, context):
        """Select an action: query by recipes/ingredients or add preferences.

        Parameters
        ----------
        update : dict
            Telegram internal state.
        context : dict
            Conversation internal state.

        Returns
        -------
            To SELECTING_ACTION state.
        """

        text = 'Puedo ayudarte a proponerte una receta con los ingredientes que me mandes en una imagen.\n' + \
            'Tambien puedes indicar tus preferencias y alergias.\n' + \
            'Selecciona la opción de que desees y escribe <code>/exit</code> cuando hayas terminado\n' + \
            'Si tienes alguna duda, introduce <code>/help</code> para más información. \n'

        buttons = [['/help'],
                   ['Recomíendame una receta',
                       'Quiero preparar una receta concreta'],
                   ['Añadir preferencia', 'Alimentos que prefiero no tomar'],
                   ['/start', '/exit']]
        keyboard = ReplyKeyboardMarkup(buttons, one_time_keyboard=True)

        # If we're starting over we don't need do send a new message
        if not context.user_data.get(START_OVER):
            update.message.reply_text(
                '¡Hola! Me llamo DASI-Chef Bot pero puedes llamarme Chef Bot ' +
                '\U0001F9D1\U0000200D\U0001F373'
            )
        update.message.reply_text(
            text=text, parse_mode=ParseMode.HTML, resize_keyboard=True, reply_markup=keyboard)

        # Clear Dialogflow context
        call2dialogflow('Hola DASI-Chef Bot')
        # Clear user context
        context.user_data.clear()
        context.user_data[START_OVER] = True
        return SELECTING_ACTION

    def display_info(update, context):
        """Shows software user manual in GUI.

        Parameters
        ----------
        update : dict
            Telegram internal state.
        context : dict
            Conversation internal state.

        Returns
        -------
            To SELECTING_ACTION state.
        """

        text = '<b><u>Información</u></b> \U00002139\n' + \
            'Este es el mensaje de ayuda del bot. A continuación te detallo lo que puedes hacer.\n' + \
            '1. Te puedo proponer un plato a elaborar en función de las imágenes que me envíes. Para seleccionar esta opción escribe <b><i>Quiero cocinar, pero no se me ocurre nada</i></b>.\n' + \
            '2. Me puedes decir una receta en concreto que te gustaría cocinar y te daré las pautas que necesitas para ayudarte en su elaboración. Para seleccionar esta opción puedes introducir <b><i>Quiero preparar una receta concreta</i></b>.\n' + \
            '3. Puedes actualizar tus preferencias, ya sea por gusto seleccionando <b><i>Añadir preferencia</i></b> o por intolerancia a algún alimento con la opción <b><i>Añadir alergia</i></b>.\n' + \
            'Una vez seleccionada una de las opciones previas sigue las indicaciones que se muestran en pantalla.\n' + \
            'Acuerdate de seleccionar la opción <code>/exit</code> cuando hayas terminado.\n' + \
            'Puedes volver a ver la sección de ayuda escribiendo <code>/help</code>\n\n' + \
            '<b>FAQs</b> \U0001F64B\U00002753\n' + \
            '1. ¿Que ocurre con las imagenes una vez que las mando al sistema? \n' + \
            '- Las imágenes enviadas al sistema son procesadas por una red neuronal entrenada con una gran variedad de alimentos.\n' + \
            '2. ¿Puedo cocinar cualquier receta? \n' + \
            '- El sistema solo ofrece las recetas que se han guardado en él, por lo que existe la posibilidad de que una receta en específico falte. Si quieres consultar las recetas disponibles, introduce <code>/recetas</code>.\n' + \
            '3. ¿Tengo que escribir el texto exactamente como se indica? \n' + \
            '- No, el bot es capaz de entenderte siguiendo una conversación natural. Por ejemplo, puedes probar a introducir tus gustos directamente escribiendo \"Me gusta mucho ...\" o \"Hoy quiero preparar ...\" para buscar una receta.\n'

        update.message.reply_text(
            text=text, parse_mode=ParseMode.HTML)
        return SELECTING_ACTION

    @send_action(ChatAction.TYPING)
    def display_recipes(update, context):
        """Shows list of recipes available in the system.

        Parameters
        ----------
        update : dict
            Telegram internal state
        context : dict
            Conversation internal state
        """

        # List of recipes available in the system
        with open((COMMON_DIR / 'recipes.csv'), 'r') as f:
            RECIPES = list(csv.reader(f))[0]

        text = "<b><u>Recetas disponibles</u></b>"

        for r in RECIPES:
            text += '\n\u2022 ' + r

        update.message.reply_text(
            text=text, parse_mode=ParseMode.HTML)

    def done(update, context):
        """Closes user conversation.

        Parameters
        ----------
        update : dict
            Telegram internal state.
        context : dict
            Conversation internal state.

        Returns
        -------
            To the END state of conversation.
        """

        update.message.reply_text('Hasta la próxima!')
        conn.send({'Finish': None})

        context.user_data.clear()
        return ConversationHandler.END

    def error(update, context):
        """Log Errors caused by Updates.

        Parameters
        ----------
        update : dict
            Telegram internal state.
        context : dict
            Conversation internal state.
        """

        logger.error('Update "%s" caused error "%s"', update, context.error)

    def ask_continue(update, context):
        """Ask the user if wishes to do more queries.

        Parameters
        ----------
        update : dict
            Telegram internal state.
        context : dict
            Conversation internal state.

        Returns
        -------
            To CONTINUE conversation state.
        """

        # Ask for more interactions
        buttons = [['Sí', 'No']]
        keyboard = ReplyKeyboardMarkup(
            buttons, resize_keyboard=True, one_time_keyboard=True)

        update.message.reply_text(
            text='¿Quieres realizar alguna otra consulta?', reply_markup=keyboard)

        return CONTINUE

    def detect_intention(update, context):
        """Detects user's intention from input text.

        Parameters
        ----------
        update : dict
            Telegram internal state.
        context : dict
            Conversation internal state.

         Returns
        -------
            To SELECTING_ACTION conversation state.
        """

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
        elif context.user_data[INTENT] == 'MostrarReceta':  # CU04
            return show_recipe(update, context)
        else:
            update.message.reply_text(context.user_data[FULFILLMENT])
            context.user_data[INTENT] = None

        return SELECTING_ACTION

    def adding_images(update, context):
        """Adds the images of ingredients.

        Parameters
        ----------
        update : dict
            Telegram internal state.
        context : dict
            Conversation internal state.

        Returns
        -------
            To ADD_PHOTO conversation state.
        """

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
        """Saves the input images.

        Parameters
        ----------
        update : dict
            Telegram internal state.
        context : dict
            Conversation internal state.

        Returns
        -------
            To ADD_PHOTO conversation state.
        """

        user = update.message.from_user
        photo_file = update.message.photo[-1].get_file()
        currentDT = datetime.datetime.now()

        photo_name = 'user_photo' + \
            currentDT.strftime("%Y-%m-%d-%H-%M-%S") + '.jpg'

        photo_path = PHOTO_DIR / photo_name
        photo_file.download(photo_path)
        logger.debug("Image of %s: %s", user.first_name, photo_name)

        logger.debug("Image updated at %s", photo_path)

        conn.send({'Image': str(photo_path)})

        # Receive answer from Chat Agent
        response = 'Foto recibida!'  # f'Uploaded image as {photo_name}!'
        if conn.poll(timeout=5):
            ingred = conn.recv()
            response = 'Veo que tienes ' + ingred.lower()
        update.message.reply_text(response)

        return ADD_PHOTO

    @send_action(ChatAction.TYPING)
    def get_cheff_response(update, context):
        """Stops image reception and calls `print_cheff_response`.

        Parameters
        ----------
        update : dict
            Telegram internal state.
        context : dict
            Conversation internal state.

        Returns
        -------
        print_cheff_response(update, context)
            The default cheff response.
        """

        update.message.reply_text(
            'Genial! Voy a ver qué puedo hacer con todos estos ingredientes...')

        return print_cheff_response(update, context)

    @send_action(ChatAction.TYPING)
    def print_cheff_response(update, context):
        """Sends data and receives according response.

        Parameters
        ----------
        update : dict
            Telegram internal state.
        context : dict
            Conversation internal state.

         Returns
        -------
            To ASK_CHEFF conversation state.
        """

        fail = True

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
                if (type(r) == list):
                    update.message.reply_text(
                        'Te sugiero preparar alguna de las siguientes recetas:')
                    # Full list of recommended recipes
                    response = ''
                    for i in r:
                        response += '\n\u2022 ' + i
                    fail = False
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
                    fail = False

        update.message.reply_text(response, parse_mode=ParseMode.HTML)

        if fail:
            return ask_continue(update, context)
        else:
            if not context.user_data.get(RECIPE):  # CU-001
                # update.message.reply_text(
                #     text='¿Quieres ver las intrucciones de esta receta?')
                msg = 'Mostrar receta'
                response = call2dialogflow(msg)
                # Store values
                try:
                    context.user_data[FULFILLMENT] = response['fulfillment']
                    context.user_data[INTENT] = response['intent']
                    assert context.user_data[INTENT] == 'MostrarReceta'
                    logger.info(f'INTENT: {context.user_data[INTENT]}')
                except KeyError:
                    update.message.reply_text('Error with Dialogflow server')
                    return error(update, context)

                update.message.reply_text(context.user_data[FULFILLMENT])

            else:  # CU-002
                # Ask for more interactions
                buttons = [['Sí', 'No']]
                keyboard = ReplyKeyboardMarkup(
                    buttons, resize_keyboard=True, one_time_keyboard=True)

                update.message.reply_text(
                    text='¿Quieres ver las intrucciones de esta receta?', reply_markup=keyboard)

            return ASK_CHEFF

    @send_action(ChatAction.TYPING)
    def show_recipe(update, context):
        """Asks agent about full recipe and shows it to user.

        Parameters
        ----------
        update : dict
            Telegram internal state.
        context : dict
            Conversation internal state.

        Returns
        -------
            To ask_continue(update, context) function.
        """

        # Send message to Chat Agent
        if not context.user_data.get(RECIPE):  # CU-001
            # TODO: Get recipe to ask cheff
            # Get recipe, if not introduced previously

            try:
                get_recipe(update, context)
            except:
                return SHOW_RECIPE

            if FIELDS in context.user_data:
                # Save recipe to cook
                context.user_data[RECIPE] = context.user_data[FIELDS].list_value.values[0].string_value
                context.user_data[FIELDS] = None
                logger.info(context.user_data[RECIPE])
            # return SHOW_RECIPE

        conn.send({'CU-004': context.user_data.get(RECIPE)})

        # Receive answer from Chat Agent
        response = 'Lo siento, el servidor está teniendo problemas. Vuelve a probar más tarde'
        if conn.poll(timeout=5):
            r = conn.recv()
            if (type(r) == dict):
                response = f'<b><u>{context.user_data.get(RECIPE)}</u></b>\n\n'
                # Full list of ingredients
                response += '<b><u>Ingredientes</u></b>'
                for i in r['Ingredients']:
                    response += '\n\u2022 ' + i
                # Recipe instructions, step by step
                response += '\n\n<b><u>Instrucciones</u></b>'
                for n, i in enumerate(r['Directions']):
                    response += '\n' + str(n+1) + '. ' + i
            elif (r == None):
                # Unreachable
                response = 'Lo siento, no hay recetas disponibles con lo que me has indicado'
        update.message.reply_text(response, parse_mode=ParseMode.HTML)

        return ask_continue(update, context)

    def adding_recipe(update, context):
        """Adds the recipe you would like to cook.

        Parameters
        ----------
        update : dict
            Telegram internal state.
        context : dict
            Conversation internal state.

        Returns
        -------
            To ADD_RECIPE conversation state.
        """

        if FIELDS in context.user_data:
            # Recipe already introduced by the user
            return save_recipe(update, context)
        else:
            update.message.reply_text(context.user_data[FULFILLMENT])
            return ADD_RECIPE
        # Unreachable
        return END

    def get_recipe(update, context):
        """Saves the recipe selected by user.

        Parameters
        ----------
        update : dict
            Telegram internal state.
        context : dict
            Conversation internal state.
        """

        # Validate with Dialogflow
        response = call2dialogflow(update.message.text)
        try:
            context.user_data[FULFILLMENT] = response['fulfillment']
            # context.user_data[INTENT] = response['intent'] # Should be already set

            logger.info(context.user_data[INTENT])
        except KeyError:
            update.message.reply_text('Error with Dialogflow server')
            exit(1)

        keyboard = ReplyKeyboardMarkup(
            [['salir']], resize_keyboard=True, one_time_keyboard=True)
        try:
            context.user_data[FIELDS] = response['fields']
            if len(context.user_data[FIELDS].list_value.values) > 1:
                update.message.reply_text(
                    'Por favor, introduce una sola receta, o escribe \'salir\' para volver',
                    reply_markup=keyboard
                )
                # return ADD_RECIPE
                raise ValueError
        except KeyError:
            update.message.reply_text(
                'Lo siento, no conozco esa receta.\n' +
                'Prueba con otra, o escribe \'salir\' para volver\n' +
                'Puedes cosultar las recetas con <code>/recetas</code>',
                reply_markup=keyboard, parse_mode=ParseMode.HTML
            )
            # return ADD_RECIPE
            raise ValueError

    def save_recipe(update, context):
        """Saves input for recipe and return to next state.

        Parameters
        ----------
        update : dict
            Telegram internal state.
        context : dict
            Conversation internal state.

        Returns
        -------
            To ADD_RECIPE conversation handler or
            to adding_images(update, context) function.
        """

        # Get recipe, if not introduced previously
        if FIELDS not in context.user_data:

            # # Validate with Dialogflow
            # response = call2dialogflow(update.message.text)

            # try:
            #     context.user_data[FULFILLMENT] = response['fulfillment']
            #     # context.user_data[INTENT] = response['intent'] # Should be already set

            #     # logger.info(context.user_data[INTENT])
            # except KeyError:
            #     update.message.reply_text('Error with Dialogflow server')
            #     exit(1)

            # keyboard = ReplyKeyboardMarkup(
            #     [['salir']], resize_keyboard=True, one_time_keyboard=True)
            # try:
            #     context.user_data[FIELDS] = response['fields']
            #     if len(context.user_data[FIELDS].list_value.values) > 1:
            #         update.message.reply_text(
            #             'Por favor, introduce una sola receta, o escribe \'salir\' para volver',
            #             reply_markup=keyboard
            #         )
            #         return ADD_RECIPE
            # except KeyError:
            #     update.message.reply_text(
            #         'Lo siento, no conozco esa receta.\n' +
            #         'Prueba con otra, o escribe \'salir\' para volver\n' +
            #         'Puedes cosultar las recetas con <code>/recetas</code>',
            #         reply_markup=keyboard, parse_mode=ParseMode.HTML
            #     )
            #     return ADD_RECIPE
            try:
                get_recipe(update, context)
            except:
                return ADD_RECIPE

        # Save recipe to cook
        context.user_data[RECIPE] = context.user_data[FIELDS].list_value.values[0].string_value
        context.user_data[FIELDS] = None
        logger.info(context.user_data[RECIPE])
        return adding_images(update, context)

    def adding_prefs(update, context):
        """Adds likes or allergies to the system.

        Parameters
        ----------
        update : dict
            Telegram internal state.
        context : dict
            Conversation internal state.

        Returns
        -------
            To ADD_PREFS conversation state.
        """

        if FIELDS in context.user_data:
            # Allergies already introduced by the user - skip this step
            return save_prefs(update, context)

        else:
            update.message.reply_text(context.user_data[FULFILLMENT])
            return ADD_PREFS
        return END  # Unreachable

    def save_prefs(update, context):
        """Saves detected likes or allergies into system.

        Parameters
        ----------
        update : dict
            Telegram internal state.
        context : dict
            Conversation internal state.

        Returns
        -------
            To ADD_PREFS conversation state.
        """

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
        """Creates and launches the Telegram Bot.

        Parameters
        ----------
        token : str
            Telegram secret token.
        """

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
                    CommandHandler('help', display_info),
                    CommandHandler('exit', done),
                    CommandHandler('recetas', display_recipes),
                    # MessageHandler(Filters.regex('^CU01$'), adding_images),
                    # MessageHandler(Filters.regex('^CU02$'), adding_recipe),
                    # MessageHandler(Filters.regex('^CU03A$'), adding_prefs),
                    # MessageHandler(Filters.regex('^CU03B$'), adding_prefs),
                    MessageHandler(Filters.text, detect_intention),
                ],
                ADD_RECIPE: [
                    CommandHandler('recetas', display_recipes),
                    MessageHandler(Filters.regex('^salir$'), start),
                    MessageHandler(Filters.text, save_recipe),
                ],
                ADD_PHOTO: [
                    MessageHandler(Filters.photo, save_image),
                    MessageHandler(Filters.text, get_cheff_response),
                ],
                ASK_CHEFF: [
                    MessageHandler(Filters.regex(
                        r'^(.*?(\b[Ss][IiÍí]\b)[^$]*)$'), show_recipe),
                    MessageHandler(Filters.regex(
                        r'^(.*?(\b[Nn][Oo]\b)[^$]*)$'), start),
                    MessageHandler(Filters.regex('^salir$'), start),
                    MessageHandler(Filters.text, show_recipe),
                ],
                SHOW_RECIPE: [
                    CommandHandler('recetas', display_recipes),
                    MessageHandler(Filters.regex('^salir$'), start),
                    # MessageHandler(Filters.regex(r'^[Ss][IiÍí]$'), start),
                    # MessageHandler(Filters.regex(r'^(.*?(\b[Nn][Oo]\b)[^$]*)$'), done),
                    MessageHandler(Filters.text, show_recipe),
                ],
                ADD_PREFS: [
                    MessageHandler(Filters.regex(
                        r'^(.*?(\b[Ss][IiÍí]\b)[^$]*)$'), adding_prefs),
                    MessageHandler(Filters.regex(
                        r'^(.*?(\b[Nn][Oo]\b)[^$]*)$'), start),
                    MessageHandler(Filters.text, save_prefs),
                ],
                CONTINUE: [
                    MessageHandler(Filters.regex(
                        r'^(.*?(\b[Ss][IiÍí]\b)[^$]*)$'), start),
                    MessageHandler(Filters.regex(
                        r'^(.*?(\b[Nn][Oo]\b)[^$]*)$'), done),
                ]
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
