import os
import json

def checkUsersExists():
    if not os.path.exists("./users.json"):
        with open("./users.json", 'w') as file:
            json.dump({}, file)

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

def getUserByName(username):
    checkUsersExists()
    #user: id, name, listOfNumbers
    with open("./users.json", 'r') as file:
        users = json.load(file)
    for user in users:
        if user["name"] == username:
            return user["name"]
    return None

def getListOfPokemonCapturedByName(username):
    checkUsersExists()
    #user: id, name, listOfNumbers [1,2,3]
    with open("./users.json", 'r') as file:
        users = json.load(file)
    for user in users:
        if user["name"] == username:
            return user["pokemonsOwned"]
    return None

def addPokemonCaptured(pokemonId,username):
    checkUsersExists()
    #user: id, name, listOfNumbers [1,2,3]
    with open("./users.json", 'r') as file:
        users = json.load(file)
    for user in users:
        if user["name"] == username:
            if pokemonId not in user["pokemonsOwned"]:
                user["pokemonsOwned"].append(pokemonId)
                with open("./users.json", 'w') as file:
                    json.dump(users, file, indent=4)
                return True
    return False