import random
import json
import os

def checkPokemonsExists():
    if not os.path.exists("./pokemons.json"):
        with open("./pokemons.json", 'w') as file:
            json.dump({}, file)

def getPokemonNameById(pokemonId):
    with open("./pokemons.json", 'r') as file:
        pokemons = json.load(file)
    for pokemon in pokemons:
        if pokemon["id"]==pokemonId:
            return pokemon["name"]

def checkLegendary(pokemonId):
    with open("./pokemons.json", 'r') as file:
        pokemons = json.load(file)
    for pokemon in pokemons:
        if pokemon["id"]==pokemonId:
            return pokemon["isLegendary"]

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
        "gender": random.choice(["male", "female"])
    }
    return pokemon