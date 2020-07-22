import asyncio

import telegram
from pyngrok import ngrok
from telegram.ext import (Updater, PicklePersistence)

import dialog_constructor

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def index():
    ngrok.connect(80, 'http', '127.0.0.1')
    tunnels = ngrok.get_tunnels()
    index = 0 if "https" in tunnels[0].public_url else 1
    webhook = tunnels[index].public_url
    bot = telegram.bot.Bot('1073356395:AAH1rkcoi6FzXXIysMLae8Exn3i4wuMj5l4')
    bot.set_webhook(webhook)

    pp = PicklePersistence(filename='conversationbot')
    updater = Updater(bot=bot, use_context=True, persistence=pp)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    bot_behaviour = dialog_constructor.DialogConstructor(dp, iter(['quiz1']), pp)

    updater.start_webhook(listen='127.0.0.1',
                          port=80,
                          webhook_url=webhook)
    updater.idle()


if __name__ == '__main__':
    index()
