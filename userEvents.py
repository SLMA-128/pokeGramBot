from pymongo import MongoClient
import random
import os
#import config
from logger_config import logger

#MONGO_URI = config.MONGO_URI
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MONGO_URI no está configurada en las variables de entorno.")

#Register a new user to the users database, checking if the username already exists.
def registerUser(username):
    try:
        client = MongoClient(MONGO_URI)  # Conectar a MongoDB
        db = client['pokemon_bot']  # Nombre de la base de datos
        collection = db['users']  # Colección de usuarios
        # Verificar si el nombre de usuario ya existe
        if collection.find_one({"name": username}):
            return False
        # Obtener el siguiente ID (por ejemplo, el máximo + 1)
        max_id = collection.find_one({}, {"id": 1}, sort=[("id", -1)])
        new_id = max_id["id"] + 1 if max_id else 1
        # Crear nuevo usuario
        new_user = {"id": new_id, "name": username, "total_pokemons": 0, "total_shiny": 0, "pokemonsOwned": []}
        collection.insert_one(new_user)
        client.close()
        return True
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        return False

#Check if the user exists in the database
def checkUserisRegistered(username):
    try:
        client = MongoClient(MONGO_URI)
        db = client['pokemon_bot']
        collection = db['users']
        # Consultar si el usuario existe
        user = collection.find_one({"name": username})
        client.close()
        return user is not None
    except Exception as e:
        logger.error(f"Error checking user: {str(e)}")
        return False

#Get the list of pokemons captured by a user using its username
def getListOfPokemonCapturedByName(username):
    try:
        client = MongoClient(MONGO_URI)
        db = client['pokemon_bot']
        collection = db['users']
        # Buscar el usuario y obtener su lista de pokemons
        user = collection.find_one({"name": username})
        client.close()
        return user["pokemonsOwned"] if user else None
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        return None

#Free all the pokemons captured by a user using their username
def freeAllPokemons(username):
    try:
        client = MongoClient(MONGO_URI)
        db = client['pokemon_bot']
        collection = db['users']
        # Buscar el usuario
        user = collection.find_one({"name": username})
        if user:
            # Actualizar la lista de pokemonsOwned
            collection.update_one({"name": username}, {"$set": {"pokemonsOwned": []}})
            client.close()
            return True
        client.close()
        return False
    except Exception as e:
        logger.error(f"Error freeing pokemons: {str(e)}")
        return False

#Add a new captured pokemon to a user
def addPokemonCaptured(pokemon, username):
    try:
        client = MongoClient(MONGO_URI)
        db = client['pokemon_bot']
        collection = db['users']
        # Buscar el usuario y agregar el pokemon
        result = collection.update_one(
            {"name": username}, 
            {"$push": {"pokemonsOwned": pokemon}}
        )
        client.close()
        return result.modified_count > 0  # True si se realizó una actualización
    except Exception as e:
        logger.error(f"Error adding pokemon: {str(e)}")
        return False
    
def getRandomPokemonCaptured(username):
    try:
        client = MongoClient(MONGO_URI)
        db = client['pokemon_bot']
        collection = db['users']
        # Buscar el usuario y obtener el pokemon
        user = collection.find_one({"name": username})
        if user:
            return random.choice(user["pokemonsOwned"])
        client.close()
        return None
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        return None