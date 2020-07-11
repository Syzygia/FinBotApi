import telegram
from flask import request
import flask
from pyngrok import ngrok

app = flask.Flask(__name__)

global bot
bot = telegram.Bot(token='941110663:AAGkCQ6F9qKA2R8LDJVuaCSUncsG4AOr-Tk')

@app.route('/api/message/update', methods=['POST'])
def webhook_handler():
    if request.method == "POST":
        # retrieve the message in JSON and then transform it to Telegram object
        update = telegram.Update.de_json(request.get_json(force=True), bot)

        chat_id = update.message.chat.id

        # Telegram understands UTF-8, so encode text for unicode compatibility
        text = update.message.text

        # repeat the same message back (echo)
        bot.sendMessage(chat_id=chat_id, text=text)

    return 'ok'

@app.route('/', methods=['GET'])
def index():
    ngrok.connect(5000, 'http', '127.0.0.1')
    tunnels = ngrok.get_tunnels()
    index = 0 if "https" in tunnels[0].public_url else 1
    webhook = tunnels[index].public_url + '/api/message/update'
    result = bot.set_webhook(webhook)
    if result:
        print('ok')
    else:
        print('fuck')
    return 'ok'
