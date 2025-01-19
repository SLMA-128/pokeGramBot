import random
import json
import os

def checkPokemonsExists():
    if not os.path.exists("./pokemons.json"):
        with open("./pokemons.json", 'w') as file:
            json.dump({}, file)

def spawnPokemon():
    return random.randint(1, 151)

def getPokemonNameById(pokemonId):
    with open("./pokemons.json", 'r') as file:
        pokemons = json.load(file)
    for pokemon in pokemons:
        if pokemon["id"]==pokemonId:
            return pokemon["name"]

def generatePokemon(pokemonId):
    isShiny_check = random.randint(1,100)
    pokemon = {
        "id": pokemonId,
        "name": getPokemonNameById(pokemonId),
        "isShiny": isShiny_check <= 5,
        "level": random.randint(1, 100),
        "gender": random.choice(["male", "female"])
    }
    return pokemon