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
#commands

commands=[
    {"command": "help", "description": "Get the list of commands."},
    {"command": "start", "description": "The bot starts and says hi."},
    {"command": "register", "description": "Register your username."},
    {"command": "spawn", "description": "Spawn a random Pokemon. Each user can spawn once a minute."},
    {"command": "mypokemons", "description": "Show how many Pokemons, normal and shiny, you captured."},
    {"command": "capturedpokemons", "description": "Show your captured Pokemon with deatails."},
    {"command": "mycollection", "description": "Show how many type of Pokemons you have captured."},
    {"command": "freemypokemons", "description": "Free all your Pokemons. (WARNING: It is irreversible!)"},
    {"command": "chance", "description": "Show the chance to capture pokemons.)"},
    {"command": "chooseyou", "description": "Summon a random pokemon from the user.)"}
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
        msg_cd = bot.send_message(group_id, "You don't have a Telegram username. Please set one to see your Pokémon.",message_thread_id=topic_id)
        threading.Timer(5, lambda: bot.delete_message(chat_id=group_id, message_id=msg_cd.message_id)).start()
        return True
    if not userEvents.checkUserisRegistered(username):
        msg_cd = bot.send_message(group_id, "You didn't register.",message_thread_id=topic_id)
        threading.Timer(5, lambda: bot.delete_message(chat_id=group_id, message_id=msg_cd.message_id)).start()
        return True
    return False

#Function to check if its time for the bot to work
def is_active_hours():
    #Add your own time
    argentina_tz = pytz.timezone('America/Argentina/Buenos_Aires')
    current_hour = datetime.now(argentina_tz).hour
    return 10 <= current_hour < 24  # Solo funciona de 10:00 a 23:59

def check_active_hours():
    if not is_active_hours():
        bot.send_message(group_id, "Sorry, the bot is not active at the moment. It works from 10:00 to 22:59.",message_thread_id=topic_id)
        return False
    return True

#Function for the escaping pokemon
def pokemon_escape(pokemon, group_id, message_id):
    try:
        escape_msgs = [f"The wild Lv.{pokemon['level']} {'Genderless' if pokemon['gender'] == 'genderless' else pokemon['gender']} {'shiny ' if pokemon['isShiny'] else ''}{pokemon['name']} has escaped!",
                       f"Someone throw a rock and made the Lv.{pokemon['level']} {'Genderless' if pokemon['gender'] == 'genderless' else pokemon['gender']} {'shiny ' if pokemon['isShiny'] else ''}{pokemon['name']} escape!",
                       f"The wild Lv.{pokemon['level']} {'Genderless' if pokemon['gender'] == 'genderless' else pokemon['gender']} {'shiny ' if pokemon['isShiny'] else ''}{pokemon['name']} saw a bad meme and escaped!",
                       f"The wild Lv.{pokemon['level']} {'Genderless' if pokemon['gender'] == 'genderless' else pokemon['gender']} {'shiny ' if pokemon['isShiny'] else ''}{pokemon['name']} is a little scared and escaped!",
                       f"The wild Lv.{pokemon['level']} {'Genderless' if pokemon['gender'] == 'genderless' else pokemon['gender']} {'shiny ' if pokemon['isShiny'] else ''}{pokemon['name']} saw someone taking down their pants and escaped!",
                       f"The wild Lv.{pokemon['level']} {'Genderless' if pokemon['gender'] == 'genderless' else pokemon['gender']} {'shiny ' if pokemon['isShiny'] else ''}{pokemon['name']} dodged a pokeball and escaped!",
                       f"The wild Lv.{pokemon['level']} {'Genderless' if pokemon['gender'] == 'genderless' else pokemon['gender']} {'shiny ' if pokemon['isShiny'] else ''}{pokemon['name']} was in reality a fake doll!",
                       f"The wild Lv.{pokemon['level']} {'Genderless' if pokemon['gender'] == 'genderless' else pokemon['gender']} {'shiny ' if pokemon['isShiny'] else ''}{pokemon['name']} was in reality a Ditto and has escaped!",
                       f"A pokeball was thrown too hard and killed the Lv.{pokemon['level']} {'Genderless' if pokemon['gender'] == 'genderless' else pokemon['gender']} {'shiny ' if pokemon['isShiny'] else ''}{pokemon['name']}!",
                       f"The wild Lv.{pokemon['level']} {'Genderless' if pokemon['gender'] == 'genderless' else pokemon['gender']} {'shiny ' if pokemon['isShiny'] else ''}{pokemon['name']} killed itself to not be captured!"]
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
        bot.reply_to(message, "Hola, soy PokeGramBot!")
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
            help_text += f"/{command['command']} - {command['description']}\n"
        help_text += f"\nEste bot es No Inclusivo, cualquier caso que pueda indicar lo contrario es un bug y será corregido."
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
        help_text = "Chance to Capture Pokemons\nLevel 1:\nBase: 80%\nShiny:56%\nLegendary:64%\n\nLevel 100:\nBase: 39%\nShiny:30%\nLegendary: 33%\nLegendary and Shiny: 25%\n\nIMPORTANT: This value can be used as reference but said chance is affected by a random value which lowers the rate!"
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
            msg_cd = bot.reply_to(message, "No tienes un nombre de usuario en Telegram. Configúralo primero.")
            threading.Timer(5, lambda: bot.delete_message(chat_id=group_id, message_id=msg_cd.message_id)).start()
            return
        if userEvents.checkUserisRegistered(username):
            msg_cd = bot.reply_to(message, f"Usuario @{username} ya está registrado.")
            threading.Timer(5, lambda: bot.delete_message(chat_id=group_id, message_id=msg_cd.message_id)).start()
        else:
            msg_cd = bot.reply_to(message, f"Usuario @{username} registrado con éxito.")
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
                    f"You're on cooldown! Please wait {int(remaining_time)} seconds before spawning another Pokémon."
                )
                threading.Timer(2, lambda: bot.delete_message(chat_id=group_id, message_id=msg_cd.message_id)).start()
                return
        last_spawn_times[user_id] = current_time
        total_pokemons = len(spawned_pokemons)
        if total_pokemons >= 2:
            msg = bot.reply_to(message, "No puedes spawnear más Pokémones. Se alcanzado el límite (2).")
            threading.Timer(2, lambda: bot.delete_message(chat_id=group_id, message_id=msg.message_id)).start()
            return
        spawn_check = random.randint(1,100)
        if spawn_check <= 10:
            msg = bot.reply_to(message, "El Pokémon escapó al intentar spawnearlo...")
            threading.Timer(2, lambda: bot.delete_message(chat_id=group_id, message_id=msg.message_id)).start()
            return
        pokemon = pokemonEvents.generatePokemon()
        pokemon_image = f"./pokemon_sprites{'_shiny' if pokemon['isShiny']==True else ''}/{pokemon['id']}.webp"
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
                f"A wild {pokemon_name}{' shiny' if pokemon['isShiny'] else ''} appeared! What will you do?\nGender: {'Genderless' if pokemon['gender']=='genderless' else 'Male' if pokemon['gender']=='male' else 'Female'}\nLevel: {pokemon['level']}",
                reply_markup=generate_capture_button(pokemon["id"]),
                message_thread_id=topic_id,
                parse_mode='Markdown'
            )
            spawned_pokemons[msg.message_id] = pokemon
            timer = threading.Timer(60.0, pokemon_escape, args=[pokemon, group_id, msg.message_id])
            capture_timers[msg.message_id] = timer
            timer.start()
        else:
            bot.reply_to(message, "Failed to spawn a Pokémon.")
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
            msg_list = ["Too late! Someone else captured the Pokémon.", "Yasper, otro lo agarró!"]
            bot.answer_callback_query(call.id, random.choice(msg_list))
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
                f"{call.from_user.first_name} captured a Lv.{pokemon['level']} {pokemon['gender']}{' shiny' if pokemon['isShiny'] else ''} {pokemon['name']}!",
                call.message.chat.id,
                call.message.message_id
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
        pokemons = userEvents.getListOfPokemonCapturedByName(username)
        if pokemons:
            shiny_counter = 0
            for pokemon in pokemons:
                if pokemon["isShiny"]:
                    shiny_counter += 1
            response = f"Your Pokémon Collection:\n- Pokemons: {len(pokemons)} (Shiny: {shiny_counter})\n"
            msg = bot.reply_to(message, response)
            threading.Timer(30, lambda: bot.delete_message(chat_id=group_id, message_id=msg.message_id)).start()
        else:
            msg = bot.reply_to(message, "You don't have any Pokémon captured.")
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
        pokemons = userEvents.getListOfPokemonCapturedByName(username)
        if pokemons:
            pokemons = sorted(pokemons, key=lambda x: x["id"])
            pokemon_counts = Counter()
            shiny_counts = Counter()
            max_levels = {}
            pokemon_ids = {}
            for pokemon in pokemons:
                pokemon_counts[pokemon["name"]] += 1
                if pokemon["isShiny"]:
                    shiny_counts[pokemon["name"]] += 1
                if pokemon["name"] not in max_levels or pokemon["level"] > max_levels[pokemon["name"]]:
                    max_levels[pokemon["name"]] = pokemon["level"]
                    pokemon_ids[pokemon["name"]] = pokemon["id"]
            response = "Your Pokémon Collection:\n"
            for pokemon_name, count in pokemon_counts.items():
                shiny_count = shiny_counts[pokemon_name]
                max_level = max_levels[pokemon_name]
                pokemon_id = pokemon_ids[pokemon_name]
                response += f"-|#{pokemon_id} - {pokemon_name}: {count} (Shiny: {shiny_count}) (Max Lv.: {max_level})|\n"
            bot.send_message(user_id, response)
        else:
            bot.send_message(user_id, "You don't have any Pokémon captured.")
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
        pokemons = userEvents.getListOfPokemonCapturedByName(username)
        pokemon_counts = {}
        shiny_counts = {}
        legendary_counts = {}
        if pokemons:
            for pokemon in pokemons:
                pokemon_counts[pokemon["name"]] = pokemon["id"]
                if pokemon["name"] not in shiny_counts and pokemon["isShiny"] == True:
                    shiny_counts[pokemon["name"]] = pokemon["id"]
                if pokemon["name"] not in legendary_counts and pokemon["isLegendary"] == True:
                    legendary_counts[pokemon["name"]] = pokemon["id"]
            response = f"Pokémons Collected: {len(pokemon_counts)}/151\nShiny: {len(shiny_counts)}/151\nLegendary: {len(legendary_counts)}/5\n"
            msg = bot.reply_to(message, response)
            threading.Timer(30, lambda: bot.delete_message(chat_id=group_id, message_id=msg.message_id)).start()
        else:
            msg = bot.reply_to(message, "You don't have any Pokémon captured.")
            threading.Timer(3, lambda: bot.delete_message(chat_id=group_id, message_id=msg.message_id)).start()
    except Exception as e:
        logger.error(f"Error during mycollection: {e}")

# Bot command handler for /freemypokemons
@bot.message_handler(commands=['freemypokemons'])
def register_command(message):
    try:
        if not check_active_hours():
            return
        username = message.from_user.username
        if checkUserExistence(username):
            return
        userEvents.freeAllPokemons(username)
        msg = bot.reply_to(message, f"Usuario @{username} liberó a todos sus pokémones!")
        threading.Timer(30, lambda: bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)).start()
    except Exception as e:
        logger.error(f"Error during freemypokemons: {e}")

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
            random_pkm_img = f"./pokemon_sprites{'_shiny' if random_pokemon['isShiny']==True else ''}/{random_pokemon['id']}.webp"
            # bot message with the image of the pokemon
            if os.path.exists(random_pkm_img):
                with open(random_pkm_img, 'rb') as photo:
                    msg_st = bot.send_sticker(
                        group_id,
                        photo,
                        message_thread_id=topic_id
                    )
            msg_list = [f"{user_name} ha elegido a {random_pkm_name}!",
                        f"{user_name} se le cayo una pokeball y {random_pkm_name} se salió!",
                        f"{random_pkm_name} salió para ver memes!",
                        f"{user_name} sacó a {random_pkm_name} mientras veia el canal NSFW!"]
            msg_rp = bot.send_message(
                group_id,
                random.choice(msg_list),
                message_thread_id=topic_id,
                parse_mode='HTML'
                )
            threading.Timer(30, lambda: bot.delete_message(chat_id=group_id, message_id=msg_rp.message_id)).start()
            threading.Timer(30, lambda: bot.delete_message(chat_id=message.chat.id, message_id=msg_st.message_id)).start()
    except Exception as e:
        logger.error(f"Error during chooseyou: {e}")

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
            time.sleep(600)  # wait 10 minutes
        except Exception as e:
            logger.error(f"Error in auto-spawn: {e}")
# start the event in a different thread
spawn_thread = threading.Thread(target=auto_spawn_event, daemon=True)
spawn_thread.start()

# From this line until the next line there will not be more documentation or comment lines explaining anything.
#----------------------------------------------------------------------------------------------------
# If you get any error then update, fix or delete the code yourself.
@bot.message_handler(func=lambda message: True)
def monitor_messages(message):
    try:
        if "(?" in message.text:
            threading.Timer(2.0, replace_message, args=[message]).start()
    except Exception as e:
        logger.error(f"Error monitoring message: {e}")

def replace_message(message):
    try:
        mod_text_list = [
            "? Por cierto, soy puto.",
            "? Me encanta tragar sables",
            "? Puto el que lee.",
            "? Ojala que llueva para vergotas.",
            "? A Nisman lo mataron."]
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