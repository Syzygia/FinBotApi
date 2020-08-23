import json

from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from telegram.ext import (CommandHandler, MessageHandler, Filters,
                          ConversationHandler, CallbackQueryHandler)

import database
import FinBot

REGULAR_CHOICE, CUSTOM_CHOICE, RETRY, SUGGESTION = range(4)
BACK, HOME, HELP = range(3)

class Line:
    def __init__(self, data, replies, custom_choices):
        self.keyboard = []
        self.text = data['text']
        self.leads = []
        self.values = []
        self.is_test_question = data['type'] == 'test_question'
        self.should_send_next = False
        self.custom_answers = set()
        self.type = data['type']
        if self.type == 'test_final_answer':
            self.value = int(data['value'])
        for key, value in data['replies'].items():
            self.keyboard.append([replies[int(key)].strip()])
            if int(key) in custom_choices:
                self.custom_answers.add(len(self.keyboard) - 1)
            if self.is_test_question:
                self.leads.append(value['leads'])
                self.values.append(value['value'])
            else:
                self.leads.append(value)
        self.is_custom = False

    def get_next(self, update, context=None):
        return self.leads[self.get_answer_num(update, context)]

    def get_answer_num(self, update, context=None):
        self.is_custom = False
        answer_num = self.keyboard.index([update.message.text])
        if answer_num in self.custom_answers:
            self.is_custom = True
        return answer_num

    def send_line(self, update, context=None):
        self.should_send_next = False
        if len(self.keyboard) == 0:
            self.should_send_next = True
            update.message.reply_text(self.text)
        else:
            update.message.reply_text(self.text,
                                      reply_markup=ReplyKeyboardMarkup(self.keyboard, one_time_keyboard=True))
            update.message.reply_markdown('.',
                                          reply_markup=InlineKeyboardMarkup(
                                              [[InlineKeyboardButton('Назад', callback_data=BACK),
                                                InlineKeyboardButton('Домой', callback_data=HOME),
                                                InlineKeyboardButton('Помощь', callback_data=HELP)]]))

    def get_test_value(self, update, context):
        return self.values[self.get_answer_num(update, context)]


class Dialog:
    def __init__(self, _id, dialog_data, pp, name):
        self._id = _id
        self.lines = []
        self.pp = pp
        self.name = name
        for line in dialog_data['lines']:
            self.lines.append(Line(line, dialog_data['replies'], set(dialog_data['custom_choices'])))

    def dialog_query_callback(self, update, context):
        query = update.callback_query
        query.answer()
        update.message = update.callback_query.message
        if int(query.data) == BACK:
            last_state = context.user_data[self._id]['state']
            if len(last_state) >= 2:
                last_state[-1] =last_state[-2]
                self.lines[last_state[-1]].send_line(update, context)
            return REGULAR_CHOICE
        if int(query.data) == HOME:
            context.user_data[self._id]['state'] = []
            FinBot.begin(update, context)
            return ConversationHandler.END
        if int(query.data) == HELP:
            update.message.reply_text(
                'Пожайлуста сообщите нам о том что бы вы хотели увидеть в нашем боте, что вас беспокоит',
                reply_markup=ReplyKeyboardRemove())
            return SUGGESTION

    def dialog_callback(self, update, context):
        #        self.pp.flush()
        if context.user_data and self._id in context.user_data and context.user_data[self._id]['state'] != []:
            if context.user_data[self._id]['state'][-1] == ConversationHandler.END:
                # Message if want to complete questions once again
                update.message.reply_text('Wonna try it once again?',
                                          reply_markup=ReplyKeyboardMarkup([['Yes'], ['No']], one_time_keyboard=True))
                return RETRY
            else:
                last_answered_line = self.get_last_answered(update, context)
                next_state = last_answered_line.get_next(update)
                context.user_data[self._id]['state'].append(next_state)
                database.update_dialog_status(update.effective_user.id,
                                              self._id, last_answered_line.get_answer_num(update))
                if last_answered_line.is_test_question:
                    self.update_test(line=last_answered_line, update=update, context=context)
                if last_answered_line.is_custom:
                    # update.message.reply_text('pls tell us what u want here')
                    return CUSTOM_CHOICE
                if next_state != ConversationHandler.END:
                    self.lines[next_state].send_line(update, context)
                    if self.lines[next_state].type == 'test_final':
                        result = self.finalize_test(next_state, context)
                        self.lines[result].send_line(update, context)
                        context.user_data[self._id]['state'].append(result)
                        return REGULAR_CHOICE

                    if self.lines[next_state].should_send_next:
                        self.lines[next_state + 1].send_line(update, context)
                        context.user_data[self._id]['state'].append(next_state + 1)
                    return REGULAR_CHOICE
                else:
                    # write last message here
                    update.message.reply_text('thanks for ur info')
                    return ConversationHandler.END
        else:
            database.insert_user(update.effective_user.id)
            database.embed_user_dialog(update.effective_user.id, self._id)
            next_state = -1 if self.name == 'Вложить или накопить деньги' else 0
            state_dict = {'state': [next_state], 'test_val': 0}
            context.user_data[self._id] = state_dict
            self.lines[next_state].send_line(update)
            if self.lines[next_state].should_send_next:
                self.lines[next_state + 1].send_line(update, context)
                context.user_data[self._id]['state'].append(next_state + 1)
            return REGULAR_CHOICE

    def custom_choice(self, update, context):
        database.add_custom_choice(self._id, update.effective_user.id, update.message.text)
        last_answered = self.get_last_answered(update, context)
        last_answered.send_line(update, context)
        return REGULAR_CHOICE

    def get_last_answered(self, update, context):
        return self.lines[context.user_data[self._id]['state'][-1]]

    def retry(self, update, context):
        if update.message.text == 'Yes':
            context.user_data[self._id]['state'] = []
            database.reset_user_dialog_status(update.effective_user.id, self._id)
            self.dialog_callback(update, context)
            return REGULAR_CHOICE
        else:
            update.message.reply_text('Ok')
            return ConversationHandler.END

    def update_test(self, line, update, context):
        context.user_data[self._id]['test_val'] += line.get_test_value(update, context)

    def finalize_test(self, current_state, context):
        current_state += 1
        lowest_diff = 100
        line_num = -1
        while self.lines[current_state].type == 'test_final_answer':
            res = self.lines[current_state].value - context.user_data[self._id]['test_val']
            if 0 <= res < lowest_diff:
                line_num = current_state
                lowest_diff = res
            current_state += 1
        return line_num

    def suggestion(self, update, context):
        database.add_suggestion(update.effective_user.id, update.message.text)
        update.message.reply_text('Спасибо за ваш отзыв')
        self.lines[context.user_data[self._id]['state'][-1]].send_line(update, context)
        return REGULAR_CHOICE


class DialogConstructor:
    def __init__(self, dispatcher, pp):
        self.__dialogs = database.get_dialogs()
        self.dialogs = []
        for dialog_js in self.__dialogs:
            dialog_data = json.loads(dialog_js['dialog'])
            dialog = Dialog(dialog_js['_id'], dialog_data, pp, dialog_js['name'])
            self.dialogs.append(dialog)

            dispatcher.add_handler(ConversationHandler(
                entry_points=[(MessageHandler(Filters.text(dialog_js['name']), dialog.dialog_callback,
                                              pass_user_data=True))],

                states={
                    REGULAR_CHOICE: [MessageHandler(Filters.text, dialog.dialog_callback,
                                                    pass_user_data=True),
                                     CallbackQueryHandler(dialog.dialog_query_callback)],

                    CUSTOM_CHOICE: [MessageHandler(Filters.text, dialog.custom_choice, pass_user_data=True)],

                    RETRY: [MessageHandler(Filters.text, dialog.retry, pass_user_data=True)],

                    SUGGESTION: [MessageHandler(Filters.text, dialog.suggestion, pass_user_data=True)]
                },
                # TODO fallback command
                fallbacks={},
                name=dialog_js['name'],
                persistent=True
            ))
