import collections
import json

from bson import ObjectId
from pymongo import MongoClient

client = MongoClient(
    "mongodb+srv://AdminFinBot:vmwbMwH7c5nrWZTE@cluster0.pyff5.mongodb.net/finbot_db?retryWrites=true&w=majority")
db = client.finbot_db

ID, PARENT_ID, TEXT, TYPE, VALUE = range(5)
CONVERSATION_END = -1


def update_dialog(_id, path):
    with open(path, 'r', encoding='utf-8') as json_data:
        json_string = ""
        for i, line in enumerate(json_data):
            json_string += line

    dialog = {'dialog': json_string}
    db.dialogs.update_one({'_id': ObjectId(_id)},{'$set': {'dialog': json_string}})


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
    json_data['custom_choices'] = list()

    csv_lines = open(path, 'r', encoding='utf-8').readlines()
    questions = dict()
    answers = collections.OrderedDict()
    csv_lines[0] = csv_lines[0].encode('utf-8-sig').decode('utf-8-sig')
    for line in csv_lines:
        line = line.rstrip()
        line = line.replace('"', '')
        line = line.split('~')
        del (line[0])
        if len(line) < 3:
            continue

        if not line[PARENT_ID] in questions:
            init_question(questions, line)
            if len(line) >= 4 and line[TYPE] == 'test_question':
                questions[line[ID]]['type'] = 'test_question'
            if line[PARENT_ID] in answers:
                questions[answers[line[PARENT_ID]]]['replies'][list(answers.keys()).index(line[PARENT_ID])] = \
                    len(questions) - 1

        else:
            if len(line) >= 4 and 'test_final_answer' == line[TYPE]:
                init_question(questions, line)
                questions[line[ID]]['type'] = 'test_final_answer'
                questions[line[ID]]['value'] = line[VALUE]
                # for k, v in questions[line[PARENT_ID]]['replies'].items():
                #     v['leads'] = len(questions) - 1
                continue

            if len(line) >= 4 and 'test_final' == line[TYPE]:
                init_question(questions, line)
                questions[line[ID]]['type'] = 'test_final'
                for k, v in questions[line[PARENT_ID]]['replies'].items():
                    v['leads'] = len(questions) - 1
                continue

            if len(line) >= 4 and 'regular_question' in line[TYPE]:
                init_question(questions, line)
                # for k, v in questions[line[PARENT_ID]]['replies'].items():
                #     v['leads'] = len(questions) - 1
                continue

            if len(line) >= 4 and 'test_question' in line[TYPE]:
                init_question(questions, line)
                questions[line[ID]]['type'] = 'test_question'
                for k, v in questions[line[PARENT_ID]]['replies'].items():
                    v['leads'] = len(questions) - 1

            else:
                answers[str(line[ID])] = line[PARENT_ID]
                json_data['replies'].append(line[TEXT])
                if len(line) >= 4 and line[TYPE] == 'test_answer':
                    questions[line[PARENT_ID]]['replies'][(len(json_data['replies']) - 1)] = \
                        {'value': int(line[VALUE].strip().replace('\"', '')),
                         'leads': CONVERSATION_END}
                else:
                    questions[line[PARENT_ID]]['replies'][(len(json_data['replies']) - 1)] = CONVERSATION_END

                if len(line) >= 4 and 'custom_choice' in line[TYPE]:
                    json_data['custom_choices'].append(len(json_data['replies']) - 1)

    for key, val in questions.items():
        json_data['lines'].append(val)

    with open('data.json', 'w+', encoding='utf-8', ) as fp:
        json.dump(json_data, fp, ensure_ascii=False, indent=4)


def init_question(questions, line):
    questions[line[ID]] = dict()
    questions[line[ID]]['text'] = line[TEXT]
    questions[line[ID]]['replies'] = dict()
    questions[line[ID]]['type'] = 'regular_question'


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


def add_custom_choice(dialog_id, user_id, text):
    db.dialogs.update_one({'_id': dialog_id},
                          {'$push':
                               {'custom_choices': {'user_id': user_id,
                                                   'text': text}
                                }
                           })


def add_suggestion(user_id, text):
    db.users.update_one({'_id': user_id},
                          {'$push':
                               {'suggestions': {'text': text}
                                }
                           })


def reset_user_dialog_status(user_id, dialog_id):
    db.users.update_one({'user_id': user_id},
                        {'$pull':

                             {"dialogs": {'_id': dialog_id}}

                         })

#db.dialogs.update_one({'_id': ObjectId('5f3a51eba7075eaa987219cd')},{'$set': {'name': 'Вложить или накопить деньги'}})
#convert_csv_to_json('latest.csv')
#update_dialog('5f3a5294f67905f0f10ca3e1', 'data.json')
#insert_dialog('data.json')
