# PokeGramBot
# Telegram Bot - Pokémon Capture Game

This is a Telegram bot that allows users to capture, view, and interact with virtual Pokémon. The bot provides various commands to interact with the game, including capturing random Pokémon, viewing your collection, and more.

## Features

- **/capturedpokemons**: Show your captured Pokémon along with their details.
- **/chance**: Show your chances of capturing Pokémon.
- **/chooseyou**: Summon a random Pokémon from your collection.
- **/help**: Get a list of available commands.
- **/mycollection**: Show the number of different Pokémon types you've captured.
- **/mypokemons**: Show the number of Pokémon you have captured (normal and shiny).
- **/profile**: Shows the profile of the user.
- **/register**: Register your username to start using the bot.
- **/spawn**: Spawn a random Pokémon. Each user can spawn once per minute.
- **/start**: The bot and greets the user.
- **/startcombat**: Start a combat with a random Pokemon. Whoever loses loses a pokemon. There is a chance that the winner keeps the loser's pokemon

Aside of those, the bot functions only between 10 AM and 23 PM (GMT-3). It also sends automatically a spawn command every 10 minutes.

## Important
The bot contains some functions that should be deleted by the user in case they dont want it. Such as th function to replace '(?' with mean messages. And a function to delete a random Pokemon if using '( ?'

## Requirements

- Python 3.8+
- `python-telegram-bot` library
- `pytz` for timezone handling (optional, if using time-based features)
- MongoDB for storing user and Pokémon data

### Install the dependencies

To install the necessary libraries, run the following command:

```bash
pip install -r requirements.txt
