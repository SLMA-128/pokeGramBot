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
def pokemon_escape(pokemonId, group_id, topic_id, message_id):
    pokemonName = pokemonEvents.getPokemonNameById(pokemonId)
    try:
        # Delete the original Pokémon message
        bot.delete_message(group_id, message_id)
        # Notify the group that the Pokémon escaped
        bot.send_message(
            group_id,
            f"The wild {pokemonName} has escaped!",
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
    pokemonId = pokemonEvents.spawnPokemon()
    pokemonName = pokemonEvents.getPokemonNameById(pokemonId)
    pokemon = pokemonEvents.generatePokemon(pokemonId)
    pokemon_image = f"./pokemon_sprites{"_shiny" if pokemon["isShiny"]==True else ""}/{pokemonId}.webp"
    if pokemonName:
        if os.path.exists(pokemon_image):
            with open(pokemon_image, 'rb') as photo:
                bot.send_sticker(
                    group_id,
                    photo,
                    message_thread_id=topic_id
                )
        msg = bot.send_message(
            group_id,
            f"A wild {pokemonName}{" shiny" if pokemon["isShiny"] else ""} appeared! What will you do?",
            reply_markup=generate_capture_button(pokemonId),
            message_thread_id=topic_id
        )
        spawned_pokemons[msg.message_id] = pokemon
        timer = threading.Timer(60.0, pokemon_escape, args=[pokemonId, group_id, topic_id, msg.message_id])
        capture_timers[msg.message_id] = timer
        timer.start()
    else:
        bot.reply_to(message, "Failed to spawn a Pokémon.")

# Callback query handler for "Capture!" button
@bot.callback_query_handler(func=lambda call: call.data.startswith("capture:"))
def capture_pokemon_handler(call):
    pokemonId = int(call.data.split(":")[1])
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
    capture_check = random.randint(1,100)
    if capture_check <= 70:
        if userEvents.addPokemonCaptured(pokemon, username)==True:
            pokemonName = pokemon["name"]
            if call.message.message_id in capture_timers:
                capture_timers[call.message.message_id].cancel()
                del capture_timers[call.message.message_id]
            bot.answer_callback_query(call.id, f"You captured a{" ✨shiny"if pokemon["isShiny"] else ""} {pokemonName}!")
            bot.edit_message_text(
            f"{call.from_user.first_name} captured a{" ✨shiny"if pokemon["isShiny"] else ""} {pokemonName}!",
            call.message.chat.id,
            call.message.message_id
            )
        else:
            bot.answer_callback_query(call.id, "You already captured this Pokémon.")
    else:
        bot.edit_message_text(
            f"{call.from_user.first_name} failed to capture {pokemonEvents.getPokemonNameById(pokemonId)} and has escaped...",
            call.message.chat.id,
            call.message.message_id)

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
        pokemon_counts = Counter()
        shiny_counts = Counter()
        for pokemon in pokemons:
            pokemon_counts[pokemon["name"]] += 1
            if pokemon["isShiny"]:
                shiny_counts[pokemon["name"]] += 1
        # Format the message
        response = "Your Pokémon Collection:\n"
        for pokemon_name, count in pokemon_counts.items():
            shiny_count = shiny_counts[pokemon_name]
            response += f"- {pokemon_name}: {count} (Shiny: {shiny_count})\n"

        bot.reply_to(message, response)
    else:
        bot.reply_to(message, "You don't have any Pokémon captured.")

bot.polling()