import asyncio

import telegram as tg
from pyngrok import ngrok
from telegram import ReplyKeyboardMarkup
from telegram.ext import (Updater, PicklePersistence, CommandHandler)

import dialog_constructor

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def begin(update, context):
    update.message.reply_text('Здравствуйте, я бесплатный финансовый бот-советник "FINBOT.AI".'
                              ' Буду рад ответить на любые вопросы, связанные с финансами.')
    update.message.reply_text('Я определяю Ваши предпочтения, запоминаю и обрабатываю их,'
                              ' а на основе этих данных предлагаю те темы, продукты и услуги,'
                              ' которые подходят конкретно Вам.')
    update.message.reply_text(' О чем бы Вы хотели узнать?',
                              reply_markup=ReplyKeyboardMarkup([['Вложить или накопить деньги'],
                                                                ['Инвестиции для чайников'],
                                                                ['Свой:вопрос']],
                                                               one_time_keyboard=True))
    return


def index():
    ngrok.connect(80, 'http', '127.0.0.1')
    tunnels = ngrok.get_tunnels()
    index = 0 if "https" in tunnels[0].public_url else 1
    webhook = tunnels[index].public_url
    bot = tg.bot.Bot('1301191797:AAGBBBCqx9opRaanCsQJc_E04LqYhjYRcJw')
    bot.set_webhook(webhook)

    pp = PicklePersistence(filename='conversationbot')
    updater = Updater(bot=bot, use_context=True, persistence=pp)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', begin))
    bot_behaviour = dialog_constructor.DialogConstructor(dp, pp)

    updater.start_webhook(listen='127.0.0.1',
                          port=80,
                          webhook_url=webhook)
    updater.idle()


if __name__ == '__main__':
    index()
