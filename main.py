import telebot
import userEvents
import pokemonEvents
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import random
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
from collections import Counter
import time
from pymongo import MongoClient
from flask import Flask, request
#import config

#TELEGRAM_TOKEN = config.TELEGRAM_TOKEN
#CHANNEL_ID = config.CHANNEL_ID
#TOPIC_ID = config.TOPIC_ID

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

# Conexión a MongoDB Atlas (reemplaza el string con tu URI de Atlas)
#client = MongoClient(config.MONGO_URI)
client = MongoClient(MONGO_URI)
db = client.get_database()

# Inicializar Flask
app = Flask(__name__)

@app.route("/", methods=["GET"])  # Permitir solo GET
def home():
    return "Hello, world!", 200

# Ruta básica para evitar el error de puerto
@app.route("/", methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "¡OK!", 200

bot = telebot.TeleBot(TELEGRAM_TOKEN)
group_id = CHANNEL_ID
topic_id = TOPIC_ID
#capture_timers should save the timers of all spawned pokemons
capture_timers = {}
#capture spawned pokemons in the dictionary
spawned_pokemons = {}
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

#Function for the escaping pokemon
def pokemon_escape(pokemon, group_id, message_id):
    try:
        escape_msgs = [f"The wild Lv.{pokemon['level']} {'Genderless' if pokemon['gender'] == 'genderless' else pokemon['gender']} {'shiny ' if pokemon['isShiny'] else ''}{pokemon['name']} has escaped!",
                       f"Someone throw a rock and made the Lv.{pokemon['level']} {'Genderless' if pokemon['gender'] == 'genderless' else pokemon['gender']} {'shiny ' if pokemon['isShiny'] else ''}{pokemon['name']} escape!",
                       f"The wild Lv.{pokemon['level']} {'Genderless' if pokemon['gender'] == 'genderless' else pokemon['gender']} {'shiny ' if pokemon['isShiny'] else ''}{pokemon['name']} saw a bad meme and escaped!",
                       f"The wild Lv.{pokemon['level']} {'Genderless' if pokemon['gender'] == 'genderless' else pokemon['gender']} {'shiny ' if pokemon['isShiny'] else ''}{pokemon['name']} is a little scared and escaped!",
                       f"The wild Lv.{pokemon['level']} {'Genderless' if pokemon['gender'] == 'genderless' else pokemon['gender']} {'shiny ' if pokemon['isShiny'] else ''}{pokemon['name']} saw someone taking down their pants and escaped!",
                       f"The wild Lv.{pokemon['level']} {'Genderless' if pokemon['gender'] == 'genderless' else pokemon['gender']} {'shiny ' if pokemon['isShiny'] else ''}{pokemon['name']} dodged a pokeball and escaped!",
                       f"The wild Lv.{pokemon['level']} {'Genderless' if pokemon['gender'] == 'genderless' else pokemon['gender']} {'shiny ' if pokemon['isShiny'] else ''}{pokemon['name']} was in reality a fake doll!"]
        # Notify the group that the Pokémon escaped
        bot.edit_message_text(
            random.choice(escape_msgs),
            chat_id=group_id,
            message_id=message_id
        )
        if message_id in spawned_pokemons:
            del spawned_pokemons[message_id]
    except Exception as e:
        print(f"Error during escape notification: {e}")

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
        bot.set_my_commands(commands)
        bot.reply_to(message, "Hola, soy PokeGramBot!")
    except Exception as e:
        print(f"Error during start: {e}")

#shows some functions
@bot.message_handler(commands=['help'])
def generate_help_message(message):
    try:
        help_text = "Here are the commands you can use:\n\n"
        for command in commands:
            help_text += f"/{command['command']} - {command['description']}\n"
        help_text += f"\nEste bot es No Inclusivo, cualquier caso que pueda indicar lo contrario es un bug y será corregido."
        bot.reply_to(message, help_text)
    except Exception as e:
        print(f"Error during help: {e}")

#shows some functions
@bot.message_handler(commands=['chance'])
def generate_help_message(message):
    try:
        help_text = "Chance to Capture Pokemons (Used Lv.100 as reference):\nBase: 39%\nShiny:30%\nLegendary: 33%\nLegendary and Shiny: 25%\n\nIMPORTANT: This value can be used as reference but said chance is affected by a random value which lowers the rate!"
        bot.reply_to(message, help_text)
    except Exception as e:
        print(f"Error during help: {e}")

# Bot command handler for /register
@bot.message_handler(commands=['register'])
def register_command(message):
    try:
        username = message.from_user.username
        if not username:
            msg_cd = bot.reply_to(message, "No tienes un nombre de usuario en Telegram. Configúralo primero.")
            threading.Timer(5, lambda: bot.delete_message(chat_id=group_id, message_id=msg_cd.message_id)).start()
            return
        if userEvents.checkUserisRegistered(username):
            msg_cd = bot.reply_to(message, f"Usuario @{username} ya está registrado.")
            threading.Timer(10, lambda: bot.delete_message(chat_id=group_id, message_id=msg_cd.message_id)).start()
        else:
            msg_cd = bot.reply_to(message, f"Usuario @{username} registrado con éxito.")
            threading.Timer(5, lambda: bot.delete_message(chat_id=group_id, message_id=msg_cd.message_id)).start()
    except Exception as e:
        print(f"Error during registration: {e}")

# Bot command handler for /spawn
@bot.message_handler(commands=['spawn'])
def spawn_pokemon_handler(message):
    try:
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
            msg = bot.reply_to(message, "El Pokémon escapó mientras intentaste spawnearlo...")
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
        print(f"Error during spawn: {e}")

# Callback query handler for "Capture!" button
@bot.callback_query_handler(func=lambda call: call.data.startswith("capture:"))
def capture_pokemon_handler(call):
    try:
        username = call.from_user.username
        if not username:
            bot.answer_callback_query(call.id, "You don't have a Telegram username. Please set one to capture Pokémon.")
            return
        if not userEvents.checkUserisRegistered(username):
            msg = bot.send_message(call.message.chat.id, "You didn't register.", message_thread_id=topic_id)
            threading.Timer(2, lambda: bot.delete_message(chat_id=call.message.chat.id, message_id=msg.message_id)).start()
            return
        pokemon = spawned_pokemons.get(call.message.message_id)
        if pokemon is None:
            bot.answer_callback_query(call.id, "No Pokémon found.")
            return
        # Attempt to capture the Pokémon
        if captureCheck(pokemon) <= 80:
            userEvents.addPokemonCaptured(pokemon, username)  # Ensure this function is compatible with MongoDB Atlas
            if call.message.message_id in capture_timers:
                capture_timers[call.message.message_id].cancel()
                del capture_timers[call.message.message_id]
            bot.answer_callback_query(call.id, f"You captured a Lv.{pokemon['level']} {pokemon['gender']}{' shiny' if pokemon['isShiny'] else ''} {pokemon['name']}!")
            bot.edit_message_text(
                f"{call.from_user.first_name} captured a Lv.{pokemon['level']} {pokemon['gender']}{' shiny' if pokemon['isShiny'] else ''} {pokemon['name']}!",
                call.message.chat.id,
                call.message.message_id
            )
            del spawned_pokemons[call.message.message_id]
        else:
            bot.answer_callback_query(call.id, f"The Pokémon escaped from your hands!")
            pokemon_escape(pokemon, call.message.chat.id, call.message.message_id)
    except Exception as e:
        if "query is too old" in str(e):  # Handle expired callback queries gracefully
            print("Expired callback query: ignoring outdated interaction.")
        else:
            print(f"Error during capture: {e}")

# Callback query handler for /mypokemons
@bot.message_handler(commands=['mypokemons'])
def get_pokemons_by_user(message):
    try:
        username = message.from_user.username
        if not username:
            msg_cd = bot.reply_to(message, "You don't have a Telegram username. Please set one to see your Pokémon.")
            threading.Timer(5, lambda: bot.delete_message(chat_id=message.chat.id, message_id=msg_cd.message_id)).start()
            return
        if not userEvents.checkUserisRegistered(username):
            msg_cd = bot.reply_to(message, "You didn't register.")
            threading.Timer(5, lambda: bot.delete_message(chat_id=message.chat.id, message_id=msg_cd.message_id)).start()
            return
        pokemons = userEvents.getListOfPokemonCapturedByName(username)
        if pokemons:
            shiny_counter = 0
            for pokemon in pokemons:
                if pokemon["isShiny"]:
                    shiny_counter += 1
            response = f"Your Pokémon Collection:\n- Pokemons: {len(pokemons)} (Shiny: {shiny_counter})\n"
            bot.reply_to(message, response)
        else:
            bot.reply_to(message, "You don't have any Pokémon captured.")
    except Exception as e:
        print(f"Error during mypokemons: {e}")

# Callback query handler for /capturedpokemons
@bot.message_handler(commands=['capturedpokemons'])
def get_pokemons_by_user(message):
    try:
        username = message.from_user.username
        user_id = message.from_user.id
        if not username:
            msg_cd = bot.send_message(user_id, "You don't have a Telegram username. Please set one to see your Pokémon.")
            threading.Timer(5, lambda: bot.delete_message(chat_id=user_id, message_id=msg_cd.message_id)).start()
            return
        if not userEvents.checkUserisRegistered(username):
            msg_cd = bot.send_message(user_id, "You didn't register.")
            threading.Timer(5, lambda: bot.delete_message(chat_id=user_id, message_id=msg_cd.message_id)).start()
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
            # Format the message
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
        print(f"Error during capturedpokemons: {e}")

# Callback query handler for /mycollection
@bot.message_handler(commands=['mycollection'])
def get_pokemons_by_user(message):
    try:
        username = message.from_user.username
        if not username:
            msg_cd = bot.reply_to(message, "You don't have a Telegram username. Please set one to see your Pokémon.")
            threading.Timer(5, lambda: bot.delete_message(chat_id=message.chat.id, message_id=msg_cd.message_id)).start()
            return
        if not userEvents.checkUserisRegistered(username):
            msg_cd = bot.reply_to(message, "You didn't register.")
            threading.Timer(5, lambda: bot.delete_message(chat_id=message.chat.id, message_id=msg_cd.message_id)).start()
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
            bot.reply_to(message, response)
        else:
            bot.reply_to(message, "You don't have any Pokémon captured.")
    except Exception as e:
        print(f"Error during mycollection: {e}")

# Bot command handler for /freemypokemons
@bot.message_handler(commands=['freemypokemons'])
def register_command(message):
    try:
        username = message.from_user.username
        if not username:
            msg_cd = bot.reply_to(message, "No tienes un nombre de usuario en Telegram. Configúralo primero.")
            threading.Timer(5, lambda: bot.delete_message(chat_id=message.chat.id, message_id=msg_cd.message_id)).start()
            return
        userEvents.freeAllPokemons(username)
        msg = bot.reply_to(message, f"Usuario @{username} liberó a todos sus pokémones!")
        threading.Timer(30, lambda: bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)).start()
    except Exception as e:
        print(f"Error during freemypokemons: {e}")

# Callback query handler for /chooseyou
@bot.message_handler(commands=['chooseyou'])
def summon_pokemon(message):
    try:
        username = message.from_user.username
        if not username:
            msg_cd = bot.reply_to(message, "No tienes un nombre de usuario en Telegram. Configúralo primero.")
            threading.Timer(5, lambda: bot.delete_message(chat_id=message.chat.id, message_id=msg_cd.message_id)).start()
            return
        if not userEvents.checkUserisRegistered(username):
            msg_cd = bot.reply_to(message, "No has registrado.")
            threading.Timer(5, lambda: bot.delete_message(chat_id=message.chat.id, message_id=msg_cd.message_id)).start()
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
            msg_rp = bot.send_message(
                group_id,
                f"{user_name} ha elegido a {random_pkm_name}!",
                message_thread_id=topic_id,
                parse_mode='HTML'
                )
            threading.Timer(30, lambda: bot.delete_message(chat_id=group_id, message_id=msg_rp.message_id)).start()
            threading.Timer(30, lambda: bot.delete_message(chat_id=message.chat.id, message_id=msg_st.message_id)).start()
    except Exception as e:
        print(f"Error during chooseyou: {e}")

class MockMessage:
    def __init__(self):
        self.from_user = type('User', (), {'id': 0})  # Replace with a valid user ID
        self.chat = type('Chat', (), {'id': group_id})     # Replace with your group ID
        self.message_id = 1
# Automatically send the command /spawn with the bot every 10 minutes
def auto_spawn_event():
    while True:
        try:
            # Crea un mensaje simulado
            mock_message = MockMessage()  # Puedes pasar un username y group_id personalizado aquí
            spawn_pokemon_handler(mock_message)  # Llama al manejador de spawn
            time.sleep(600)  # Espera 10 minutos antes de ejecutar de nuevo
        except Exception as e:
            print(f"Error in auto-spawn: {e}")
# Inicia el evento en un hilo separado
spawn_thread = threading.Thread(target=auto_spawn_event, daemon=True)
spawn_thread.start()

# From this point onwards there will not be more documentation or comment lines explaining anything.
# If you get any error, update, fix or delete the code yourself.
# From this point onwards there will not be more documentation or comment lines explaining anything.
# If you get any error, update, fix the code yourself.
# Monitor message handler
@bot.message_handler(func=lambda message: True)
def monitor_messages(message):
    try:
        if "(?" in message.text:
            threading.Timer(2.0, replace_message, args=[message]).start()
    except Exception as e:
        print(f"Error monitoring message: {e}")

def replace_message(message):
    try:
        mod_text_list = [
            "? Por cierto, soy puto.",
            "? Me encanta tragar sables",
            "? Puto el que lee.",
            "? Ojala que llueva para vergotas."]
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
        print(f"Error replacing message: {e}")

# Initialization of the bot.
# Hilo separado para el bot
def start_bot():
    bot.infinity_polling()

def start_server():
    port = int(os.environ.get("PORT", 10000))
    handler = SimpleHTTPRequestHandler
    httpd = HTTPServer(("0.0.0.0", port), handler)
    print(f"Servidor HTTP corriendo en el puerto {port}")
    httpd.serve_forever()

if __name__ == "__main__":
    # Ejecutar el bot y el servidor HTTP en hilos separados
    threading.Thread(target=start_bot).start()
    threading.Thread(target=start_server).start()