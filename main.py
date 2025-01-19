import telebot
from config import TELEGRAM_TOKEN
from config import CHANNEL_ID
from config import TOPIC_ID
import userEvents
import pokemonEvents
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import random
import threading
from collections import Counter

bot = telebot.TeleBot(TELEGRAM_TOKEN)
group_id = CHANNEL_ID
topic_id = TOPIC_ID
#capture_timers should save the timers of all spawned pokemons
capture_timers = {}
#capture spawned pokemons in the dictionary
spawned_pokemons = {}
#commands
commands=[
    {"command": "help", "description": "Get the list of commands."},
    {"command": "start", "description": "The bot starts and says hi."},
    {"command": "register", "description": "Register your username."},
    {"command": "spawn", "description": "Spawn a random Pokemon"},
    {"command": "mypokemons", "description": "Show your captured Pokemon"},
]

#General functions
# Generate an inline keyboard with a "Capture!" button
def generate_capture_button(pokemonId):
    markup = InlineKeyboardMarkup()
    button = InlineKeyboardButton("Capture!", callback_data=f"capture:{pokemonId}")
    markup.add(button)
    return markup

#Function for the escaping pokemon
def pokemon_escape(pokemon, group_id, topic_id, message_id):
    try:
        # Delete the original Pokémon message
        bot.delete_message(group_id, message_id)
        # Notify the group that the Pokémon escaped
        bot.send_message(
            group_id,
            f"The wild Lv.{pokemon["level"]} {pokemon["gender"]}{" ✨shiny"if pokemon["isShiny"] else ""} {pokemon["name"]} has escaped!",
            message_thread_id=topic_id
        )
    except Exception as e:
        print(f"Error during escape notification: {e}")

#Functions for the bot
#The bot start and says hi
@bot.message_handler(commands=['start'])
def start(message):
    bot.set_my_commands(commands)
    bot.reply_to(message, "Hola, soy PokeGramBot!")

#shows some functions
@bot.message_handler(commands=['help'])
def generate_help_message(message):
    help_text = "Here are the commands you can use:\n\n"
    for command in commands:
        help_text += f"/{command['command']} - {command['description']}\n"
    bot.reply_to(message, help_text)

# Bot command handler for /register
@bot.message_handler(commands=['register'])
def register_command(message):
    username = message.from_user.username
    if not username:
        bot.reply_to(message, "No tienes un nombre de usuario en Telegram. Configúralo primero.")
        return
    if userEvents.registerUser(username)==True:
        bot.reply_to(message, f"Usuario @{username} registrado con éxito.")
    else:
        bot.reply_to(message, f"Usuario @{username} ya está registrado.")

# Bot command handler for /spawn
@bot.message_handler(commands=['spawn'])
def spawn_pokemon_handler(message):
    spawn_check = random.randint(1,100)
    if spawn_check <= 20:
        bot.reply_to(message, "El Pokémon escapó mientras intentaste spawnearlo...")
        return
    pokemon = pokemonEvents.generatePokemon()
    pokemon_image = f"./pokemon_sprites{"_shiny" if pokemon["isShiny"]==True else ""}/{pokemon["id"]}.webp"
    if pokemon:
        if os.path.exists(pokemon_image):
            with open(pokemon_image, 'rb') as photo:
                bot.send_sticker(
                    group_id,
                    photo,
                    message_thread_id=topic_id
                )
        msg = bot.send_message(
            group_id,
            f"A wild {pokemon["name"]}{" ✨shiny" if pokemon["isShiny"] else ""} appeared! What will you do?\nGender: {"Male" if pokemon["gender"]=="male" else "Female"}\nLevel: {pokemon["level"]}",
            reply_markup=generate_capture_button(pokemon["id"]),
            message_thread_id=topic_id
        )
        spawned_pokemons[msg.message_id] = pokemon
        timer = threading.Timer(60.0, pokemon_escape, args=[pokemon, group_id, topic_id, msg.message_id])
        capture_timers[msg.message_id] = timer
        timer.start()
    else:
        bot.reply_to(message, "Failed to spawn a Pokémon.")

# Callback query handler for "Capture!" button
@bot.callback_query_handler(func=lambda call: call.data.startswith("capture:"))
def capture_pokemon_handler(call):
    username = call.from_user.username
    if not username:
        bot.answer_callback_query(call.id, "You don't have a Telegram username. Please set one to capture Pokémon.")
        return
    if userEvents.checkUserisRegistered(username) == False:
        bot.send_message(group_id, "You didn't registered.",message_thread_id=topic_id)
        return
    pokemon = spawned_pokemons.get(call.message.message_id)
    if pokemon is None:
        bot.answer_callback_query(call.id, "No Pokémon found.")
        return
    # Attempt to capture the Pokémon
    capture_check = round((random.uniform(1,100) * (1 + pokemon["level"]/100)), 2)
    if pokemon["isShiny"]:
        capture_check *= 1.2
    if pokemon["isLegendary"]:
        capture_check *= 1.2
    if capture_check <= 80:
        if userEvents.addPokemonCaptured(pokemon, username)==True:
            if call.message.message_id in capture_timers:
                capture_timers[call.message.message_id].cancel()
                del capture_timers[call.message.message_id]
            bot.answer_callback_query(call.id, f"You captured a Lv.{pokemon["level"]} {pokemon["gender"]}{" ✨shiny"if pokemon["isShiny"] else ""} {pokemon["name"]}!")
            bot.edit_message_text(
            f"{call.from_user.first_name} captured a Lv.{pokemon["level"]} {pokemon["gender"]}{" ✨shiny"if pokemon["isShiny"] else ""} {pokemon["name"]}!",
            call.message.chat.id,
            call.message.message_id
            )
        else:
            bot.answer_callback_query(call.id, "You already captured this Pokémon.")
    else:
        bot.answer_callback_query(call.id, f"The Pokémon escaped!")
        pokemon_escape(pokemon, call.message.chat.id, topic_id, call.message.message_id)

# Callback query handler for /mypokemons
@bot.message_handler(commands=['mypokemons'])
def get_pokemons_by_user(message):
    username = message.from_user.username
    if not username:
        bot.reply_to(message, "You don't have a Telegram username. Please set one to see your Pokémon.")
        return
    if userEvents.checkUserisRegistered(username) == False:
        bot.reply_to(message, "You didn't registered.")
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

# Callback query handler for /mypokemons
@bot.message_handler(commands=['mypokemonsall'])
def get_pokemons_by_user(message):
    username = message.from_user.username
    user_id = message.from_user.id
    if not username:
        bot.send_message(user_id, "You don't have a Telegram username. Please set one to see your Pokémon.")
        return
    if userEvents.checkUserisRegistered(username) == False:
        bot.send_message(user_id, "You didn't registered.")
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
            response += f"-|{pokemon_name}: {count} (Shiny: {shiny_count}) (Max Lv.: {max_level}) #{pokemon_id}|\n"
        bot.send_message(user_id, response)
    else:
        bot.send_message(user_id, "You don't have any Pokémon captured.")


bot.polling()