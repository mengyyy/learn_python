#!/usr/bin/env python

'''Using Webhook and self-signed certificate'''

# This file is an annotated example of a webhook based bot for
# telegram. It does not do anything useful, other than provide a quick
# template for whipping up a testbot. Basically, fill in the CONFIG
# section and run it.
# Dependencies (use pip to install them):
# - python-telegram-bot: https://github.com/leandrotoledo/python-telegram-bot
# - Flask              : http://flask.pocoo.org/
# Self-signed SSL certificate (make sure 'Common Name' matches your FQDN):
# $ openssl req -new -x509 -nodes -newkey rsa:1024 -keyout server.key -out server.crt -days 3650
# You can test SSL handshake running this script and trying to connect using wget:
# $ wget -O /dev/null https://$HOST:$PORT/

from flask import Flask, request
import time
import telegram
from telegram import Bot
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
import logging

# CONFIG
TOKEN = '123456789:asdasdsadsadasdasd'
HOST = 'yourdomain.com'  # Same FQDN used when generating SSL Cert
PORT = 8443
CERT = 'path to server.crt'
CERT_KEY = 'path to server.key'


logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger()

bot = telegram.Bot(TOKEN)
dispatcher = Dispatcher(bot=bot, update_queue=None, workers=4)
app = Flask(__name__)
context = (CERT, CERT_KEY)


def start(bot, update):
    bot.sendMessage(update.message.chat_id, text='Hi!')


def help(bot, update):
    bot.sendMessage(update.message.chat_id, text='Help!')


def echo(bot, update):
    bot.sendMessage(update.message.chat_id, text=update.message.text)


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

@app.route('/')
def hello():
    return 'Hello World!'


@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    update = telegram.update.Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'OK'


def setWebhook():
    bot.setWebhook(webhook_url='https://%s:%s/%s' % (HOST, PORT, TOKEN),
                   certificate=open(CERT, 'rb'))
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(MessageHandler(Filters.text, echo))
    dispatcher.add_error_handler(error)

if __name__ == '__main__':
    setWebhook()
    time.sleep(5)
    app.run(host='0.0.0.0',
            port=PORT,
            ssl_context=context,
            debug=True)

