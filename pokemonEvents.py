import random
from pymongo import MongoClient
import os
#import config
from logger_config import logger

#MONGO_URI = config.MONGO_URI
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MONGO_URI no está configurada en las variables de entorno.")

#Check the existence of the pokemon database
def checkPokemonsExists():
    try:
        client = MongoClient(MONGO_URI)
        db = client['pokemon_bot']
        collection = db['pokemons']
        # Verificar si la colección de pokemons está vacía
        if collection.count_documents({}) == 0:
            # Si la colección está vacía, insertar un documento de ejemplo
            collection.insert_one({"placeholder": "data"})
        client.close()
    except Exception as e:
        logger.error(f"Error checking the existence of the Pokémon database: {e}")

#Get a pokemon name from the database using its ID
def getPokemonNameById(pokemonId):
    try:
        client = MongoClient(MONGO_URI)
        db = client['pokemon_bot']
        collection = db['pokemons']
        # Buscar el pokemon por ID
        pokemon = collection.find_one({"id": pokemonId})
        client.close()
        return pokemon["name"] if pokemon else None
    except Exception as e:
        logger.error(f"Error getting the Pokémon by ID: {e}")
        return None

#Get a pokemon from the database using its ID
def getPokemonById(pokemonId):
    try:
        client = MongoClient(MONGO_URI)
        db = client['pokemon_bot']
        collection = db['pokemons']
        # Buscar el pokemon por ID
        pokemon = collection.find_one({"id": pokemonId})
        client.close()
        return pokemon
    except Exception as e:
        logger.error(f"Error getting the Pokémon by ID: {e}")
        return None

#Check if a pokemon is legendary by its ID
def checkLegendary(pokemonId):
    try:
        client = MongoClient(MONGO_URI)
        db = client['pokemon_bot']
        collection = db['pokemons']
        # Buscar el pokemon por ID y obtener si es legendario
        pokemon = collection.find_one({"id": pokemonId})
        client.close()
        return pokemon["isLegendary"] if pokemon else False
    except Exception as e:
        logger.error(f"Error checking if the Pokémon is legendary: {e}")
        return False

#Get the gender of a pokemon by its ID
def getGender(pokemonId):
    try:
        client = MongoClient(MONGO_URI)
        db = client['pokemon_bot']
        collection = db['pokemons']
        # Buscar el pokemon por ID
        pokemon = collection.find_one({"id": pokemonId})
        client.close()
        return random.choice(pokemon["gender"]) if pokemon else None
    except Exception as e:
        logger.error(f"Error getting the gender of the Pokémon: {e}")
        return None

#Generate a new random pokemon with its ID, name, shiny status, legendary status, level, and gender
def generatePokemon():
    try:
        pokemon = getPokemonById(random.randint(1, 151))
        if pokemon is None:
            return None  # No existe pokemon con ese ID
        isShiny_check = random.randint(1, 4096) <= 2
        pokemon_image = f"./pokemon_sprites{'_shiny' if isShiny_check==True else ''}/{pokemon['id']}.webp"
        # Generar el pokemon usando los datos de la base de datos
        new_pokemon = {
            "id": pokemon['id'],
            "name": pokemon['name'],
            "isShiny": isShiny_check,
            "isLegendary": pokemon['isLegendary'],
            "level": random.randint(1, 100),
            "gender": random.choice(pokemon['gender']),
            "image": pokemon_image
        }
        return new_pokemon
    except Exception as e:
        logger.error(f"Error generating a new Pokémon: {e}")
        return None
