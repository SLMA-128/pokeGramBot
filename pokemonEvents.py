import random
from pymongo import MongoClient
import os
from logger_config import logger

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MONGO_URI no está configurada en las variables de entorno.")

# Define the type effectiveness dictionary.
type_effectiveness = {
    "Normal":   {"strong_against": [], "resistant_against": [], "weak_against": ["Lucha"], "immune_against": ["Fantasma"]},
    "Fuego":     {"strong_against": ["Planta", "Bicho", "Hielo", "Acero"], "resistant_against": ["Fuego", "Hada"], "weak_against": ["Agua", "Roca", "Tierra"], "immune_against": []},
    "Agua":    {"strong_against": ["Fuego", "Tierra", "Roca"], "resistant_against": ["Agua", "Hielo", "Acero"], "weak_against": ["Electrico", "Planta"], "immune_against": []},
    "Electrico": {"strong_against": ["Agua", "Volador"], "resistant_against": ["Electrico", "Acero",  "Volador"], "weak_against": ["Tierra"], "immune_against": []},
    "Planta":    {"strong_against": ["Agua", "Tierra", "Roca"], "resistant_against": ["Electrico", "Planta"], "weak_against": ["Fuego", "Volador", "Bicho", "Veneno", "Hielo"], "immune_against": []},
    "Hielo":      {"strong_against": ["Planta", "Tierra", "Volador", "Dragon"], "resistant_against": ["Hielo"], "weak_against": ["Fuego", "Acero", "Roca", "Lucha"], "immune_against": []},
    "Lucha": {"strong_against": ["Normal", "Hielo", "Roca", "Siniestro", "Acero"], "resistant_against": ["Siniestro", "Bicho", "Roca"], "weak_against": ["Volador", "Psiquico", "Hada"], "immune_against": []},
    "Veneno":   {"strong_against": ["Planta", "Hada"], "resistant_against": ["Bicho", "Veneno", "Lucha"],  "weak_against": ["Tierra", "Psiquico"], "immune_against": []},
    "Tierra":   {"strong_against": ["Fuego", "Electrico", "Veneno", "Roca", "Acero"], "resistant_against": ["Veneno", "Roca"], "weak_against": ["Planta", "Hielo", "Agua"], "immune_against": ["Electrico"]},
    "Volador":   {"strong_against": ["Planta", "Lucha", "Bicho"], "resistant_against": [], "weak_against": ["Electrico", "Roca", "Hielo"], "immune_against": ["Tierra"]},
    "Psiquico":  {"strong_against": ["Lucha", "Veneno"], "resistant_against": ["Psiquico"], "weak_against": ["Siniestro", "Fantasma", "Bicho"], "immune_against": []},
    "Bicho":      {"strong_against": ["Planta", "Psiquico", "Siniestro"], "resistant_against": ["Tierra", "Lucha"], "weak_against": ["Fuego", "Volador", "Roca"], "immune_against": []},
    "Roca":     {"strong_against": ["Fuego", "Hielo", "Volador", "Bicho"], "resistant_against": ["Normal", "Volador", "Veneno", "Fuego"], "weak_against": ["Lucha", "Tierra", "Acero","Planta", "Agua"], "immune_against": []},
    "Fantasma":    {"strong_against": ["Psiquico", "Fantasma"], "resistant_against": ["Bicho", "Veneno"], "weak_against": ["Siniestro", "Fantasma"], "immune_against": ["Normal", "Lucha"]},
    "Dragon":   {"strong_against": ["Dragon"], "resistant_against": ["Electrico", "Agua", "Planta", "Fuego"], "weak_against": ["Hada", "Hielo", "Dragon"], "immune_against": []},
    "Siniestro":     {"strong_against": ["Psiquico", "Fantasma"], "resistant_against": ["Fantasma", "Siniestro"], "weak_against": ["Lucha", "Hada", "Bicho"], "immune_against": ["Psiquico"]},
    "Acero":    {"strong_against": ["Hielo", "Roca", "Hada"], "resistant_against": ["Dragon", "Acero", "Bicho", "Psiquico", "Normal", "Volador", "Planta"], "weak_against": ["Fuego", "Tierra", "Lucha"], "immune_against": ["Veneno"]},
    "Hada":    {"strong_against": ["Lucha", "Dragon", "Siniestro"], "resistant_against": ["Bicho"], "weak_against": ["Veneno", "Acero"], "immune_against": ["Dragon"]}
}

#Check the existence of the pokemon database
def checkPokemonsExists():
    try:
        client = MongoClient(MONGO_URI)
        db = client['pokemon_bot']
        collection = db['pokemons']
        if collection.count_documents({}) == 0:
            collection.insert_one({"placeholder": "data"})
        client.close()
    except Exception as e:
        logger.error(f"Error al comprobar la existencia del Pokémon en la base de datos: {e}")

#Get a pokemon name from the database using its ID
def getPokemonNameById(pokemonId):
    try:
        client = MongoClient(MONGO_URI)
        db = client['pokemon_bot']
        collection = db['pokemons']
        pokemon = collection.find_one({"id": pokemonId})
        client.close()
        return pokemon["name"] if pokemon else None
    except Exception as e:
        logger.error(f"Error obteniendo el nombre del Pokémon por su ID: {e}")
        return None

#Get a pokemon from the database using its ID
def getPokemonById(pokemonId):
    try:
        client = MongoClient(MONGO_URI)
        db = client['pokemon_bot']
        collection = db['pokemons']
        pokemon = collection.find_one({"id": pokemonId})
        client.close()
        return pokemon
    except Exception as e:
        logger.error(f"Error obteniendo el Pokémon por su ID: {e}")
        return None

#Get a pokemon from the database using its name
def getPokemonByName(pokemonName):
    try:
        client = MongoClient(MONGO_URI)
        db = client['pokemon_bot']
        collection = db['pokemons']
        pokemon = collection.find_one({"name": {"$regex": f"^{pokemonName}$", "$options": "i"}})
        client.close()
        return pokemon
    except Exception as e:
        logger.error(f"Error obteniendo el Pokémon por su nombre: {e}")
        return None

#Check if a pokemon is legendary by its ID
def checkLegendary(pokemonId):
    try:
        client = MongoClient(MONGO_URI)
        db = client['pokemon_bot']
        collection = db['pokemons']
        pokemon = collection.find_one({"id": pokemonId})
        client.close()
        return pokemon["isLegendary"] if pokemon else False
    except Exception as e:
        logger.error(f"Error al comprobar si el Pokémon es legendario: {e}")
        return False

#Get the gender of a pokemon by its ID
def getGender(pokemonId):
    try:
        client = MongoClient(MONGO_URI)
        db = client['pokemon_bot']
        collection = db['pokemons']
        pokemon = collection.find_one({"id": pokemonId})
        client.close()
        return random.choice(pokemon["gender"]) if pokemon else None
    except Exception as e:
        logger.error(f"Error obteniendo el genero del Pokémon: {e}")
        return None

#Generate a new random pokemon with its ID, name, shiny status, legendary status, level, and gender
def generatePokemon():
    try:
        pokemon = getPokemonById(random.randint(1, 151))
        if pokemon is None:
            return None  # No existe pokemon con ese ID
        isShiny_check = random.randint(1, 1000) <= 5
        pokemon_image = f"./pokemon_sprites{'_shiny' if isShiny_check==True else ''}/{random.choice(pokemon['image'])}"
        pkm_gender = "Female" if pokemon_image.endswith("f") else "Male" if pokemon_image.endswith("m") else random.choice(pokemon['gender'])
        new_pokemon = {
            "id": pokemon['id'],
            "name": pokemon['name'],
            "isShiny": isShiny_check,
            "isLegendary": pokemon['isLegendary'],
            "level": random.randint(1, 100),
            "gender": pkm_gender,
            "types": pokemon['types'],
            "image": pokemon_image,
            "captured": 1
        }
        return new_pokemon
    except Exception as e:
        logger.error(f"Error generando un nuevo Pokémon: {e}")
        return None

# bonus por ventaja de tipos
def get_type_advantage(attacker_types, defender_types):
    bonus = 0
    for atk_type in attacker_types:
        if atk_type in type_effectiveness:
            for def_type in defender_types:
                if def_type in type_effectiveness[atk_type]["strong_against"]:
                    bonus += 15  # Bonificación si el atacante tiene ventaja
                elif def_type in type_effectiveness[atk_type]["resistant_against"]:
                    bonus += 7  # Bonificación si el atacante tiene ventaja pero el atacado tiene resistencia
                elif def_type in type_effectiveness[atk_type]["weak_against"]:
                    bonus -= 15  # Penalización si el atacante tiene desventaja
                elif def_type in type_effectiveness[atk_type]["immune_against"]:
                    bonus -= 25  # Desventaja total si el ataque no afecta
    return bonus
