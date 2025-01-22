import os
import json

#Check if the users database exists
def checkUsersExists():
    if not os.path.exists("./users.json"):
        with open("./users.json", 'w') as file:
            json.dump({}, file)

#Register a new user to the users database, checking if the username already exists.
def registerUser(username):
    checkUsersExists()
    with open("./users.json", 'r') as file:
        users = json.load(file)
    if any(user["name"] == username for user in users):
        return False
    listIDs = [int(user["id"]) for user in users]
    newID = 1
    while newID in listIDs:
        newID += 1
    new_user = {"id": newID,
                "name": username,
                "pokemonsOwned": []}
    users.append(new_user)
    with open("./users.json", 'w') as file:
        json.dump(users, file, indent=4)
        return True

#Check if the user exists in the database
def checkUserisRegistered(username):
    checkUsersExists()
    with open("./users.json", 'r') as file:
        users = json.load(file)
    for user in users:
        if user["name"] == username:
            return True
    return False

#Get the user name by their username from the database
def getUserByName(username):
    checkUsersExists()
    #user: id, name, listOfNumbers
    with open("./users.json", 'r') as file:
        users = json.load(file)
    for user in users:
        if user["name"] == username:
            return user["name"]
    return None

#Get the list of pokemons captured by a user using its username
def getListOfPokemonCapturedByName(username):
    checkUsersExists()
    #user: id, name, listOfNumbers [1,2,3]
    with open("./users.json", 'r') as file:
        users = json.load(file)
    for user in users:
        if user["name"] == username:
            return user["pokemonsOwned"]
    return None

#Free all the pokemons captured by a user using their username
def freeAllPokemons(username):
    checkUsersExists()
    #user: id, name, listOfNumbers [1,2,3]
    with open("./users.json", 'r') as file:
        users = json.load(file)
    for user in users:
        if user["name"] == username:
            user["pokemonsOwned"] = []
            with open("./users.json", 'w') as file:
                json.dump(users, file, indent=4)
            return True
    return False

#Add a new captured pokemon to a user
def addPokemonCaptured(pokemon,username):
    checkUsersExists()
    #user: id, name, listOfNumbers [1,2,3]
    with open("./users.json", 'r') as file:
        users = json.load(file)
    for user in users:
        if user["name"] == username:
            user["pokemonsOwned"].append(pokemon)
            with open("./users.json", 'w') as file:
                json.dump(users, file, indent=4)