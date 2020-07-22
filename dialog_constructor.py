import json

from telegram import ReplyKeyboardMarkup
from telegram.ext import (CommandHandler, MessageHandler, Filters,
                          ConversationHandler)

import database

REGULAR_CHOICE, CUSTOM_CHOICE, RETRY = range(3)


class Line:
    def __init__(self, data, replies):
        self.keyboard = []
        self.leads = []
        self.text = data['text']
        for reply in data['replies']:
            self.keyboard.append([replies[int(reply)]])
        for ref in data['leads']:
            self.leads.append(ref)
        self.is_custom = False

    def get_next(self, update, context=None):
        return self.leads[self.get_answer_num(update, context)]

    def get_answer_num(self, update, context=None):
        self.is_custom = False
        if (update.message.text == "smth_else"):
            self.is_custom = True
        return self.keyboard.index([update.message.text])

    def send_line(self, update, context=None):
        update.message.reply_text(self.text, reply_markup=ReplyKeyboardMarkup(self.keyboard, one_time_keyboard=True))


class Dialog:
    def __init__(self, _id, dialog_data, pp):
        self._id = _id
        self.replies = dialog_data['replies']
        self.lines = []
        self.pp = pp
        # self.last_added_state = None
        for line in dialog_data['lines']:
            self.lines.append(Line(line, dialog_data['replies']))

    def dialog_callback(self, update, context):
        #        self.pp.flush()
        if context.user_data and context.user_data[self._id]['state'] != []:
            if context.user_data[self._id]['state'][-1] == 0.1:
                # Message if want to complete questions once again
                update.message.reply_text('Wonna try it once again?',
                                          reply_markup=ReplyKeyboardMarkup([['Yes'], ['No']], one_time_keyboard=True))
                return 2
            else:
                last_answered_line = self.lines[context.user_data[self._id]['state'][-1]]
                next_state = last_answered_line.get_next(update)
                context.user_data[self._id]['state'].append(next_state)
                database.update_dialog_status(update.effective_user.id,
                                              self._id, last_answered_line.get_answer_num(update))
                if (last_answered_line.is_custom == True):
                    update.message.reply_text('pls tell us what u want here')
                    return 1
                if next_state * 10 != 1:
                    self.lines[next_state].send_line(update, context)
                else:
                    # write last message here
                    update.message.reply_text('thanks for ur info')
                    return ConversationHandler.END
        else:
            database.insert_user(update.effective_user.id)
            database.embed_user_dialog(update.effective_user.id, self._id)
            state_dict = {}
            state_dict['state'] = [0]
            context.user_data[self._id] = state_dict
            self.lines[0].send_line(update)
            return 0

    def custom_choice(self, update, context):
        database.add_custom_choce(self._id, update.effective_user.id, update.message.text)
        update.message.reply_text('Thanks for ur suggestion')
        return ConversationHandler.END

    def retry(self, update, context):
        if update.message.text == 'Yes':
            context.user_data[self._id]['state'] = []
            database.reset_user_dialog_status(update.effective_user.id, self._id)
            self.dialog_callback(update, context)
            return 0
        else:
            update.message.reply_text('Ok')
            return ConversationHandler.END


class DialogConstructor:
    def __init__(self, dispatcher, commands_iter, pp):
        self.__dialogs = database.get_dialogs()
        self.dialogs = []
        for dialog in self.__dialogs:
            dialog_data = json.loads(dialog['dialog'])
            self.dialogs.append(Dialog(dialog['_id'], dialog_data, pp))

            dialog_name = next(commands_iter)
            callback_dispatcher = self.dialogs[-1].dialog_callback
            dispatcher.add_handler(ConversationHandler(
                entry_points=[(CommandHandler(dialog_name, callback_dispatcher,
                                              pass_user_data=True))],

                states={
                    REGULAR_CHOICE: [MessageHandler(Filters.text(dialog_data['replies']), callback_dispatcher,
                                                    pass_user_data=True)],

                    CUSTOM_CHOICE: [MessageHandler(Filters.text, self.dialogs[-1].custom_choice, pass_user_data=True)],

                    RETRY: [MessageHandler(Filters.text, self.dialogs[-1].retry, pass_user_data=True)]

                },
                # TODO fallback command
                fallbacks={},
                name=dialog_name,
                persistent=True
            ))
