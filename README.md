# PokeGramBot
# Telegram Bot - Pokémon Capture Game

This is a Telegram bot that allows users to capture, view, and interact with virtual Pokémon. The bot provides various commands to interact with the game, including capturing random Pokémon, viewing your collection, and more.

## Features

- **/help**: Get a list of available commands.
- **/start**: Starts the bot and greets the user.
- **/register**: Register your username to start using the bot.
- **/spawn**: Spawn a random Pokémon. Each user can spawn once per minute.
- **/mypokemons**: Show the number of Pokémon you have captured (normal and shiny).
- **/capturedpokemons**: Show your captured Pokémon along with their details.
- **/mycollection**: Show the number of different Pokémon types you've captured.
- **/freemypokemons**: Free all your Pokémon (WARNING: This is irreversible!).
- **/chance**: Show your chances of capturing Pokémon.
- **/chooseyou**: Summon a random Pokémon from your collection.

## Requirements

- Python 3.8+
- `python-telegram-bot` library
- `pytz` for timezone handling (optional, if using time-based features)
- MongoDB for storing user and Pokémon data

### Install the dependencies

To install the necessary libraries, run the following command:

```bash
pip install -r requirements.txt
