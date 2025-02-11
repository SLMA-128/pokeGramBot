import random
from pymongo import MongoClient
import os
from logger_config import logger

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MONGO_URI no está configurada en las variables de entorno.")

# Define the type effectiveness dictionary.
type_effectiveness = {
    "Normal":   {"strong_against": [], "weak_against": ["Rock", "Steel"], "immune_against": ["Ghost"]},
    "Fire":     {"strong_against": ["Grass", "Bug", "Ice", "Steel"], "weak_against": ["Water", "Rock", "Fire"], "immune_against": []},
    "Water":    {"strong_against": ["Fire", "Ground", "Rock"], "weak_against": ["Electric", "Grass", "Water"], "immune_against": []},
    "Electric": {"strong_against": ["Water", "Flying"], "weak_against": ["Electric", "Grass", "Dragon"], "immune_against": ["Ground"]},
    "Grass":    {"strong_against": ["Water", "Ground", "Rock"], "weak_against": ["Fire", "Flying", "Bug", "Poison", "Grass", "Dragon", "Steel"], "immune_against": []},
    "Ice":      {"strong_against": ["Grass", "Ground", "Flying", "Dragon"], "weak_against": ["Fire", "Water", "Ice", "Steel"], "immune_against": []},
    "Fighting": {"strong_against": ["Normal", "Ice", "Rock", "Dark", "Steel"], "weak_against": ["Flying", "Poison", "Bug", "Psychic", "Fairy"], "immune_against": ["Ghost"]},
    "Poison":   {"strong_against": ["Grass", "Fairy"], "weak_against": ["Poison", "Ground", "Rock", "Ghost"], "immune_against": ["Steel"]},
    "Ground":   {"strong_against": ["Fire", "Electric", "Poison", "Rock", "Steel"], "weak_against": ["Grass", "Bug"], "immune_against": ["Electric"]},
    "Flying":   {"strong_against": ["Grass", "Fighting", "Bug"], "weak_against": ["Electric", "Rock", "Steel"], "immune_against": ["Ground"]},
    "Psychic":  {"strong_against": ["Fighting", "Poison"], "weak_against": ["Psychic", "Steel"], "immune_against": ["Dark"]},
    "Bug":      {"strong_against": ["Grass", "Psychic", "Dark"], "weak_against": ["Fire", "Fighting", "Poison", "Flying", "Ghost", "Steel", "Fairy"], "immune_against": []},
    "Rock":     {"strong_against": ["Fire", "Ice", "Flying", "Bug"], "weak_against": ["Fighting", "Ground", "Steel"], "immune_against": []},
    "Ghost":    {"strong_against": ["Psychic", "Ghost"], "weak_against": ["Dark"], "immune_against": ["Normal", "Fighting"]},
    "Dragon":   {"strong_against": ["Dragon"], "weak_against": ["Steel"], "immune_against": ["Fairy"]},
    "Dark":     {"strong_against": ["Psychic", "Ghost"], "weak_against": ["Fighting", "Dark", "Fairy"], "immune_against": []},
    "Steel":    {"strong_against": ["Ice", "Rock", "Fairy"], "weak_against": ["Fire", "Water", "Electric", "Steel"], "immune_against": ["Poison"]},
    "Fairy":    {"strong_against": ["Fighting", "Dragon", "Dark"], "weak_against": ["Fire", "Poison", "Steel"], "immune_against": ["Dragon"]}
}


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

#Get a pokemon from the database using its name
def getPokemonByName(pokemonName):
    try:
        client = MongoClient(MONGO_URI)
        db = client['pokemon_bot']
        collection = db['pokemons']
        # Buscar el pokemon por nombre
        pokemon = collection.find_one({"name": {"$regex": f"^{pokemonName}$", "$options": "i"}})
        client.close()
        return pokemon
    except Exception as e:
        logger.error(f"Error getting the Pokémon by name: {e}")
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
        pokemon_image = f"./pokemon_sprites{'_shiny' if isShiny_check==True else ''}/{random.choice(pokemon['image'])}.webp"
        pkm_gender = "Female" if pokemon_image.endswith("f") else "Male" if pokemon_image.endswith("m") else random.choice(pokemon['gender'])
        # Generar el pokemon usando los datos de la base de datos
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
        logger.error(f"Error generating a new Pokémon: {e}")
        return None

# bonus por ventaja de tipos
def get_type_advantage(attacker_types, defender_types):
    bonus = 0
    for atk_type in attacker_types:
        if atk_type in type_effectiveness:
            for def_type in defender_types:
                if def_type in type_effectiveness[atk_type]["strong_against"]:
                    bonus += 15  # Bonificación si el atacante tiene ventaja
                elif def_type in type_effectiveness[atk_type]["weak_against"]:
                    bonus -= 15  # Penalización si el atacante tiene desventaja
                elif def_type in type_effectiveness[atk_type]["immune_against"]:
                    bonus -= 25  # Desventaja total si el ataque no afecta
    return bonus
