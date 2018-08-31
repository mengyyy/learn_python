#! /usr/bin/python3
# -*- coding:utf-8 -*-

import itchat
from itchat.content import *
import telegram
import logzero
import os
import tempfile
import time
import datetime

LOG2FILE = True
if LOG2FILE:
    logPath = 'wechat.log'
else:
    logPath = None

logger = logzero.setup_logger("wechat telegram", logfile=logPath, maxBytes=2**20, backupCount=10)

my_token = "telegram bot token"
bot = telegram.Bot(my_token)

telegram_chat_id = 1234567890
chat_id = telegram_chat_id
bot.send_message(chat_id=chat_id, text="Hello World")


@itchat.msg_register([TEXT, MAP, CARD, NOTE, SHARING])
def text_person(msg):
    logger.info("text_person | {} | {}".format(msg.user.NickName, msg.text))
    # msg.user.send('%s: %s' % (msg.type, msg.text))
    info = "<b>{}</b>\n<i>{}</i>\n<code>{}</code>".format(datetime.datetime.now(), msg.user.NickName, msg.text)
    bot.send_message(
        chat_id=chat_id,
        text=info,
        parse_mode=telegram.ParseMode.HTML,
    )


@itchat.msg_register([TEXT, MAP, CARD, NOTE, SHARING], isGroupChat=True)
def text_group(msg):
    logger.info("text_group | {} | {}".format(msg.user.NickName, msg.text))
    info = "<b>{} in {}</b>\n<i>{}</i>\n<code>{}</code>".format(
        msg.get("ActualNickName", "ActualNickName"), msg.user.NickName, datetime.datetime.now(), msg.text
    )
    bot.send_message(
        chat_id=chat_id,
        text=info,
        parse_mode=telegram.ParseMode.HTML,
        disable_notification=True,
    )


@itchat.msg_register([PICTURE, RECORDING, ATTACHMENT, VIDEO])
def download_files_person(msg):
    logger.info("download_files_person | {} | {}".format(msg.user.NickName, msg.fileName))
    msg.download(msg.fileName)
    info = "<b>{}</b>\n<i>{}</i>\n<code>{}</code>".format(datetime.datetime.now(), msg.user.NickName, msg.fileName)
    if os.path.getsize(msg.fileName) == 0:
        os.remove(msg.fileName)
        return
    try:
        for _ in range(5):
            result = bot.send_document(
                chat_id=chat_id,
                document=open(msg.fileName, "rb"),
                caption=info,
                parse_mode=telegram.ParseMode.HTML,
                disable_notification=True,
            )
            if result:
                break
    finally:
        os.remove(msg.fileName)


@itchat.msg_register([PICTURE, RECORDING, ATTACHMENT, VIDEO], isGroupChat=True)
def download_files_group(msg):
    logger.info("download_files_group | {} | {}".format(msg.user.NickName, msg.fileName))
    msg.download(msg.fileName)
    info = "<b>{} in {}</b>\n<i>{}</i>\n<code>{}</code>".format(
        msg.get("ActualNickName", "ActualNickName"), msg.user.NickName, datetime.datetime.now(), msg.fileName
    )
    if os.path.getsize(msg.fileName) == 0:
        os.remove(msg.fileName)
        return
    try:
        for _ in range(5):
            result = bot.send_document(
                chat_id=chat_id,
                document=open(msg.fileName, "rb"),
                caption=info,
                parse_mode=telegram.ParseMode.HTML,
                disable_notification=True,
            )
            if result:
                break
    finally:
        os.remove(msg.fileName)


def qrCallback(uuid, status, qrcode):
    logger.info(
        "qrCallback params | uuid {} | status {} | qrcode {}".format(
            uuid, status, qrcode
        )
    )
    if status == "0":
        temp = tempfile.NamedTemporaryFile(delete=False)
        temp.write(qrcode)
        temp.close()
        try:
            bot.send_photo(chat_id=chat_id, photo=open(temp.name, "rb"))
        finally:
            os.remove(temp.name)
    elif status == "200":
        logger.info("Logged in!")
    elif status == "201":
        logger.info("Confirm")


def loginCallback():
    logger.info("finish login")


def exitCallback():
    logger.info("exit")


itchat.auto_login(
    hotReload=True,
    qrCallback=qrCallback,
    loginCallback=loginCallback,
    exitCallback=exitCallback,
)

friends = itchat.get_friends()

itchat.run(True)
