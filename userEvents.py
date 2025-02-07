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
        new_user = {
            "id": new_id,
            "name": username,
            "total_pokemons": 0,
            "total_shiny": 0,
            "pokemonsOwned": [],
            "victories":[],
            "defeats": []
            }
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

#Get user from database by username

def getUserByName(username):
    try:
        client = MongoClient(MONGO_URI)
        db = client['pokemon_bot']
        collection = db['users']
        # Buscar el usuario por nombre
        user = collection.find_one({"name": username})
        client.close()
        return user
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        return None

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
        # Incrementar el contador total de Pokémon atrapados
        update_user_stats = {
            "$inc": {"total_pokemons": 1}  # Se incrementa con cada captura
        }
        # Si el Pokémon capturado es shiny, también incrementamos total_shiny
        if pokemon["isShiny"]:
            update_user_stats["$inc"]["total_shiny"] = 1
        # Aplicar incremento en la base de datos
        collection.update_one({"name": username}, update_user_stats)
        query = {
            "name": username,
            "pokemonsOwned": {
                "$elemMatch": {
                    "id": pokemon["id"],
                    "isShiny": pokemon["isShiny"]  # Diferenciar shiny de no shiny
                }
            }
        }
        existing_pokemon = collection.find_one(query)
        if existing_pokemon:
            # Si el Pokémon ya existe, actualizar sus datos
            update_fields = {
                "$inc": {"pokemonsOwned.$.captured": 1}  # Incrementar cantidad capturada
            }
            # Si el nuevo Pokémon tiene mayor nivel, actualizar nivel e imagen
            if existing_pokemon["pokemonsOwned"][0]["level"] < pokemon["level"]:
                update_fields["$set"] = {
                    "pokemonsOwned.$.level": pokemon["level"],
                    "pokemonsOwned.$.image": pokemon["image"]
                }
            collection.update_one(query, update_fields)
        else:
            # Si el Pokémon no existe, agregarlo normalmente
            collection.update_one(
                {"name": username},
                {"$push": {"pokemonsOwned": pokemon}}
            )
        client.close()
        return True
    except Exception as e:
        logger.error(f"Error adding pokemon: {str(e)}")
        return False

#Get a random pokemon captured by a user using their username
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

# Reduce the capture counter of a Pokémon by the loser, considering if it was shiny or not.
def reducePokemonCaptured(loser, loser_pokemon):
    try:
        client = MongoClient(MONGO_URI)
        db = client['pokemon_bot']
        collection = db['users']
        user = collection.find_one({"name": loser})
        if not user or not user["pokemonsOwned"]:
            client.close()
            return False
        for pkm in user["pokemonsOwned"]:
            if pkm["id"] == loser_pokemon["id"] and pkm["isShiny"] == loser_pokemon["isShiny"]:
                if pkm["captured"] > 1:
                    collection.update_one(
                        {"name": loser, "pokemonsOwned.id": loser_pokemon["id"], "pokemonsOwned.isShiny": loser_pokemon["isShiny"]},
                        {"$inc": {"pokemonsOwned.$.captured": -1, "total_pokemons": -1}}
                    )
                    if loser_pokemon["isShiny"]:
                        collection.update_one({"name": loser}, {"$inc": {"total_shiny": -1}})
                else:
                    collection.update_one(
                        {"name": loser},
                        {
                            "$pull": {"pokemonsOwned": {"id": loser_pokemon["id"], "isShiny": loser_pokemon["isShiny"]}},
                            "$inc": {"total_pokemons": -1}
                        }
                    )
                    if loser_pokemon["isShiny"]:
                        collection.update_one({"name": loser}, {"$inc": {"total_shiny": -1}})
                break  # Salimos del bucle una vez encontrado y actualizado
        client.close()
        return True
    except Exception as e:
        logger.error(f"Error reducing Pokémon count: {str(e)}")
        return False

#Reduce the capture counter of a pokemon by the loser, considering if it was shiny or not. 
def deleteRandomPokemon(username):
    try:
        client = MongoClient(MONGO_URI)
        db = client['pokemon_bot']
        collection = db['users']
        user = collection.find_one({"name": username})
        if not user or not user["pokemonsOwned"]:
            client.close()
            return False
        selected_pokemon = random.choice(user["pokemonsOwned"])
        if selected_pokemon is None:
            return False
        query = {
            "name": username,
            "pokemonsOwned.id": selected_pokemon["id"],
            "pokemonsOwned.isShiny": selected_pokemon["isShiny"]
        }
        update = {
            "$inc": {"pokemonsOwned.$.captured": -1, "total_pokemons": -1}
        }
        if selected_pokemon["isShiny"]:
            update["$inc"]["total_shiny"] = -1
        collection.update_one(query, update)
        updated_user = collection.find_one({"name": username})
        updated_pokemons = [pkm for pkm in updated_user["pokemonsOwned"] if pkm["captured"] > 0]
        if len(updated_user["pokemonsOwned"]) != len(updated_pokemons):
            collection.update_one({"name": username}, {"$set": {"pokemonsOwned": updated_pokemons}})
        client.close()
        return True
    except Exception as e:
        logger.error(f"Error reducing pokemon count: {str(e)}")
        return False

# combat results incresing victories for the winner and defeats for the loser
def updateCombatResults(winner, loser):
    try:
        client = MongoClient(MONGO_URI)
        db = client['pokemon_bot']
        collection = db['users']
        def update_record(username, field, opponent):
            query = {"name": username, f"{field}.opponent": opponent}
            existing_record = collection.find_one(query)
            if existing_record:
                collection.update_one(
                    {"name": username, f"{field}.opponent": opponent},
                    {"$inc": {f"{field}.$.count": 1}}
                )
            else:
                collection.update_one(
                    {"name": username},
                    {"$push": {field: {"opponent": opponent, "count": 1}}}
                )
        update_record(winner, "victories", loser)
        update_record(loser, "defeats", winner)
        client.close()
        return True
    except Exception as e:
        logger.error(f"Error updating combat results: {str(e)}")
        return False
