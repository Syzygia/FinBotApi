import telegram
from pyngrok import ngrok
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler, PicklePersistence)
import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

def start(update, context):
    reply_text = "Hi! I am FinBotAi"
    if context.user_data:
        reply_text += "Hello again"
    else:
        reply_text += "Whay is your problem?"
    update.message.reply_text(reply_text)
    return 0

def resend_back(update, context):
    update.message.reply_text(update.message.text)
    return 0

def done(update, context) :
    update.message.reply_text("Nice chating, see u later")

def index():
    ngrok.connect(80, 'http', '127.0.0.1')
    tunnels = ngrok.get_tunnels()
    index = 0 if "https" in tunnels[0].public_url else 1
    webhook = tunnels[index].public_url
    bot = telegram.bot.Bot('1073356395:AAH1rkcoi6FzXXIysMLae8Exn3i4wuMj5l4')
    bot.set_webhook(webhook)
    updater = Updater(bot=bot, use_context=True)

    # Get the dispatcher to register handlers

    dp = updater.dispatcher
    end_command = CommandHandler('done', done)
    dp.add_handler(end_command)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            0: [MessageHandler(Filters.text,resend_back)]
        },
        fallbacks=[CommandHandler('done', done)]
    )
    dp.add_handler(conv_handler)
    updater.start_webhook(listen='127.0.0.1',
                      port=80,
                      webhook_url=webhook)
    updater.idle()


if __name__ == '__main__':
    index()
