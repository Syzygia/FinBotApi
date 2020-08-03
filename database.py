import collections
import json

from pymongo import MongoClient

client = MongoClient(
    "mongodb+srv://AdminFinBot:vmwbMwH7c5nrWZTE@cluster0.pyff5.mongodb.net/finbot_db?retryWrites=true&w=majority")
db = client.finbot_db


def update_dialog(_id, path):
    with open(path, 'r', encoding='utf-8') as json_data:
        json_string = ""
        for i, line in enumerate(json_data):
            json_string += line

    dialog = {'dialog': json_string}
    db.dialogs.replace_one({'_id': _id}, dialog)


def insert_dialog(path):
    json_string = ""
    # use Python's open() function to load a JSON file
    with open(path, 'r', encoding='utf-8') as json_data:
        # iterate over the _io.TextIOWrapper returned by open() using e numerate()
        for i, line in enumerate(json_data):
            # append the parsed IO string to the JSON string
            json_string += line

    dialog = {'dialog': json_string}
    db.dialogs.insert_one(dialog)


def convert_csv_to_json(path):
    json_data = dict()
    json_data['replies'] = list()
    json_data['lines'] = list()

    csv_lines = open(path, 'r', encoding='utf-8').readlines()
    questions = dict()
    answers = collections.OrderedDict()
    # csv_lines[0] = csv_lines[0].encode('utf-8-sig').decode('utf-8-sig')
    # csv_lines = csv_lines[0].split('"')
    for line in csv_lines:
        line = line.split('"')[1].split('~')
        # line 0-id 1-parent id 2-text

        if (not line[1] in questions):
            questions[line[0]] = dict()
            questions[line[0]]['text'] = line[2]
            questions[line[0]]['replies'] = dict()
            if (line[1] in answers):
                questions[answers[line[1]]]['replies'][list(answers.keys()).index(line[1])] = len(questions) - 1

        else:
            answers[str(line[0])] = line[1]
            json_data['replies'].append(line[2])
            questions[line[1]]['replies'][(len(json_data['replies']) - 1)] = 0.1

    for key, val in questions.items():
        json_data['lines'].append(val)

    with open('data.json', 'w+', encoding='utf-8', ) as fp:
        json.dump(json_data, fp, ensure_ascii=False, indent=4)


def insert_user(user_id):
    return db.users.update_one({'user_id': user_id},
                               {'$setOnInsert': {'dialogs': []}},
                               upsert=True
                               )


def embed_user_dialog(user_id, dialog_id):
    return db.users.update_one({'user_id': user_id},
                               {'$addToSet':
                                   {'dialogs':
                                       {
                                           '_id': dialog_id,
                                           'answered': []
                                       }
                                   }
                               })


def update_dialog_status(user_id, dialog_id, answered_index=None):
    return db.users.update_one({'user_id': user_id,
                                'dialogs._id': dialog_id},
                               {'$push':
                                   {
                                       'dialogs.$.answered': answered_index
                                   }
                               })


def get_dialogs():
    return db.dialogs.find({})


def add_custom_choce(dialog_id, user_id, text):
    db.dialogs.update_one({'_id': dialog_id},
                          {'$push':
                               {'custom_choices': {'user_id': user_id,
                                                   'text': text}
                                }
                           })


def reset_user_dialog_status(user_id, dialog_id):
    db.users.update_one({'user_id': user_id},
                        {'$pull':

                             {"dialogs": {'_id': dialog_id}}

                         })

# convert_csv_to_json('Untitled_6.csv')
# insert_dialog('data.json')
