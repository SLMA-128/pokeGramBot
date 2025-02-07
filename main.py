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

# Definir las variables de entorno
#TELEGRAM_TOKEN = config.TELEGRAM_TOKEN
#CHANNEL_ID = config.CHANNEL_ID
#TOPIC_ID = config.TOPIC_ID
#MONGO_URI = config.MONGO_URI
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
TOPIC_ID = int(os.getenv("TOPIC_ID", "0"))
MONGO_URI = os.getenv("MONGO_URI")
# Validar que las variables de entorno estén configuradas
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN no está configurado en las variables de entorno.")
if not CHANNEL_ID:
    raise ValueError("CHANNEL_ID no está configurado en las variables de entorno.")
if not TOPIC_ID:
    raise ValueError("TOPIC_ID no está configurado en las variables de entorno.")
if not MONGO_URI:
    raise ValueError("MONGO_URI no está configurada en las variables de entorno.")

# Conexión a MongoDB Atlas
#client = MongoClient(config.MONGO_URI)
client = MongoClient(MONGO_URI)
db = client.get_database()
#bpt, group_id and topic_id values
bot = telebot.TeleBot(TELEGRAM_TOKEN)
group_id = CHANNEL_ID
topic_id = TOPIC_ID
#capture_timers should save the timers of all spawned pokemons
capture_timers = {}
#capture spawned pokemons in the dictionary
spawned_pokemons = {}
#capture spawned pokemons in the dictionary to prvent others users to get them
capture_locks = {}
# Dictionary to track last usage times for the spawn command
last_spawn_times = {}
spawn_cooldawn = 60  # Cooldown time in seconds
# Dictionary to track combats
ongoing_combats = {}
#commands

commands=[
    {"command": "capturedpokemons", "description": "Show your captured Pokemon with deatails."},
    {"command": "chance", "description": "Show the chance to capture pokemons.)"},
    {"command": "chooseyou", "description": "Summon a random pokemon from the user.)"},
    {"command": "help", "description": "Get the list of commands."},
    {"command": "mycollection", "description": "Show how many type of Pokemons you have captured."},
    {"command": "mypokemons", "description": "Show how many Pokemons, normal and shiny, you captured."},
    {"command": "profile", "description": "Shows the profile of the user"},
    {"command": "register", "description": "Register your username."},
    {"command": "spawn", "description": "Spawn a random Pokemon. Each user can spawn once a minute."},
    {"command": "start", "description": "The bot starts and says hi."},
    {"command": "startcombat", "description": "Start a combat with a random Pokemon. Whoever loses loses a pokemon."}
]

#General functions
# Generate an inline keyboard with a "Capture!" button
def generate_capture_button(pokemonId):
    markup = InlineKeyboardMarkup()
    button = InlineKeyboardButton("Capture!", callback_data=f"capture:{pokemonId}")
    markup.add(button)
    return markup

def checkUserExistence(username):
    if not username:
        msg_cd = bot.send_message(group_id, "\u26A0 You don't have a Telegram username. Please set one to see your Pokémon.",message_thread_id=topic_id)
        threading.Timer(5, lambda: bot.delete_message(chat_id=group_id, message_id=msg_cd.message_id)).start()
        return True
    if not userEvents.checkUserisRegistered(username):
        msg_cd = bot.send_message(group_id, "\u26A0 You didn't register.",message_thread_id=topic_id)
        threading.Timer(5, lambda: bot.delete_message(chat_id=group_id, message_id=msg_cd.message_id)).start()
        return True
    return False

#Function to check if its time for the bot to work
def is_active_hours():
    #Add your own time
    argentina_tz = pytz.timezone('America/Argentina/Buenos_Aires')
    current_hour = datetime.now(argentina_tz).hour
    return 10 <= current_hour < 23  # Solo funciona de 10:00 a 22:59

def check_active_hours():
    if not is_active_hours():
        msg = bot.send_message(group_id, "\U0001F4E2 Sorry, the bot is not active at the moment. It works from 10:00 to 22:59.",message_thread_id=topic_id)
        threading.Timer(5, lambda: bot.delete_message(chat_id=group_id, message_id=msg.message_id)).start()
        return False
    return True

#Function for the escaping pokemon
def pokemon_escape(pokemon, group_id, message_id):
    try:
        escape_msgs = [f"\U0001F4A8 The wild Lv.{pokemon['level']} {'\u2642 ' if pokemon['gender']=='Male' else '\u2640 ' if pokemon['gender']=='Female' else ''} {'\U0001F48E' if pokemon['isLegendary'] else ''}{pokemon['name']}{'\U0001F31F' if pokemon['isShiny'] else ''} has escaped!",
                       f"\U0001F4A8 Someone throw a rock and made the Lv.{pokemon['level']} {'\u2642 ' if pokemon['gender']=='Male' else '\u2640 ' if pokemon['gender']=='Female' else ''}{'\U0001F48E' if pokemon['isLegendary'] else ''}{pokemon['name']}{'\U0001F31F' if pokemon['isShiny'] else ''} escape!",
                       f"\U0001F4A8 The wild Lv.{pokemon['level']} {'\u2642 ' if pokemon['gender']=='Male' else '\u2640 ' if pokemon['gender']=='Female' else ''} {'\U0001F48E' if pokemon['isLegendary'] else ''}{pokemon['name']}{'\U0001F31F' if pokemon['isShiny'] else ''} saw a bad meme and escaped!",
                       f"\U0001F4A8 The wild Lv.{pokemon['level']} {'\u2642 ' if pokemon['gender']=='Male' else '\u2640 ' if pokemon['gender']=='Female' else ''} {'\U0001F48E' if pokemon['isLegendary'] else ''}{pokemon['name']}{'\U0001F31F' if pokemon['isShiny'] else ''} is a little scared and escaped!",
                       f"\U0001F4A8 The wild Lv.{pokemon['level']} {'\u2642 ' if pokemon['gender']=='Male' else '\u2640 ' if pokemon['gender']=='Female' else ''} {'\U0001F48E' if pokemon['isLegendary'] else ''}{pokemon['name']}{'\U0001F31F' if pokemon['isShiny'] else ''} saw someone taking down their pants and escaped!",
                       f"\U0001F4A8 The wild Lv.{pokemon['level']} {'\u2642 ' if pokemon['gender']=='Male' else '\u2640 ' if pokemon['gender']=='Female' else ''} {'\U0001F48E' if pokemon['isLegendary'] else ''}{pokemon['name']}{'\U0001F31F' if pokemon['isShiny'] else ''} dodged a pokeball and escaped!",
                       f"\U0001F4A8 The wild Lv.{pokemon['level']} {'\u2642 ' if pokemon['gender']=='Male' else '\u2640 ' if pokemon['gender']=='Female' else ''} {'\U0001F48E' if pokemon['isLegendary'] else ''}{pokemon['name']}{'\U0001F31F' if pokemon['isShiny'] else ''} was in reality a fake doll!",
                       f"\U0001F4A8 The wild Lv.{pokemon['level']} {'\u2642 ' if pokemon['gender']=='Male' else '\u2640 ' if pokemon['gender']=='Female' else ''} {'\U0001F48E' if pokemon['isLegendary'] else ''}{pokemon['name']}{'\U0001F31F' if pokemon['isShiny'] else ''} was in reality a Ditto and has escaped!",
                       f"\U0001F480 A pokeball was thrown too hard and killed the Lv.{pokemon['level']} {'\u2642 ' if pokemon['gender']=='Male' else '\u2640 ' if pokemon['gender']=='Female' else ''} {'\U0001F48E' if pokemon['isLegendary'] else ''}{pokemon['name']}{'\U0001F31F' if pokemon['isShiny'] else ''}!",
                       f"\U0001F480 The wild Lv.{pokemon['level']} {'\u2642 ' if pokemon['gender']=='Male' else '\u2640 ' if pokemon['gender']=='Female' else ''} {'\U0001F48E' if pokemon['isLegendary'] else ''}{pokemon['name']}{'\U0001F31F' if pokemon['isShiny'] else ''} killed itself to not be captured!"]
        # Notify the group that the Pokémon escaped
        bot.edit_message_text(
            random.choice(escape_msgs),
            chat_id=group_id,
            message_id=message_id
        )
        if message_id in spawned_pokemons:
            del spawned_pokemons[message_id]
    except Exception as e:
        logger.error(f"Error during escape notification: {e}")

#generate the capture chance
def captureCheck(pokemon):
    capture_check = round((random.uniform(1,100) * (1 + pokemon["level"]/100)), 2)
    if pokemon["isShiny"]:
        capture_check *= 1.3
    if pokemon["isLegendary"]:
        capture_check *= 1.2
    return capture_check

#Functions for the bot
#The bot start and says hi
@bot.message_handler(commands=['start'])
def start(message):
    try:
        if not check_active_hours():
            return
        bot.set_my_commands(commands)
        bot.reply_to(message, "\U0001F4AC Hola, soy PokeGramBot!")
    except Exception as e:
        logger.error(f"Error during start: {e}")

#shows some functions
@bot.message_handler(commands=['help'])
def generate_help_message(message):
    try:
        if not check_active_hours():
            return
        help_text = "Here are the commands you can use:\n\n"
        for command in commands:
            help_text += f"/{command['command']}@pokegrambotbot - {command['description']}\n"
        help_text += f"\n\u26A0 Este bot es No Inclusivo, cualquier caso que pueda indicar lo contrario es un bug y será corregido."
        msg_cd = bot.reply_to(message, help_text)
        threading.Timer(60, lambda: bot.delete_message(chat_id=group_id, message_id=msg_cd.message_id)).start()
    except Exception as e:
        logger.error(f"Error during help: {e}")

#shows the chance of capture
@bot.message_handler(commands=['chance'])
def generate_help_message(message):
    try:
        if not check_active_hours():
            return
        help_text = "\U0001F4DC Chance to Capture Pokemons\n\U0001F538Level 1:\nBase: 80%\nShiny:56%\nLegendary:64%\n\n\U0001F539Level 100:\nBase: 39%\nShiny:30%\nLegendary: 33%\nLegendary and Shiny: 25%\n\n\u26A0IMPORTANT: This value can be used as reference but said chance is affected by a random value which lowers the rate!"
        msg_cd = bot.reply_to(message, help_text)
        threading.Timer(90, lambda: bot.delete_message(chat_id=group_id, message_id=msg_cd.message_id)).start()
    except Exception as e:
        logger.error(f"Error during help: {e}")

# Bot command handler for /register
@bot.message_handler(commands=['register'])
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
        logger.error(f"Error during registration: {e}")

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
                    f"\u26A0 You're on cooldown! Please wait {int(remaining_time)} seconds before spawning another Pokémon."
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
        if spawn_check <= 10:
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
                f"\U0001F514 A wild {'\U0001F48E' if pokemon['isLegendary'] else ''}{pokemon_name}{'\U0001F31F' if pokemon['isShiny'] else ''} appeared! What will you do?\nGender: {'\u2642 ' if pokemon['gender']=='Male' else '\u2640 ' if pokemon['gender']=='Female' else pokemon['gender']}\nLevel: {pokemon['level']}",
                reply_markup=generate_capture_button(pokemon["id"]),
                message_thread_id=topic_id,
                parse_mode='Markdown'
            )
            spawned_pokemons[msg.message_id] = pokemon
            timer = threading.Timer(60.0, pokemon_escape, args=[pokemon, group_id, msg.message_id])
            capture_timers[msg.message_id] = timer
            timer.start()
        else:
            bot.reply_to(message, "\u26A0 Failed to spawn a Pokémon.")
    except Exception as e:
        logger.error(f"Error during spawn: {e}")

# Callback query handler for "Capture!" button
@bot.callback_query_handler(func=lambda call: call.data.startswith("capture:"))
def capture_pokemon_handler(call):
    try:
        username = call.from_user.username
        if checkUserExistence(username):
            return
        pokemon = spawned_pokemons.get(call.message.message_id)
        if pokemon is None:
            bot.answer_callback_query(call.id, "No Pokémon found.")
            return
        message_id = call.message.message_id
        if message_id in capture_locks:
            bot.answer_callback_query(call.id, random.choice(["Too late! Someone else captured the Pokémon.", "Yasper, otro lo agarró!"]))
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
                f"\U0001F3C6 {call.from_user.first_name} captured a Lv.{pokemon['level']} {'\u2642 ' if pokemon['gender']=='Male' else '\u2640 ' if pokemon['gender']=='Female' else ''} {'\U0001F48E' if pokemon['isLegendary'] else ''}{pokemon['name']}{'\U0001F31F' if pokemon['isShiny'] else ''}!",
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
            logger.error(f"Error during capture: {e}")

# Callback query handler for /mypokemons
@bot.message_handler(commands=['mypokemons'])
def get_pokemons_by_user(message):
    try:
        if not check_active_hours():
            return
        username = message.from_user.username
        if checkUserExistence(username):
            return
        user = userEvents.getUserByName(username)
        pokemons = userEvents.getListOfPokemonCapturedByName(username)
        if pokemons:
            total_pokemons = len(user['pokemonsOwned'])
            total_shiny = user['total_shiny']
            response = f"\U0001F4DC Your Pokémon Collection:\n\U0001F3C6 Pokemons: {total_pokemons} (\U0001F31FShiny: {total_shiny})\n"
            msg = bot.reply_to(message, response)
            threading.Timer(30, lambda: bot.delete_message(chat_id=group_id, message_id=msg.message_id)).start()
        else:
            msg = bot.reply_to(message, "\u26A0 You don't have any Pokémon captured.")
            threading.Timer(3, lambda: bot.delete_message(chat_id=group_id, message_id=msg.message_id)).start()
    except Exception as e:
        logger.error(f"Error during mypokemons: {e}")

# Callback query handler for /capturedpokemons
@bot.message_handler(commands=['capturedpokemons'])
def get_pokemons_by_user(message):
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
                response += f"\U0001F538 #{pkm['id']} - {'\U0001F48E' if pkm['isLegendary'] else ''}*{pkm['name']}*: {pkm['captured']}x (Shiny: {shiny_status}) (Lv.: {pkm['level']})\n"
            bot.send_message(user_id, response, parse_mode="Markdown")
        else:
            bot.send_message(user_id, "\u26A0 You don't have any Pokémon captured.")
    except Exception as e:
        logger.error(f"Error during capturedpokemons: {e}")

# Callback query handler for /mycollection
@bot.message_handler(commands=['mycollection'])
def get_pokemons_by_user(message):
    try:
        if not check_active_hours():
            return
        username = message.from_user.username
        if checkUserExistence(username):
            return
        user = userEvents.getUserByName(username)
        pokemons = userEvents.getListOfPokemonCapturedByName(username)
        total_pokemons = user['total_pokemons']
        total_shiny = user['total_shiny']
        legendary_counts = {}
        if pokemons:
            for pokemon in pokemons:
                if pokemon["name"] not in legendary_counts and pokemon["isLegendary"] == True:
                    legendary_counts[pokemon["name"]] = pokemon["id"]
            response = f"\U0001F3C6 Pokémons Collected: {total_pokemons}/151\n\U0001F31F Shiny: {total_shiny}/151\n\U0001F48E Legendary: {len(legendary_counts)}/5\n"
            msg = bot.reply_to(message, response)
            threading.Timer(30, lambda: bot.delete_message(chat_id=group_id, message_id=msg.message_id)).start()
        else:
            msg = bot.reply_to(message, "\u26A0 You don't have any Pokémon captured.")
            threading.Timer(3, lambda: bot.delete_message(chat_id=group_id, message_id=msg.message_id)).start()
    except Exception as e:
        logger.error(f"Error during mycollection: {e}")

# Callback query handler for /chooseyou
@bot.message_handler(commands=['chooseyou'])
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
                        f"\U0001F3B2 {user_name} se le cayo una pokeball y {random_pkm_name} se salió!",
                        f"\U0001F3B2 {random_pkm_name} salió para ver memes!",
                        f"\U0001F3B2 {user_name} sacó a {random_pkm_name} mientras veia el canal NSFW!"]
            msg_rp = bot.send_message(
                group_id,
                random.choice(msg_list),
                message_thread_id=topic_id,
                parse_mode='HTML'
                )
            threading.Timer(30, lambda: bot.delete_message(chat_id=group_id, message_id=msg_rp.message_id)).start()
            threading.Timer(30, lambda: bot.delete_message(chat_id=message.chat.id, message_id=msg_st.message_id)).start()
        else:
            msg = bot.send_message(group_id, "\u26A0 No tienes pokémones capturados.", message_thread_id=topic_id)
            threading.Timer(3, lambda: bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)).start()
    except Exception as e:
        logger.error(f"Error during chooseyou: {e}")

# Callback query handler for /startcombat
@bot.message_handler(commands=['startcombat'])
def start_combat(message):
    try:
        if not check_active_hours():
            return
        username = message.from_user.username
        user_id = message.from_user.id
        if username in ongoing_combats:
            bot.reply_to(message, "\u26A0 Ya tienes un combate en curso.")
            return
        user_pokemon = userEvents.getRandomPokemonCaptured(username)
        if not user_pokemon:
            bot.reply_to(message, "\u26A0 No tienes Pokémon para combatir.")
            return
        ongoing_combats[username] = {"pokemon": user_pokemon, "opponent": None}
        keyboard = InlineKeyboardMarkup()
        duel_button = InlineKeyboardButton("Duel", callback_data=f"duel:{username}")
        keyboard.add(duel_button)
        msg = bot.send_message(group_id, f"\u2694 {username} ha iniciado un combate con *{user_pokemon['name']}* Lv.{user_pokemon['level']}!\nPresiona 'Duel' para enfrentarlo!", message_thread_id=topic_id, reply_markup=keyboard, parse_mode="Markdown")
        # Cancelar el combate después de 2 minutos si nadie lo acepta
        ongoing_combats[username]["message_id"] = msg.message_id
        def cancel_combat():
            if username in ongoing_combats and not ongoing_combats[username]['opponent']:
                bot.edit_message_text(
                    "\u23F3 El combate ha expirado.", 
                    group_id,
                    ongoing_combats[username]["message_id"]
                )
                threading.Timer(10, lambda: bot.delete_message(chat_id=group_id, message_id=ongoing_combats[username]["message_id"])).start()
                del ongoing_combats[username]
        threading.Timer(120, cancel_combat).start()
    except Exception as e:
        logger.error(f"Error during startcombat: {e}")

# Callback query handler for "Duel" button
@bot.callback_query_handler(func=lambda call: call.data.startswith("duel:"))
def accept_duel(call):
    try:
        challenger = call.data.split(":")[1]
        opponent = call.from_user.username
        if challenger not in ongoing_combats or ongoing_combats[challenger]["opponent"]:
            bot.answer_callback_query(call.id, "El duelo ya ha sido aceptado o ha expirado.")
            return
        if opponent == challenger:
            bot.answer_callback_query(call.id, "No puedes luchar contra ti mismo.")
            return
        opponent_pokemon = userEvents.getRandomPokemonCaptured(opponent)
        if not opponent_pokemon:
            bot.answer_callback_query(call.id, "No tienes Pokémon para combatir.")
            return
        ongoing_combats[challenger]["opponent"] = {"username": opponent, "pokemon": opponent_pokemon}
        # Determinar el resultado del combate
        combat_roll = random.randint(1, 100)
        level_check = ongoing_combats[challenger]['pokemon']['level'] - opponent_pokemon['level']
        challenger_advantage = pokemonEvents.get_type_advantage(ongoing_combats[challenger]['pokemon']['types'], opponent_pokemon['types'])
        opponent_advantage = pokemonEvents.get_type_advantage(opponent_pokemon['types'], ongoing_combats[challenger]['pokemon']['types'])
        type_modifier = challenger_advantage - opponent_advantage
        result = (combat_roll + level_check + type_modifier) < 50
        winner = opponent if result else challenger
        loser = challenger if result else opponent
        loser_pokemon = ongoing_combats[challenger]['pokemon'] if loser==challenger else opponent_pokemon
        userEvents.reducePokemonCaptured(loser, loser_pokemon)
        steal = random.randint(1,100) <= 5
        if steal:
            userEvents.addPokemonCaptured(loser_pokemon, winner)
        userEvents.updateCombatResults(winner, loser)
        bot.edit_message_text(
            f"\u2694 {challenger} ({ongoing_combats[challenger]['pokemon']['name']} Lv.{ongoing_combats[challenger]['pokemon']['level']}) vs {opponent} ({opponent_pokemon['name']} Lv.{opponent_pokemon['level']})!\n\n\U0001F3C6 {'¡' + opponent + ' gana!' if result else '¡' + challenger + ' gana!'}\n\n\u274C {loser} pierde un {loser_pokemon['name']}!{('\n\n\U0001F3C5 ' + winner + 'se queda con el pokemon!') if steal else ''}",
            call.message.chat.id, call.message.message_id
        )
        del ongoing_combats[challenger]
    except Exception as e:
        logger.error(f"Error in duel handling: {e}")

# Callback query handler for /profile
@bot.message_handler(commands=['profile'])
def profile(message):
    try:
        username = message.from_user.username
        if checkUserExistence(username):
            return
        user_data = userEvents.getUserByName(username)
        victories = user_data.get("victories", [])
        defeats = user_data.get("defeats", [])
        total_victories = sum(entry["count"] for entry in victories) if victories else 0
        total_defeats = sum(entry["count"] for entry in defeats) if defeats else 0
        victories_text = "\n\U0001F539 " + "\n\U0001F539 ".join(
            [f"{entry['opponent']}: {entry['count']}" for entry in victories]
        ) if victories else ""
        defeats_text = "\n\U0001F538 " + "\n\U0001F538 ".join(
            [f"{entry['opponent']}: {entry['count']}" for entry in defeats]
        ) if defeats else ""
        most_victories = max(victories, key=lambda x: x["count"])["opponent"] if victories else "Virgin"
        most_defeats = max(defeats, key=lambda x: x["count"])["opponent"] if defeats else "Undefeated"
        winrate = round((total_victories / (total_victories + total_defeats)) * 100, 2) if (total_victories + total_defeats) > 0 else 0
        # Mensaje de respuesta
        profile_text = (
            f"\U0001F4DC *{user_data["name"]} Profile*\n"
            f"\U0001F4E6 Pokemons Captured: {user_data["total_pokemons"]}\n"
            f"\U0001F31F Shiny Captured: {user_data["total_shiny"]}\n"
            f"\U0001F3AF Winrate: {winrate}%\n"
            f"\U0001F3C6 Victories:\nTotal: {total_victories}{victories_text}\n"
            f"\U0001F947 Most Victories: {most_victories}\n"
            f"\U0001F480 Defeats:\nTotal: {total_defeats}{defeats_text}\n"
            f"\U0001F635 Most Defeats: {most_defeats}"
        )
        msg = bot.reply_to(message, profile_text, parse_mode="Markdown")
        threading.Timer(30, lambda: bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)).start()
    except Exception as e:
        logger.error(f"Error mostrando perfil: {e}")
        msg = bot.reply_to(message, "\u26A0 Ocurrió un error al obtener tu perfil.")
        threading.Timer(5, lambda: bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)).start()

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
            logger.error(f"Error in auto-spawn: {e}")
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
        logger.error(f"Error monitoring message: {e}")

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
        logger.error(f"Error replacing message: {e}")
#----------------------------------------------------------------------------------------------------
# Initialization of the bot.
bot.infinity_polling()