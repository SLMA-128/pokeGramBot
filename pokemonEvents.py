import random
import json
import os

#Check the existence of the pokemon database
def checkPokemonsExists():
    try:
        if not os.path.exists("./pokemons.json"):
            with open("./pokemons.json", 'w') as file:
                json.dump({}, file)
    except Exception as e:
        print(f"Error checking the existence of the Pokémon database: {e}")

#Get a pokemon from the database using its ID
def getPokemonNameById(pokemonId):
    try:
        with open("./pokemons.json", 'r') as file:
            pokemons = json.load(file)
        for pokemon in pokemons:
            if pokemon["id"]==pokemonId:
                return pokemon["name"]
    except Exception as e:
        print(f"Error getting the Pokémon by ID: {e}")

#Check if a pokemon is legendary by its ID
def checkLegendary(pokemonId):
    try:
        with open("./pokemons.json", 'r') as file:
            pokemons = json.load(file)
        for pokemon in pokemons:
            if pokemon["id"]==pokemonId:
                return pokemon["isLegendary"]
    except Exception as e:
        print(f"Error checking if the Pokémon is legendary: {e}")

#Get the gender of a pokemon by its ID
def getGender(pokemonId):
    try:
        with open("./pokemons.json", 'r') as file:
            pokemons = json.load(file)
        for pokemon in pokemons:
            if pokemon["id"]==pokemonId:
                return random.choice(pokemon["gender"])
    except Exception as e:
        print(f"Error getting the gender of the Pokémon: {e}")

#Generate a new random pokemon with its ID, name, shiny status, legendary status, level, and gender
def generatePokemon():
    try:
        pokemonId = random.randint(1, 151)
        isShiny_check = random.randint(1,1000)
        isLegendary_check = checkLegendary(pokemonId)
        pokemon = {
            "id": pokemonId,
            "name": getPokemonNameById(pokemonId),
            "isShiny": isShiny_check <= 10,
            "isLegendary": isLegendary_check,
            "level": random.randint(1, 100),
            "gender": getGender(pokemonId)
        }
        return pokemon
    except Exception as e:
        print(f"Error generating a new Pokémon: {e}")