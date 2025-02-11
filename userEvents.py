from pymongo import MongoClient
import random
import os
from logger_config import logger

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MONGO_URI no está configurada en las variables de entorno.")

# List of all the titles and their descriptions
titles = [
    {
        "title": "Entrenador Novato",
        "description": "Has capturado más de 10 Pokémon. ¡Apenas comienzas!",
        "condition": lambda u: u["total_pokemons"] > 10,
        "howto": "Captura 10 Pokémones."
    },
    {
        "title": "Entrenador Experimentado",
        "description": "Has capturado más de 50 Pokémon. ¡Sigue creciendo!",
        "condition": lambda u: u["total_pokemons"] > 50,
        "howto": "Captura 50 Pokémones."
    },
    {
        "title": "Maestro Pokémon",
        "description": "Has capturado más de 100 Pokémon. ¡Tampoco te abuses!",
        "condition": lambda u: u["total_pokemons"] > 100,
        "howto": "Captura 100 Pokémones."
    },
    {
        "title": "Maestro Pokémon Shiny",
        "description": "Has capturado al menos un Pokémon shiny. ¡Su cabeza adornara tu pared!",
        "condition": lambda u: u["total_shiny"] > 0,
        "howto": "Captura Pokémones shiny."
    },
    {
        "title": "Duelista",
        "description": "Has ganado al menos 10 duelos contra otros entrenadores. ¡Como te encanta el bardo!",
        "condition": lambda u: sum(entry["count"] for entry in u.get("victories", [])) > 10,
        "howto": "Gana 10 duelos."
    },
    {
        "titles": "Leyenda de los Combates",
        "description": "Has ganado más de 50 duelos. ¡La violencia es una pregunta y la respuesta es si!",
        "condition": lambda u: sum(entry["count"] for entry in u.get("victories", [])) > 50,
        "howto": "Gana 50 duelos."
    },
    {
        "title": "Coleccionista",
        "description": "Capturaste al menos 50 especies diferentes de Pokémon. ¡Vas bastante bien!",
        "condition": lambda u: len(u["pokemonsOwned"]) > 50,
        "howto": "Ten al menos 50 especies diferentes de Pokémon."
    },
    {
        "title": "Completista",
        "description": "Completaste la Pokedex con los 151 Pokémones. ¡No hay NewGame+!",
        "condition": lambda u: len(u["pokemonsOwned"]) == 151,
        "howto": "Completa la Pokedex con los 151 Pokémones."
    },
    {
        "title": "Domador",
        "description": "Tienes al menos un Pokémon de nivel 100. ¡Demuestra tu poder!",
        "condition": lambda u: len([p for p in u["pokemonsOwned"] if p["level"] == 100]) >= 1,
        "howto": "Tienes al menos un Pokémon de nivel 100."
    },
    {
        "title": "Veterano",
        "description": "Tienes al menos 20 Pokémon en nivel 100. ¡No seas tna tryhard!",
        "condition": lambda u: len([p for p in u["pokemonsOwned"] if p["level"] == 100]) >= 20,
        "howto": "Tienes al menos 20 Pokémon en nivel 100."
    },
    {
        "title": "Cazador de Legendarios",
        "description": "Capturaste al menos un Pokémon legendario. ¡Nadie escapará de tus Pokébolas!",
        "condition": lambda u: sum(1 for p in u["pokemonsOwned"] if p["isLegendary"]) >= 1,
        "howto": "Ten al menos un Pokémon legendario."
    },
    {
        "title": "Scalies",
        "description": "Capturaste al menos 5 Pokémon de tipo Dragón. ¡Se nota que te gustan las escamas!",
        "condition": lambda u: sum(1 for p in u["pokemonsOwned"] if "Dragon" in p["types"]) >= 5,
        "howto": "Ten al menos 5 Pokémon de tipo Dragón."
    },
    {
        "title": "Metalero",
        "description": "Capturaste al menos 5 Pokémon de tipo Acero. ¡Pegale con el fierro!",
        "condition": lambda u: sum(1 for p in u["pokemonsOwned"] if "Steel" in p["types"]) >= 5,
        "howto": "Ten al menos 5 Pokémon de tipo Acero."
    },
    {
        "title": "Piromano",
        "description": "Capturaste al menos 5 Pokémon de tipo Fuego. ¡A cocinar esos Pokémones!",
        "condition": lambda u: sum(1 for p in u["pokemonsOwned"] if "Fire" in p["types"]) >= 5,
        "howto": "Ten al menos 5 Pokémon de tipo Fuego."
    },
    {
        "title": "Hidrofilico",
        "description": "Capturaste al menos 5 Pokémon de tipo Agua. ¡Glu glu glu!",
        "condition": lambda u: sum(1 for p in u["pokemonsOwned"] if "Water" in p["types"]) >= 5,
        "howto": "Ten al menos 5 Pokémon de tipo Agua."
    },
    {
        "title": "Normalucho",
        "description": "Capturaste al menos 5 Pokémon de tipo Normal. ¡No eres nada especial!",
        "condition": lambda u: sum(1 for p in u["pokemonsOwned"] if "Normal" in p["types"]) >= 5,
        "howto": "Ten al menos 5 Pokémon de tipo Normal."
    },
    {
        "title": "Vegano",
        "description": "Capturaste al menos 5 Pokémon de tipo Planta. ¡Metele hasta la raíz!",
        "condition": lambda u: sum(1 for p in u["pokemonsOwned"] if "Grass" in p["types"]) >= 5,
        "howto": "Ten al menos 5 Pokémon de tipo Planta."
    },
    {
        "title": "Edgy",
        "description": "Capturaste al menos 5 Pokémon de tipo Siniestro. ¡Sigue cultivando esa aura!",
        "condition": lambda u: sum(1 for p in u["pokemonsOwned"] if "Dark" in p["types"]) >= 5,
        "howto": "Ten al menos 5 Pokémon de tipo Siniestro."
    },
    {
        "title": "Electricista",
        "description": "Capturaste al menos 5 Pokémon de tipo Eléctrico. ¡Tira esos Pokémones a la bañera!",
        "condition": lambda u: sum(1 for p in u["pokemonsOwned"] if "Electric" in p["types"]) >= 5,
        "howto": "Ten al menos 5 Pokémon de tipo Eléctrico."
    },
    {
        "title": "Kamikaze",
        "description": "Capturaste al menos 5 Pokémon de tipo Volador. ¡Contra las torres!",
        "condition": lambda u: sum(1 for p in u["pokemonsOwned"] if "Flying" in p["types"]) >= 5,
        "howto": "Ten al menos 5 Pokémon de tipo Volador."
    },
    {
        "title": "Hard Rock",
        "description": "Capturaste al menos 5 Pokémon de tipo Roca. ¡Ya te gustaria tenerla así!",
        "condition": lambda u: sum(1 for p in u["pokemonsOwned"] if "Rock" in p["types"]) >= 5,
        "howto": "Ten al menos 5 Pokémon de tipo Roca."
    },
    {
        "title": "Sucio",
        "description": "Capturaste al menos 5 Pokémon de tipo Tierra. ¡Te encanta que te den en el barro!",
        "condition": lambda u: sum(1 for p in u["pokemonsOwned"] if "Ground" in p["types"]) >= 5,
        "howto": "Ten al menos 5 Pokémon de tipo Tierra."
    },
    {
        "title": "Hechicero",
        "description": "Capturaste al menos 5 Pokémon de tipo Psíquico. ¡No te inmutas!",
        "condition": lambda u: sum(1 for p in u["pokemonsOwned"] if "Psychic" in p["types"]) >= 5,
        "howto": "Ten al menos 5 Pokémon de tipo Psíquico."
    },
    {
        "title": "Cazador de Hadas",
        "description": "Capturaste al menos 5 Pokémon de tipo Hada. ¡No cuentan como padrinos-magicos!",
        "condition": lambda u: sum(1 for p in u["pokemonsOwned"] if "Fairy" in p["types"]) >= 5,
        "howto": "Ten al menos 5 Pokémon de tipo Hada."
    },
    {
        "title": "Ghostbuster",
        "description": "Capturaste al menos 5 Pokémon de tipo Fantasma. ¡Haz plata con esos fantasmas!",
        "condition": lambda u: sum(1 for p in u["pokemonsOwned"] if "Ghost" in p["types"]) >= 5,
        "howto": "Ten al menos 5 Pokémon de tipo Fantasma."
    },
    {
        "title": "Maltratador",
        "description": "Capturaste al menos 5 Pokémon de tipo Lucha. ¡Hazlos luchar por las buenas o por las malas!",
        "condition": lambda u: sum(1 for p in u["pokemonsOwned"] if "Fighting" in p["types"]) >= 5,
        "howto": "Ten al menos 5 Pokémon de tipo Lucha."
    },
    {
        "title": "Toxico",
        "description": "Capturaste al menos 5 Pokémon de tipo Veneno. ¡Esto dice mucho de ti!",
        "condition": lambda u: sum(1 for p in u["pokemonsOwned"] if "Poison" in p["types"]) >= 5,
        "howto": "Ten al menos 5 Pokémon de tipo Veneno."
    },
    {
        "title": "Blue Balls",
        "description": "Capturaste al menos 5 Pokémon de tipo Hielo. ¡Siempre los dejas frios!",
        "condition": lambda u: sum(1 for p in u["pokemonsOwned"] if "Ice" in p["types"]) >= 5,
        "howto": "Ten al menos 5 Pokémon de tipo Hielo."
    },
    {
        "title": "Bichero",
        "description": "Capturaste al menos 5 Pokémon de tipo Bicho. ¡Cada quien tiene sus gustos!",
        "condition": lambda u: sum(1 for p in u["pokemonsOwned"] if "Bug" in p["types"]) >= 5,
        "howto": "Ten al menos 5 Pokémon de tipo Bicho."
    },
    {
        "title": "Vivido",
        "description": "Capturaste al menos un Pokémon de cada tipo en tu colección. ¡Uno de cada sabor!",
        "condition": lambda u: len(set([p["types"] for p in u["pokemonsOwned"]])) == 18,
        "howto": "Tienes al menos un Pokémon de cada tipo en tu colección."
    }
]

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
def updateCombatResults(winner, loser, winner_pokemon, new_level):
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
        if winner_pokemon:
            collection.update_one(
                {"name": winner, "pokemonsOwned.id": winner_pokemon['id']},
                {"$set": {"pokemonsOwned.$.level": new_level}}
            )
        client.close()
        return True
    except Exception as e:
        logger.error(f"Error updating combat results: {str(e)}")
        return False

# Add titles to the user
def add_titles_to_user(username):
    try:
        print("intentando agregar titulos")
        client = MongoClient(MONGO_URI)
        db = client['pokemon_bot']
        collection = db['users']
        user = collection.find_one({"name": username})
        if not user:
            return False
        current_titles = set(user.get("titles", []))
        new_titles = []
        for titulo in titles:
            # Imprimir el resultado de la condición para verificar su ejecución
            condition_result = titulo["condition"](user)
            print(f"Condición para el título '{titulo['title']}': {condition_result}")
            if condition_result and titulo["title"] not in current_titles:
                new_titles.append(titulo["title"])
        print("Nuevos títulos a agregar:", new_titles)
        if new_titles:
            updated_titles = current_titles | set(new_titles)
            print(f"Actualizando títulos para {username}: {updated_titles}")
            collection.update_one({"name": username}, {"$set": {"titles": list(updated_titles)}})
        client.close()
        return True
    except Exception as e:
        logger.error(f"Error otorgando títulos: {str(e)}")
        return False
