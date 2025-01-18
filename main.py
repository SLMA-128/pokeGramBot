import telebot
from config import TELEGRAM_TOKEN
from config import CHANNEL_ID
from config import TOPIC_ID
import userEvents
import pokemonEvents
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import threading

bot = telebot.TeleBot(TELEGRAM_TOKEN)
group_id = CHANNEL_ID
topic_id = TOPIC_ID
#capture_timers should save the timers of all spawned pokemons
capture_timers = {}
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
def pokemon_escape(pokemonId, chat_id, message_id):
    pokemonName = pokemonEvents.getPokemonNameById(pokemonId)
    bot.edit_message_text(
        f"The wild {pokemonName} has escaped!",
        group_id,
        message_id,
        message_thread_id=topic_id
    )

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
    pokemonId = pokemonEvents.spawnPokemon()
    pokemonName = pokemonEvents.getPokemonNameById(pokemonId)
    pokemon_image = f"./pokemon_sprites_webp/{pokemonId}.webp"
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
            f"A wild {pokemonName} appeared! What will you do?",
            reply_markup=generate_capture_button(pokemonId),
            message_thread_id=topic_id
        )
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
    # Attempt to capture the Pokémon
    if userEvents.addPokemonCaptured(pokemonId, username)==True:
        pokemonName = pokemonEvents.getPokemonNameById(pokemonId)
        if call.message.message_id in capture_timers:
            capture_timers[call.message.message_id].cancel()
            del capture_timers[call.message.message_id]
        bot.answer_callback_query(call.id, f"You captured a {pokemonName}!")
        bot.edit_message_text(
            f"{call.from_user.first_name} captured a {pokemonName}!",
            call.message.chat.id,
            call.message.message_id
        )
    else:
        bot.answer_callback_query(call.id, "You already captured this Pokémon.")

# Callback query handler for /mypokemons
@bot.message_handler(commands=['mypokemons'])
def get_pokemons_by_user(message):
    username = message.from_user.username
    if not username:
        bot.reply_to(message, "You don't have a Telegram username. Please set one to see your Pokémon.")
        return
    pokemons = userEvents.getListOfPokemonCapturedByName(username)
    print("hi")
    if pokemons:
        pokemon_names = [pokemonEvents.getPokemonNameById(pokemon_id) for pokemon_id in pokemons]
        pokemons_list = "\n".join(pokemon_names)
        bot.send_message(group_id, f"Your captured Pokémon:\n{pokemons_list}")
    else:
        bot.reply_to(message, "You don't have any Pokémon captured.")

bot.polling()