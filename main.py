import telebot
import userEvents
import pokemonEvents
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import random
import threading
from collections import Counter
import time
from pymongo import MongoClient
#import config
from logger_config import logger
from datetime import datetime
import pytz

# Environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
TOPIC_ID = int(os.getenv("TOPIC_ID", "0"))
MONGO_URI = os.getenv("MONGO_URI")
# Check if the environment variables are set correctly
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN no está configurado en las variables de entorno.")
if not CHANNEL_ID:
    raise ValueError("CHANNEL_ID no está configurado en las variables de entorno.")
if not TOPIC_ID:
    raise ValueError("TOPIC_ID no está configurado en las variables de entorno.")
if not MONGO_URI:
    raise ValueError("MONGO_URI no está configurada en las variables de entorno.")

# Connection to MongoDB Atlas
client = MongoClient(MONGO_URI)
db = client.get_database()
# Bot token, group_id and topic_id values
bot = telebot.TeleBot(TELEGRAM_TOKEN)
group_id = CHANNEL_ID
topic_id = TOPIC_ID
# Capture_timers should save the timers of all spawned pokemons
capture_timers = {}
# Capture spawned pokemons in the dictionary
spawned_pokemons = {}
# Capture spawned pokemons in the dictionary to prvent others users to get them
capture_locks = {}
# Dictionary to track last usage times for the spawn command
last_spawn_times = {}
spawn_cooldawn = 60  # Cooldown time in seconds
# Dictionary to track combats
ongoing_combats = {}
# Commands
commands=[
    {"command": "ayuda", "description": "Muestra la lista de comandos."},
    {"command": "captura", "description": "Muestra la probabilidad de captura de los Pokémones.)"},
    {"command": "capturados", "description": "Te muestra por privado una lista detallada de tus Pokémones."},
    {"command": "combate", "description": "Inicia un combate con un Pokémon aleatorio tuyo."},
    {"command": "iniciar", "description": "El bot saludará."},
    {"command": "jugadores", "description": "Muestra una lista con todos los jugadores del grupo."},
    {"command": "micoleccion", "description": "Muestra cuantos pokemones vas atrapando."},
    {"command": "mispokemones", "description": "Muestra cuantos pokemones tienes en total."},
    {"command": "mistitutlos", "description": "Muestra tus titulos con sus descripciones."},
    {"command": "perfil", "description": "Muestra tu perfil o el de algun otro jugador."},
    {"command": "pokedex", "description": "Muestra los datos de Pokémon a partir de su ID o Nombre."},
    {"command": "registrar", "description": "Registra tu nombre de usuario."},
    {"command": "spawn", "description": "Spawnea un Pokémon aleatorio."},
    {"command": "teelijo", "description": "Invoca uno de tus Pokémones de forma aleatoria.)"},
    {"command": "titulos", "description": "Muestra un listado de todos los titulos y como conseguirlos."},
    {"command": "yoteelijo", "description": "Invoca un Pokémon a partir de su ID o Nombre."}
]

# General functions
#----------------------------------------------------------------
# Generate an inline keyboard with a "Capture!" button
def generate_capture_button(pokemonId):
    markup = InlineKeyboardMarkup()
    button = InlineKeyboardButton("Capturar!", callback_data=f"capture:{pokemonId}")
    markup.add(button)
    return markup

# Function to check if the user exists
def checkUserExistence(username):
    if not username:
        msg_cd = bot.send_message(group_id, "\u26A0 No tienes un nombre de usuario en Telegram.",message_thread_id=topic_id)
        threading.Timer(5, lambda: bot.delete_message(chat_id=group_id, message_id=msg_cd.message_id)).start()
        return True
    if not userEvents.checkUserisRegistered(username):
        msg_cd = bot.send_message(group_id, "\u26A0 No estas registrado.",message_thread_id=topic_id)
        threading.Timer(5, lambda: bot.delete_message(chat_id=group_id, message_id=msg_cd.message_id)).start()
        return True
    return False

# Function to remove special chars to prevent errors with markdown
def escape_markdown(text):
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in escape_chars:
        text = text.replace(char, f"\\{char}")
    return text

# Function to get profile data using user_data from a user
def get_user_data(user_data):
    victories = user_data.get("victories", [])
    defeats = user_data.get("defeats", [])
    victories_text = ""
    if victories:
        for victory in victories:
            opponent = escape_markdown(str(victory["opponent"]))
            victories_text += f"\U0001F539 {opponent}: {victory['count']}\n"
    defeats_text = ""
    if defeats:
        for defeat in defeats:
            opponent = escape_markdown(str(defeat["opponent"]))
            defeats_text += f"\U0001F538 {opponent}: {defeat['count']}\n"
    total_victories = sum(entry["count"] for entry in victories) if victories else 0
    total_defeats = sum(entry["count"] for entry in defeats) if defeats else 0
    most_victories = max(victories, key=lambda x: x["count"])["opponent"] if victories else "Pacifista"
    most_defeats = max(defeats, key=lambda x: x["count"])["opponent"] if defeats else "Invicto"
    winrate = round((total_victories / (total_victories + total_defeats)) * 100, 2) if (total_victories + total_defeats) > 0 else 0
    titles = user_data.get("titles", [])
    titles_text = ""
    if len(titles) > 0:
        for title in titles:
            titles_text += f"\U0001F396 {title}\n"
    else:
        titles_text = "Aun no tienes títulos.\n"
    # Mensaje de respuesta
    profile_text = (
        f"\U0001F4DC *Perfil de {escape_markdown(user_data['name'])}*\n"
        f"\U0001F4E6 Pokémones Capturados: {user_data.get('total_pokemons', 0)}\n"
        f"\U0001F31F Shiny Capturados: {user_data.get('total_shiny', 0)}\n"
        f"\U0001F3AF Winrate: {winrate}%\n"
        f"\U0001F3C6 Total de Victorias: {total_victories}\n{escape_markdown(victories_text)}"
        f"\U0001F947 Más Victorias contra: {most_victories}\n"
        f"\U0001F480 Total Derrotas: {total_defeats}\n{escape_markdown(defeats_text)}"
        f"\U0001F635 Más Derrotas contra: {most_defeats}\n"
        f"\U0001F4D6 Titulos:\n{titles_text}"
    )
    return profile_text

# Function to set the schedule for the bot to operate
def is_active_hours():
    #Add your own time
    argentina_tz = pytz.timezone('America/Argentina/Buenos_Aires')
    current_hour = datetime.now(argentina_tz).hour
    return 10 <= current_hour < 23  # Solo funciona de 10:00 a 22:59

# Function to check if its time for the bot to work
def check_active_hours():
    if not is_active_hours():
        msg = bot.send_message(group_id, "\U0001F4E2 Lo siento, el bot no está activo en estos momentos. Estará activo entre las 10:00 AM y 22:59 PM (GMT-3).",message_thread_id=topic_id)
        threading.Timer(5, lambda: bot.delete_message(chat_id=group_id, message_id=msg.message_id)).start()
        return False
    return True

# Function for the escaping pokemon
def pokemon_escape(pokemon, group_id, message_id):
    try:
        escape_msgs = [f"\U0001F4A8 ¡El {'\U0001F48E' if pokemon['isLegendary'] else ''}{pokemon['name']}{'\U0001F31F' if pokemon['isShiny'] else ''} {'\u2642' if pokemon['gender']=='Male' else '\u2640' if pokemon['gender']=='Female' else ''} Nv.{pokemon['level']} salvaje se ha escapado!",
                       f"\U0001F4A8 ¡Alguien tiro una piedra e hizo que el {'\U0001F48E' if pokemon['isLegendary'] else ''}{pokemon['name']}{'\U0001F31F' if pokemon['isShiny'] else ''} {'\u2642' if pokemon['gender']=='Male' else '\u2640' if pokemon['gender']=='Female' else ''} Nv.{pokemon['level']} salvaje se escapará!",
                       f"\U0001F4A8 ¡El {'\U0001F48E' if pokemon['isLegendary'] else ''}{pokemon['name']}{'\U0001F31F' if pokemon['isShiny'] else ''} {'\u2642' if pokemon['gender']=='Male' else '\u2640' if pokemon['gender']=='Female' else ''} Nv.{pokemon['level']} salvaje vio un mal meme y se escapó!",
                       f"\U0001F4A8 ¡El {'\U0001F48E' if pokemon['isLegendary'] else ''}{pokemon['name']}{'\U0001F31F' if pokemon['isShiny'] else ''} {'\u2642' if pokemon['gender']=='Male' else '\u2640' if pokemon['gender']=='Female' else ''} Nv.{pokemon['level']} salvaje estaba un poco asustado y se escapó!",
                       f"\U0001F4A8 ¡El {'\U0001F48E' if pokemon['isLegendary'] else ''}{pokemon['name']}{'\U0001F31F' if pokemon['isShiny'] else ''} {'\u2642' if pokemon['gender']=='Male' else '\u2640' if pokemon['gender']=='Female' else ''} Nv.{pokemon['level']} salvaje vio a alguien bajarse los pantalones y se escapó!",
                       f"\U0001F4A8 ¡El {'\U0001F48E' if pokemon['isLegendary'] else ''}{pokemon['name']}{'\U0001F31F' if pokemon['isShiny'] else ''} {'\u2642' if pokemon['gender']=='Male' else '\u2640' if pokemon['gender']=='Female' else ''} Nv.{pokemon['level']} salvaje esquivo una pokebola y se escapó!",
                       f"\U0001F4A8 ¡El {'\U0001F48E' if pokemon['isLegendary'] else ''}{pokemon['name']}{'\U0001F31F' if pokemon['isShiny'] else ''} {'\u2642' if pokemon['gender']=='Male' else '\u2640' if pokemon['gender']=='Female' else ''} Nv.{pokemon['level']} salvaje era en realidad un muñeco falso!",
                       f"\U0001F4A8 ¡El {'\U0001F48E' if pokemon['isLegendary'] else ''}{pokemon['name']}{'\U0001F31F' if pokemon['isShiny'] else ''} {'\u2642' if pokemon['gender']=='Male' else '\u2640' if pokemon['gender']=='Female' else ''} Nv.{pokemon['level']} salvaje era en realidad un Ditto y se escapó!",
                       f"\U0001F480 ¡Una pokebola fue arrojada tan fuerte que mato al {'\U0001F48E' if pokemon['isLegendary'] else ''}{pokemon['name']}{'\U0001F31F' if pokemon['isShiny'] else ''} {'\u2642' if pokemon['gender']=='Male' else '\u2640' if pokemon['gender']=='Female' else ''} Nv.{pokemon['level']}!",
                       f"\U0001F480 ¡El {'\U0001F48E' if pokemon['isLegendary'] else ''}{pokemon['name']}{'\U0001F31F' if pokemon['isShiny'] else ''} {'\u2642' if pokemon['gender']=='Male' else '\u2640' if pokemon['gender']=='Female' else ''} Nv.{pokemon['level']} salvaje se suicidó para que no lo capturaran!"]
        # Notify the group that the Pokémon escaped
        bot.edit_message_text(
            random.choice(escape_msgs),
            chat_id=group_id,
            message_id=message_id
        )
        if message_id in spawned_pokemons:
            del spawned_pokemons[message_id]
    except Exception as e:
        logger.error(f"Error durante la notificacion de escape: {e}")

# Function to generate the capture chance
def captureCheck(pokemon):
    capture_check = round((random.uniform(1,100) * (1 + pokemon["level"]/100)), 2)
    if pokemon["isShiny"]:
        capture_check *= 1.3
    if pokemon["isLegendary"]:
        capture_check *= 1.2
    return capture_check

# Function to cancel the ongoing combat
def cancel_combat():
    if combat_manager.is_combat_active() and combat_manager.ongoing_combat["opponent"] is None:
        try:
            msg = bot.edit_message_text(
                "\u23F3 El combate ha expirado.",
                group_id,
                combat_manager.ongoing_combat["message_id"]
            )
            threading.Timer(3, lambda: bot.delete_message(chat_id=group_id, message_id=msg.message_id)).start()
        except Exception as e:
            logger.error(f"Error al cancelar combate: {e}")
        combat_manager.end_combat()

# Functions for the commands of the bot
#----------------------------------------------------------------
# Bot command handler for /iniciar
@bot.message_handler(commands=['iniciar'])
def start(message):
    try:
        if not check_active_hours():
            return
        bot.set_my_commands(commands)
        bot.reply_to(message, "\U0001F4AC Hola, soy PokeGramBot!")
    except Exception as e:
        logger.error(f"Error durante /iniciar: {e}")

# Bot command handler for /ayuda
@bot.message_handler(commands=['ayuda'])
def generate_help_message(message):
    try:
        if not check_active_hours():
            return
        help_text = "Lista de los comandos del bot:\n\n"
        for command in commands:
            help_text += f"/{command['command']}@pokegrambotbot - {command['description']}\n"
        help_text += f"\n\u26A0 Este bot es No Inclusivo, cualquier caso que pueda indicar lo contrario es un bug y será corregido."
        msg_cd = bot.reply_to(message, help_text)
        threading.Timer(60, lambda: bot.delete_message(chat_id=group_id, message_id=msg_cd.message_id)).start()
    except Exception as e:
        logger.error(f"Error durante /ayuda: {e}")

# Bot command handler for /captura
@bot.message_handler(commands=['captura'])
def generate_help_message(message):
    try:
        if not check_active_hours():
            return
        help_text = "\U0001F4DC Probabilidad de captura de Pokémones\n\U0001F538Nivel 1:\nComún: 80%\nShiny:56%\nLegendario:64%\n\n\U0001F539Nivel 100:\nComún: 39%\nShiny:30%\nLegendario: 33%\nLegendario y Shiny: 25%\n\n\u26A0IMPORTANTe: Este valor solo puede usarse como referencia. La probabilidad real es afectada por un valor aleatorio que puede disminuir la probabilidad de captura!"
        msg_cd = bot.reply_to(message, help_text)
        threading.Timer(90, lambda: bot.delete_message(chat_id=group_id, message_id=msg_cd.message_id)).start()
    except Exception as e:
        logger.error(f"Error durante /captura: {e}")

# Bot command handler for /registrar
@bot.message_handler(commands=['registrar'])
def register_command(message):
    try:
        if not check_active_hours():
            return
        username = message.from_user.username
        if not username:
            msg_cd = bot.reply_to(message, "\u26A0 No tienes un nombre de usuario en Telegram. Configúralo primero.")
            threading.Timer(5, lambda: bot.delete_message(chat_id=group_id, message_id=msg_cd.message_id)).start()
            return
        if userEvents.checkUserisRegistered(username):
            msg_cd = bot.reply_to(message, f"\U0001F4E2 Usuario @{username} ya está registrado.")
            threading.Timer(5, lambda: bot.delete_message(chat_id=group_id, message_id=msg_cd.message_id)).start()
        else:
            userEvents.registerUser(username)
            msg_cd = bot.reply_to(message, f"\U0001F514 Usuario @{username} registrado con éxito.")
            threading.Timer(10, lambda: bot.delete_message(chat_id=group_id, message_id=msg_cd.message_id)).start()
    except Exception as e:
        logger.error(f"Error durante /registrar: {e}")

# Bot command handler for /spawn
@bot.message_handler(commands=['spawn'])
def spawn_pokemon_handler(message):
    try:
        if not check_active_hours():
            return
        user_id = message.from_user.id
        current_time = time.time()
        if user_id in last_spawn_times:
            elapsed_time = current_time - last_spawn_times[user_id]
            if elapsed_time < spawn_cooldawn:
                remaining_time = spawn_cooldawn - elapsed_time
                msg_cd = bot.reply_to(
                    message,
                    f"\u26A0 ¡Estás en cooldown! Por favor espera {int(remaining_time)} segundos antes de spawnear otro Pokémon."
                )
                threading.Timer(2, lambda: bot.delete_message(chat_id=group_id, message_id=msg_cd.message_id)).start()
                return
        last_spawn_times[user_id] = current_time
        total_pokemons = len(spawned_pokemons)
        if total_pokemons >= 2:
            msg = bot.reply_to(message, "\u26A0 No puedes spawnear más Pokémones. Se alcanzado el límite (2).")
            threading.Timer(2, lambda: bot.delete_message(chat_id=group_id, message_id=msg.message_id)).start()
            return
        spawn_check = random.randint(1,100)
        if spawn_check <= 5:
            msg = bot.reply_to(message, "\U0001F4A8 El Pokémon escapó al intentar spawnearlo...")
            threading.Timer(2, lambda: bot.delete_message(chat_id=group_id, message_id=msg.message_id)).start()
            return
        pokemon = pokemonEvents.generatePokemon()
        pokemon_image = pokemon["image"]
        if pokemon:
            if os.path.exists(pokemon_image):
                with open(pokemon_image, 'rb') as photo:
                    bot.send_sticker(
                        group_id,
                        photo,
                        message_thread_id=topic_id
                    )
            pokemon_name = f"***{pokemon['name']}***" if pokemon['isLegendary'] else pokemon['name']
            msg = bot.send_message(
                group_id,
                f"\U0001F514 ¡Un {'\U0001F48E' if pokemon['isLegendary'] else ''}{pokemon_name}{'\U0001F31F' if pokemon['isShiny'] else ''} salvaje apareció! ¿Qué vas a hacer?\nGenero: {'\u2642 ' if pokemon['gender']=='Male' else '\u2640 ' if pokemon['gender']=='Female' else 'Desconocido'}\nNivel: {pokemon['level']}",
                reply_markup=generate_capture_button(pokemon["id"]),
                message_thread_id=topic_id,
                parse_mode='Markdown'
            )
            spawned_pokemons[msg.message_id] = pokemon
            timer = threading.Timer(60.0, pokemon_escape, args=[pokemon, group_id, msg.message_id])
            capture_timers[msg.message_id] = timer
            timer.start()
        else:
            bot.reply_to(message, "\u26A0 Fallo al spawnear un Pokémon.")
    except Exception as e:
        logger.error(f"Error durante /spawn: {e}")

# Callback query handler for "Capturar!" button
@bot.callback_query_handler(func=lambda call: call.data.startswith("capture:"))
def capture_pokemon_handler(call):
    try:
        username = call.from_user.username
        if checkUserExistence(username):
            return
        pokemon = spawned_pokemons.get(call.message.message_id)
        if pokemon is None:
            bot.answer_callback_query(call.id, "Pokémon no encontrado.")
            return
        message_id = call.message.message_id
        if message_id in capture_locks:
            bot.answer_callback_query(call.id, random.choice(["¡Muy tarde! Alguien más capturó al Pokémon.", "¡Yasper, otro lo agarró!"]))
            return
        user_id = call.from_user.id
        capture_locks[message_id] = user_id
        # Attempt to capture the Pokémon
        if captureCheck(pokemon) <= 80:
            userEvents.addPokemonCaptured(pokemon, username)  # Ensure this function is compatible with MongoDB Atlas
            if call.message.message_id in capture_timers:
                capture_timers[call.message.message_id].cancel()
                del capture_timers[call.message.message_id]
            bot.edit_message_text(
                f"\U0001F3C6 ¡{call.from_user.first_name} capturó un {'\U0001F48E' if pokemon['isLegendary'] else ''}{pokemon['name']}{'\U0001F31F' if pokemon['isShiny'] else ''} {'\u2642' if pokemon['gender']=='Male' else '\u2640' if pokemon['gender']=='Female' else ''} Nv.{pokemon['level']}!",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown"
            )
            del spawned_pokemons[call.message.message_id]
            del capture_locks[message_id]
        else:
            pokemon_escape(pokemon, call.message.chat.id, call.message.message_id)
    except Exception as e:
        if "query is too old" in str(e):  # Handle expired callback queries gracefully
            logger.error("Expired callback query: ignoring outdated interaction.")
        else:
            logger.error(f"Error durante capture: {e}")

# Bot command handler for /mispokemones
@bot.message_handler(commands=['mispokemones'])
def get_my_pokemons_by_user(message):
    try:
        if not check_active_hours():
            return
        username = message.from_user.username
        if checkUserExistence(username):
            return
        user = userEvents.getUserByName(username)
        pokemons = userEvents.getListOfPokemonCapturedByName(username)
        if pokemons:
            total_pokemons = user['total_pokemons']
            total_shiny = user['total_shiny']
            response = f"\U0001F4DC Tus Pokémones:\n\U0001F3C6 Pokémones: {total_pokemons} (\U0001F31FShiny: {total_shiny})\n"
            msg = bot.reply_to(message, response)
            threading.Timer(30, lambda: bot.delete_message(chat_id=group_id, message_id=msg.message_id)).start()
        else:
            msg = bot.reply_to(message, "\u26A0 No tienes Pokémones.")
            threading.Timer(3, lambda: bot.delete_message(chat_id=group_id, message_id=msg.message_id)).start()
    except Exception as e:
        logger.error(f"Error durante /mispokemones: {e}")

# Bot command handler for /capturados
@bot.message_handler(commands=['capturados'])
def get_captured_pokemons_by_user(message):
    try:
        if not check_active_hours():
            return
        username = message.from_user.username
        user_id = message.from_user.id
        if checkUserExistence(username):
            return
        user = userEvents.getUserByName(username)
        pokemons = userEvents.getListOfPokemonCapturedByName(username)
        if pokemons:
            pokemons = sorted(pokemons, key=lambda x: x["id"])
            total_pokemons = len(user['pokemonsOwned'])
            total_shiny = user['total_shiny']
            response = f"\U0001F4DC*Tu colección de Pokémon:*\n"
            response += f"\U0001F4E6 *Total capturados:* {total_pokemons}\n"
            response += f"\U0001F4E6 *Total Shiny:* {total_shiny}\n\n"
            for pkm in pokemons:
                shiny_status = "\u2705" if pkm["isShiny"] else "\u274C"
                response += f"\U0001F538 #{pkm['id']} - {'\U0001F48E' if pkm['isLegendary'] else ''}*{pkm['name']}*: {pkm['captured']}x (Shiny: {shiny_status}) (Nv.: {pkm['level']})\n"
            bot.send_message(user_id, response, parse_mode="Markdown")
        else:
            bot.send_message(user_id, "\u26A0 No tienes Pokémones.")
    except Exception as e:
        logger.error(f"Error durante /capturados: {e}")

# Bot command handler for /micoleccion
@bot.message_handler(commands=['micoleccion'])
def get_pokemons_collection_by_user(message):
    try:
        if not check_active_hours():
            return
        username = message.from_user.username
        if checkUserExistence(username):
            return
        user = userEvents.getUserByName(username)
        pokemons = userEvents.getListOfPokemonCapturedByName(username)
        total_pokemons = len(user['pokemonsOwned'])
        shiny_counts = {}
        legendary_counts = {}
        if pokemons:
            for pokemon in pokemons:
                if pokemon["name"] not in legendary_counts and pokemon["isLegendary"] == True:
                    legendary_counts[pokemon["name"]] = pokemon["id"]
                if pokemon["name"] not in shiny_counts and pokemon["isShiny"] == True:
                    shiny_counts[pokemon["name"]] = pokemon["id"]
            response = f"\U0001F3C6 Coleccipon de Pokémones: {total_pokemons}/151\n\U0001F31F Shiny: {shiny_counts}/151\n\U0001F48E Legendarios: {len(legendary_counts)}/5\n"
            msg = bot.reply_to(message, response)
            threading.Timer(30, lambda: bot.delete_message(chat_id=group_id, message_id=msg.message_id)).start()
        else:
            msg = bot.reply_to(message, "\u26A0 No tienes Pokémones.")
            threading.Timer(3, lambda: bot.delete_message(chat_id=group_id, message_id=msg.message_id)).start()
    except Exception as e:
        logger.error(f"Error durante /micoleccion: {e}")

# Bot command handler for /teelijo
@bot.message_handler(commands=['teelijo'])
def summon_pokemon(message):
    try:
        if not check_active_hours():
            return
        username = message.from_user.username
        if checkUserExistence(username):
            return
        # Get a random pokemon id from the user's collection
        random_pokemon = userEvents.getRandomPokemonCaptured(username)
        if random_pokemon:
            random_pkm_name = f"<b>{random_pokemon['name']}</b>"
            user_name = f"<b>{username}</b>"
            random_pkm_img = random_pokemon["image"]
            # bot message with the image of the pokemon
            if os.path.exists(random_pkm_img):
                with open(random_pkm_img, 'rb') as photo:
                    msg_st = bot.send_sticker(
                        group_id,
                        photo,
                        message_thread_id=topic_id
                    )
            msg_list = [f"\U0001F3B2 {user_name} ha elegido a {random_pkm_name}!",
                        f"\U0001F3B2 {user_name} se le cayó una pokeball y {random_pkm_name} se salió!",
                        f"\U0001F3B2 {random_pkm_name} salió para ver memes!",
                        f"\U0001F3B2 {user_name} sacó a {random_pkm_name} mientras veia el canal NSFW!"]
            msg_p = bot.send_message(
                group_id,
                random.choice(msg_list),
                message_thread_id=topic_id,
                parse_mode='HTML'
                )
            threading.Timer(30, lambda: bot.delete_message(chat_id=group_id, message_id=msg_p.message_id)).start()
            threading.Timer(30, lambda: bot.delete_message(chat_id=message.chat.id, message_id=msg_st.message_id)).start()
        else:
            msg = bot.send_message(group_id, "\u26A0 No tienes pokémones capturados.", message_thread_id=topic_id)
            threading.Timer(3, lambda: bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)).start()
    except Exception as e:
        logger.error(f"Error durante /teelijo: {e}")

# Bot command handler for /yoteelijo
@bot.message_handler(commands=['yoteelijo'])
def ichooseyou(message):
    try:
        if not check_active_hours():
            return
        username = message.from_user.username
        if checkUserExistence(username):
            return
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            msg = bot.reply_to(message, "\u26A0 Debes proporcionar un nombre o ID de Pokémon.")
            threading.Timer(5, lambda: bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)).start()  # Borrar el mensaje después de 5 segundos
            return
        parametro = args[1].strip()
        if parametro.isdigit():
            pokemon = userEvents.getPokemonCapturedById(username, int(parametro))
        else:
            pokemon = userEvents.getPokemonCapturedById(username, pokemonEvents.getPokemonByName(parametro.capitalize())['id'])
        if pokemon:
            pkm_name = f"<b>{pokemon['name']}</b>"
            user_name = f"<b>{username}</b>"
            pkm_image = pokemon["image"]
            if os.path.exists(pkm_image):
                with open(pkm_image, 'rb') as photo:
                    msg_st = bot.send_sticker(
                        group_id,
                        photo,
                        message_thread_id=topic_id
                    )
            msg_list = [f"\U0001F3B2 {user_name} ha elegido a {pkm_name}!",
                        f"\U0001F3B2 {user_name} liberó de su cautiverio a {pkm_name}!",
                        f"\U0001F3B2 {user_name} se sentia cariñoso de más y sacó a {pkm_name}!"]
            msg = bot.send_message(group_id, random.choice(msg_list), message_thread_id=topic_id, parse_mode="HTML")
            threading.Timer(30, lambda: bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)).start()
            threading.Timer(30, lambda: bot.delete_message(chat_id=message.chat.id, message_id=msg_st.message_id)).start()
        else:
            msg = bot.reply_to(message, "\u274C No tienes a ese Pokémon.")
            threading.Timer(5, lambda: bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)).start()
    except Exception as e:
        logger.error(f"Error durante /yoteelijo: {e}")

# Bot command handler for /perfil
@bot.message_handler(commands=['perfil'])
def profile(message):
    try:
        if not check_active_hours():
            return
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            username = message.from_user.username
        else:
            username = args[1].strip()
        if checkUserExistence(username):
            return
        user_data = userEvents.getUserByName(username)
        profile_text = get_user_data(user_data)
        msg = bot.reply_to(message, profile_text, parse_mode="Markdown")
        threading.Timer(30, lambda: bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)).start()
    except Exception as e:
        logger.error(f"Error durante /perfil: {e}")

# Bot command handler for /pokedex
@bot.message_handler(commands=['pokedex'])
def pokedex(message):
    try:
        if not check_active_hours():
            return
        args = message.text.split(maxsplit=1)  # Obtiene el parámetro después del comando
        if len(args) < 2:
            msg = bot.reply_to(message, "\u26A0 Debes proporcionar un nombre o ID de Pokémon.")
            threading.Timer(5, lambda: bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)).start()  # Borrar el mensaje después de 5 segundos
            return
        parametro = args[1].strip()
        if parametro.isdigit():
            pokemon = pokemonEvents.getPokemonById(int(parametro))
        else:
            pokemon = pokemonEvents.getPokemonByName(parametro.capitalize())  # Capitaliza el nombre
        if not pokemon:
            msg = bot.reply_to(message, "\u274C No se encontró el Pokémon en la Pokédex.")
            threading.Timer(5, lambda: bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)).start()  # Borrar el mensaje después de 5 segundos
            return
        gender_symbols = {
            "Male": "\u2642",
            "Female": "\u2640",
            "Genderless": "Desconocido"
        }
        type_symbols = {
            "Normal": "\u26AA",      
            "Fuego": "\U0001F525",    
            "Agua": "\U0001F4A7",   
            "Electrico": "\u26A1",    
            "Planta": "\U0001F33F",   
            "Hielo": "\u2744",         
            "Lucha": "\U0001F94A",
            "Veneno": "\u2620",      
            "Tierra": "\U0001F30E",  
            "Volador": "\U0001F54A",  
            "Pisiquico": "\U0001F52E", 
            "Bicho": "\U0001F41B",     
            "Roca": "\U0001FAA8",    
            "Fantasma": "\U0001F47B",   
            "Dragon": "\U0001F409",  
            "Siniestro": "\U0001F311",    
            "Acero": "\u2699",       
            "Hada": "\u2728"        
        }
        gender_display = ", ".join([gender_symbols.get(g, g) for g in pokemon.get("gender", ["Genderless"])])
        types_text = ", ".join([f"{type_symbols.get(t, '')} {t}" for t in pokemon["types"]])
        legendary_text = "\U0001F48E Legendario" if pokemon.get("isLegendary", False) else "\U0001F4A0 Común"
        pokemon_text = (
            f"\U0001F4D6 *Pokedex #{pokemon['id']}*\n"
            f"\U0001F535 *Nombre:* {pokemon['name']}\n"
            f"\U0001F300 *Tipos:* {types_text}\n"
            f"\U0001F538 *Generos:* {gender_display}\n"
            f"{legendary_text}"
        )
        msg = bot.send_message(group_id, pokemon_text, message_thread_id=topic_id, parse_mode="Markdown")
        threading.Timer(30, lambda: bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)).start()  # Borrar el mensaje después de 30 segundos
    except Exception as e:
        logger.error(f"Error durante /pokedex: {e}")

# Bot command handler for /mistitutlos
@bot.message_handler(commands=['mistitutlos'])
def my_titles_handler(message):
    try:
        if not check_active_hours():
            return
        username = message.from_user.username
        if checkUserExistence(username):
            return
        # Revisar y agregar títulos si es necesario
        userEvents.add_titles_to_user(username)
        updated_user_data = userEvents.getUserByName(username)  # Volver a obtener los datos actualizados
        user_titles = updated_user_data.get("titles", [])
        if not user_titles:
            msg = bot.reply_to(message, "\u26A0 No tienes títulos aún. ¡Sigue jugando para obtenerlos!")
            threading.Timer(5, lambda: bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)).start()
            return
        # Formatear la lista de títulos con descripciones
        print(userEvents.titles)
        titles_list = "\n".join([f"\U0001F3C6 *{title}*: {next(t['description'] for t in userEvents.titles if t['title'] == title)}" for title in user_titles])
        msg = bot.send_message(group_id, f"\U0001F451 *Tus títulos obtenidos:*\n{titles_list}", parse_mode="Markdown", message_thread_id=topic_id)
        threading.Timer(30, lambda: bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)).start()
    except Exception as e:
        logger.error(f"Error durante /mistitutlos: {e}")

# Bot command handler for /titulos
@bot.message_handler(commands=['titulos'])
def all_titles_handler(message):
    try:
        if not check_active_hours():
            return
        titles_list = "\n".join([f"\U0001F3C6 *{title["title"]}*: {title["howto"]}" for title in userEvents.titles])
        msg = bot.send_message(group_id, f"\U0001F4D2 *Títulos Disponibles:*\n{titles_list}", parse_mode="Markdown", message_thread_id=topic_id)
        threading.Timer(30, lambda: bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)).start()  # Borrar el mensaje después de 30 segundos
    except Exception as e:
        logger.error(f"Error durante /titulos: {e}")

# Bot command handler for /jugadores
@bot.message_handler(commands=['jugadores'])
def players_handler(message):
    try:
        if not check_active_hours():
            return
        players = userEvents.getAllUsers()
        players_list = "\n".join([f"\U0001F464 *{player}*" for player in players])
        msg = bot.send_message(group_id, f"\U0001F465 *Jugadores Activos:*\n{players_list}", parse_mode="Markdown", message_thread_id=topic_id)
        threading.Timer(30, lambda: bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)).start()  # Borrar el mensaje después de 30 segundos
    except Exception as e:
        logger.error(f"Error durante /jugadores: {e}")
        msg = bot.reply_to(message, "\u274C Ocurrió un error al obtener la lista de jugadores.")
        threading.Timer(5, lambda: bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)).start()

class CombatManager:
    def __init__(self):
        self.ongoing_combat = None  # Stores the ongoing combat
    def is_combat_active(self):
        return self.ongoing_combat is not None
    def start_combat(self, username, user_pokemon, msg_id):
        self.ongoing_combat = {
            "username": username,
            "pokemon": user_pokemon,
            "message_id": msg_id,
            "opponent": None
        }
    def end_combat(self):
        self.ongoing_combat = None  # Restarts the ongoing combat
# instance of the combat manager to manage the ongoing combat
combat_manager = CombatManager()


# Bot command handler for /combate
@bot.message_handler(commands=['combate'])
def start_combat(message):
    try:
        if not check_active_hours():
            return
        if combat_manager.is_combat_active():
            msg = bot.reply_to(message, "\u26A0 Ya hay un combate en curso. Espera a que termine.")
            threading.Timer(5, lambda: bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)).start()
            return
        username = message.from_user.username
        user_pokemon = userEvents.getRandomPokemonCaptured(username)
        if not user_pokemon:
            msg = bot.reply_to(message, "\u26A0 No tienes Pokémon para combatir.")
            threading.Timer(5, lambda: bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)).start()
            return
        keyboard = InlineKeyboardMarkup()
        duel_button = InlineKeyboardButton("Luchar", callback_data=f"duel:{username}")
        keyboard.add(duel_button)
        msg = bot.send_message(
            group_id,
            f"\u2694 ¡{escape_markdown(username)} ha iniciado un combate con *{user_pokemon['name']}* Nv.{user_pokemon['level']}!\n¡Presiona 'Luchar' para enfrentarlo!",
            message_thread_id=topic_id,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        # Registrar el combate en el CombatManager
        combat_manager.start_combat(username, user_pokemon, msg.message_id)
        # Temporizador para cancelar el combate en 2 minutos si no es aceptado
        threading.Timer(120, cancel_combat).start()
    except Exception as e:
        logger.error(f"Error durante /combate: {e}")

# Callback query handler for "Duel" button
@bot.callback_query_handler(func=lambda call: call.data.startswith("duel:"))
def accept_duel(call):
    try:
        if not combat_manager.is_combat_active():  # Verificar si hay un combate activo
            bot.answer_callback_query(call.id, "El duelo ya ha sido aceptado o ha expirado.")
            return
        challenger = combat_manager.ongoing_combat["username"]
        opponent = call.from_user.username
        if combat_manager.ongoing_combat["opponent"]:
            bot.answer_callback_query(call.id, "El duelo ya ha sido aceptado.")
            return
        if opponent == challenger:
            bot.answer_callback_query(call.id, "No puedes luchar contra ti mismo.")
            return
        opponent_pokemon = userEvents.getRandomPokemonCaptured(opponent)
        if not opponent_pokemon:
            bot.answer_callback_query(call.id, "No tienes Pokémon para combatir.")
            return
        # Set the opponent for the ongoing combat
        combat_manager.ongoing_combat["opponent"] = {
            "username": opponent,
            "pokemon": opponent_pokemon
        }
        # Combat result calculation
        challenger_pokemon = combat_manager.ongoing_combat['pokemon']
        combat_roll = random.randint(10, 60)
        level_check = 2 * (challenger_pokemon['level'] - opponent_pokemon['level'])
        challenger_advantage = pokemonEvents.get_type_advantage(challenger_pokemon['types'], opponent_pokemon['types'])
        opponent_advantage = pokemonEvents.get_type_advantage(opponent_pokemon['types'], challenger_pokemon['types'])
        type_modifier = challenger_advantage - opponent_advantage
        final_score = combat_roll * 0.4 + level_check * 0.3 + type_modifier * 0.3
        result = final_score < 50
        # Setting winner and loser
        winner, loser = (opponent, challenger) if result else (challenger, opponent)
        loser_pokemon = challenger_pokemon if loser == challenger else opponent_pokemon
        winner_pokemon = challenger_pokemon if winner == challenger else opponent_pokemon
        # reduce or delete pokemon
        userEvents.reducePokemonCaptured(loser, loser_pokemon)
        # steal chance
        steal = random.randint(1, 100) <= 5
        if steal:
            userEvents.addPokemonCaptured(loser_pokemon, winner)
        # leveling up pkm
        leveled_up = False
        if winner_pokemon['level'] < 100:
            new_level = min(winner_pokemon['level'] + random.randint(1, 5), 100)
            leveled_up = True
        userEvents.updateCombatResults(winner, loser, winner_pokemon, new_level)
        # responce msg
        response = (
            f"\u2694 {challenger} ({challenger_pokemon['name']} Nv.{challenger_pokemon['level']}) vs {opponent} ({opponent_pokemon['name']} Nv.{opponent_pokemon['level']})!\n\n"
            f"\U0001F3C6 {'¡' + opponent + ' gana!' if result else '¡' + challenger + ' gana!'}\n\n"
            f"\u274C {loser} pierde a su {loser_pokemon['name']}!\n\n"
            f"{(f"\U0001F53C {winner}'s {winner_pokemon['name']} ha subido de nivel! Ahora es Nv.{new_level}!") if leveled_up else ''}"
            f"{(f'\n\n\U0001F3C5 {winner} ha robado a {loser} su {loser_pokemon['name']} antes de que se muriera!') if steal else ''}"
        )
        bot.edit_message_text(
            response,
            call.message.chat.id, call.message.message_id
        )
        # end the ongoing combat
        combat_manager.end_combat()
    except Exception as e:
        logger.error(f"Error durante duel: {e}")

# Mock message class for the auto_spawn_event
class MockMessage:
    def __init__(self):
        self.from_user = type('User', (), {'id': 0})  # Replace with a valid user ID
        self.chat = type('Chat', (), {'id': group_id})     # Replace with your group ID
        self.message_id = 1
# Automatically send the command /spawn with the bot every 10 minutes
def auto_spawn_event():
    while True:
        try:
            if check_active_hours():
                mock_message = MockMessage()  # mock message
                spawn_pokemon_handler(mock_message)  # call spawn_pokemon_handler
            time.sleep(1200)  # wait 10 minutes
        except Exception as e:
            logger.error(f"Error durante auto-spawn: {e}")
# start the event in a different thread
spawn_thread = threading.Thread(target=auto_spawn_event, daemon=True)
spawn_thread.start()

# From this line until the next line there will not be more documentation or comment lines explaining anything.
# If you get any error then update, fix or delete the code yourself.
#----------------------------------------------------------------------------------------------------
@bot.message_handler(func=lambda message: True)
def monitor_messages(message):
    try:
        if "(?" in message.text:
            threading.Timer(2.0, replace_message, args=[message]).start()
        if "( ?" in message.text:
            username = message.from_user.username or message.from_user.first_name
            userEvents.deleteRandomPokemon(username)
    except Exception as e:
        logger.error(f"Error monitoreando mensajes: {e}")

def replace_message(message):
    try:
        mod_text_list = [
            "? Por cierto, soy puto.",
            "? Me encanta tragar sables",
            "? Puto el que lee.",
            "? Ojala que llueva para vergotas.",
            "? A Nisman lo mataron.",
            "? Se te borró un pokemon, F"]
        modified_text = message.text.replace("(?", random.choice(mod_text_list))
        bot.delete_message(message.chat.id, message.message_id)
        user_name = message.from_user.username or message.from_user.first_name
        user_intro = f"<b>@{user_name}</b> dijo:"
        final_text = f"{user_intro}\n{modified_text}"
        bot.send_message(
            chat_id=message.chat.id,
            text=final_text,
            parse_mode="HTML",
            message_thread_id=message.message_thread_id
        )
    except Exception as e:
        logger.error(f"Error reemplazando mensajes: {e}")
#----------------------------------------------------------------------------------------------------
# Initialization of the bot.
bot.infinity_polling()