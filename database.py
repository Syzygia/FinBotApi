import pymongo
from pymongo import MongoClient
import json

client = MongoClient("mongodb+srv://AdminFinBot:vmwbMwH7c5nrWZTE@cluster0.pyff5.mongodb.net/finbot_db?retryWrites=true&w=majority")
db = client.finbot_db

def insert_dialog (path):
    json_string = ""
    # use Python's open() function to load a JSON file
    with open(path, 'r', encoding='utf-8') as json_data:
        # iterate over the _io.TextIOWrapper returned by open() using e numerate()
        for i, line in enumerate(json_data):
            # append the parsed IO string to the JSON string
            json_string += line

    dialog = {'dialog': json_string}
    db.dialogs.insert_one(dialog)

def insert_user (user_id):
    return db.users.insert_one({'user_id' : user_id,
                                'dialogs' : []}).inserted_id

def embed_user_dialog(user_id, dialog_id):
    return db.users.update_one({'user_id' : user_id},
                               {'$push' :
                                    {'dialogs' :
                                         {
                                             '_id' : dialog_id,
                                             'answered' : []
                                         }
                                    }
                               })

def update_dialog_status(user_id, dialog_id, answered_index):
    return db.users.update_one({'user_id' : user_id,
                                'dialogs._id' : dialog_id},
                               {'$push':
                                    {
                                        'dialogs.$.answered' : answered_index
                                    }
                               })
