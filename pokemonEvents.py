import random
import json
import os

#Check the existence of the pokemon database
def checkPokemonsExists():
    if not os.path.exists("./pokemons.json"):
        with open("./pokemons.json", 'w') as file:
            json.dump({}, file)

#Get a pokemon from the database using its ID
def getPokemonNameById(pokemonId):
    with open("./pokemons.json", 'r') as file:
        pokemons = json.load(file)
    for pokemon in pokemons:
        if pokemon["id"]==pokemonId:
            return pokemon["name"]

#Check if a pokemon is legendary by its ID
def checkLegendary(pokemonId):
    with open("./pokemons.json", 'r') as file:
        pokemons = json.load(file)
    for pokemon in pokemons:
        if pokemon["id"]==pokemonId:
            return pokemon["isLegendary"]

#Get the gender of a pokemon by its ID
def getGender(pokemonId):
    with open("./pokemons.json", 'r') as file:
        pokemons = json.load(file)
    for pokemon in pokemons:
        if pokemon["id"]==pokemonId:
            return random.choice(pokemon["gender"])

#Generate a new random pokemon with its ID, name, shiny status, legendary status, level, and gender
def generatePokemon():
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