#! /usr/bin/python
# -*- coding:utf-8 -*-

import telegram
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram.ext import RegexHandler
import logging
import subprocess
import requests
import re
import os
import io
import fnmatch
from PIL import Image
import zbarlight


my_chatid = [123456789]
my_token = '123456789:abcdefghijklmnopq...'
send_photo_api = "https://api.telegram.org/bot{}/sendPhoto".format(my_token)
bilibili_source = 'http://bangumi.bilibili.com/jsonp/seasoninfo/{}.ver?callback=seasonListCallback'

cell_location_api = 'http://api.cellocation.com/recell/?lat={}&lon={}&n=10'
cell_location_res = '_MNC_ : `{}`\n_LAC_ : `{}`\n_CI_ : `{}`\n_LAT_ : `{}`\n_LON_ : `{}`\n_ACC_ : `{}`\n[link]({})'

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger()
BANNED_CMD = ('vi', 'nload', 'vim', 'top')
bot = telegram.Bot(my_token)
chat_id = my_chatid[0]
ipr = '^([0-9]{0,3}\.){3}([0-9]{0,3})$'



def send_test(size, test_file_name='./test.bin'):
    while True:
        with open(test_file_name, 'wb') as f:
            f.write(b'1' * size)
        try:
            bot.sendDocument(
                chat_id=chat_id, document=open(test_file_name, 'rb'))
        except:
            size -= 1
            continue
        else:
            print('size is {}'.format(size))
            break


def send_test_one(size, test_file_name='./test.bin'):
    with open(test_file_name, 'wb') as f:
        f.write(b'1' * size)
    try:
        bot.sendDocument(chat_id=chat_id, document=open(test_file_name, 'rb'))
    except:
        print('failed size {}'.format(size))
    else:
        print('success size {}'.format(size))


def file_match_pattern(pattern, path='.'):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result


def file_match_name(name, path='.', reflag=False):
    result = []
    for root, dirs, files in os.walk(path):
        if not reflag:
            if name in files:
                result.append(os.path.join(root, name))
        else:
            rr = re.compile(name)
            for file_name in files:
                if rr.match(file_name) is not None:
                    result.append(os.path.join(root, file_name))
    return result


def qr_code_decode(file_path):
    with open(file_path, 'rb') as image_file:
        image = Image.open(image_file)
        image.load()
    # Convert image to gray scale (8 bits per pixel).
    converted_image = image.convert('L')
    image.close()
    raw = converted_image.tobytes()  # Get image data.
    width, height = converted_image.size  # Get image size.
    code = zbarlight.qr_code_scanner(raw, width, height)
    if len(code):
        print('QR code: %s' % code.decode('utf-8'))
        return code.decode('utf-8')
    else:
        logger.info()


def deal_qrcode(bot, update):
    nf = bot.getFile(update.message.photo[-1].file_id)
    ng = nf.download('./tmp.jpg')
    bot.sendMessage(chat_id=update.message.chat_id,
                    text='OR code:\n{}'.format(qr_code_decode('./tmp.jpg')))


def auto_ping(bot, update):
    logger.info('ip {}'.format(update.message.text))
    ip = requests.packages.urllib3.util.url.parse_url(update.message.text).netloc
    bot.sendChatAction(chat_id=update.message.chat_id,
                       action=telegram.ChatAction.TYPING)
    p = subprocess.Popen(["ping", "-c", "4", ip],
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    output, err = p.communicate()
    rc = p.returncode
    if len(output):
        bot.sendMessage(chat_id=update.message.chat_id,
                    text=output.decode('utf-8'))
    elif len(err):
        bot.sendMessage(chat_id=update.message.chat_id,
                    text=err.decode('utf-8'))

def echo(bot, update):
    bot.sendChatAction(chat_id=update.message.chat_id,
                       action=telegram.ChatAction.TYPING)
    bot.sendMessage(chat_id=update.message.chat_id,
                    text="*bold* _italic_ `fixed width font` [link](http://google.com)",
                    parse_mode=telegram.ParseMode.MARKDOWN)
    bot.sendMessage(chat_id=update.message.chat_id,
                    text='<b>bold</b> <i>italic</i> <a href="http://google.com">link</a>.',
                    parse_mode=telegram.ParseMode.HTML)


def cmd_send_photo(bot, update):
    bot.sendChatAction(chat_id=update.message.chat_id,
                       action=telegram.ChatAction.UPLOAD_PHOTO)
    bot.sendPhoto(chat_id=update.message.chat_id,
                  photo=open('./t_logo.png', 'rb'))
    bot.sendPhoto(chat_id=update.message.chat_id,
                  photo='https://telegram.org/img/SiteAndroid.jpg?1')


def cmd_you_get_send(bot, update, args):
    for link in args:
        try:
            p = subprocess.Popen(["you-get", '-o', '/tmp', link],
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            output, err = p.communicate()
            rc = p.returncode
        except:
            update.message.reply_text('you-get failed')
        else:
            update.message.reply_text('Done')


def cmd_gm5(bot, update, args):
    logger.info('gm5 args {}'.format(args))
    for filename in args:
        try:
            bot.sendDocument(chat_id=update.message.chat_id,
                             document=open(filename, 'rb'))
        except:
            file_list = file_match_name(filename)
            if len(file_list):
                for file in file_list:
                    bot.sendMessage(chat_id=update.message.chat_id,
                                    text='*{}*'.format(file),
                                    parse_mode=telegram.ParseMode.MARKDOWN)
                    bot.sendChatAction(chat_id=update.message.chat_id,
                                       action=telegram.ChatAction.UPLOAD_DOCUMENT)
                    bot.sendDocument(chat_id=update.message.chat_id,
                                     document=open(file, 'rb'))
            else:
                bot.sendMessage(chat_id=update.message.chat_id,
                                text='<i>None found</i>',
                                parse_mode=telegram.ParseMode.HTML)


def cmd_gm5_re(bot, update, args):
    logger.info('gm5_re args {}'.format(args))
    for filename in args:
        file_list = file_match_name(filename, reflag=True)
        if len(file_list):
            for file in file_list:
                bot.sendMessage(chat_id=update.message.chat_id,
                                text='*{}*'.format(file),
                                parse_mode=telegram.ParseMode.MARKDOWN)
                bot.sendChatAction(chat_id=update.message.chat_id,
                                   action=telegram.ChatAction.UPLOAD_DOCUMENT)
                bot.sendDocument(chat_id=update.message.chat_id,
                                 document=open(file, 'rb'))
        else:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text='<i{}/>'.format(file),
                            parse_mode=telegram.ParseMode.HTML)


def cmd_ping(bot, update, args):
    logger.info('ping args {}'.format(args))
    for ip in args:
        bot.sendChatAction(chat_id=update.message.chat_id,
                           action=telegram.ChatAction.TYPING)
        p = subprocess.Popen(["ping", "-c", "4", ip],
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        output, err = p.communicate()
        rc = p.returncode
        bot.sendMessage(chat_id=update.message.chat_id,
                        text=output.decode('utf-8'))


def cmd_root(bot, update, args):
    logger.info('cmd args {}'.format(args))
    if (update.message.chat_id not in my_chatid):
        update.message.reply_text('No Admin')
    else:
        if len(set(args).intersection(BANNED_CMD)):
            update.message.reply_text('Banned command')
        elif args[0] == 'cd':
            try:
                os.chdir(args[1])
                update.message.reply_text(os.path.abspath('.'))
            except:
                update.message.reply_text('chang dir failed')
        else:
            bot.sendChatAction(chat_id=update.message.chat_id,
                               action=telegram.ChatAction.TYPING)
            args2command = ''
            for i in args:
                if i == '»':
                    logger.info('"»" will replaced with">>"')
                    args2command += '>>' + ' '
                else:
                    args2command += i + ' '
            try:
                p = subprocess.Popen(args2command,
                                     stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     shell=True)
                output, err = p.communicate(timeout=120)
                rc = p.returncode
            except subprocess.TimeoutExpired:
                logger.info('Time out')
                update.message.reply_text('process cmd time out')
            except:
                update.message.reply_text('process cmd failed')
            else:
                for i in range(0, len(output), 4080):
                    output_dis = output.decode('utf-8')[i:i + 4080]
                    bot.sendMessage(chat_id=update.message.chat_id,
                                    text='respon :\n{}'.format(output_dis))
                bot.sendMessage(chat_id=update.message.chat_id,
                                text='returncode : {}'.format(rc))
                if len(err) > 0:
                    bot.sendMessage(chat_id=update.message.chat_id,
                                    text='errinfo :\n{}'.format(err.decode('utf-8')))


def cmd_bilibili(bot, update, args):
    respon_str = ''
    logger.info('bilibili args {}'.format(args))
    for i in args:
        baseUrl = bilibili_source.format(i)
        req = requests.get(baseUrl)
        linklist = re.findall(
            'http://bangumi.bilibili.com/anime/' + i + '/play#\d{0,6}', req.text)
        if len(linklist) > 0:
            for link in linklist[::-1]:
                respon_str += link + ' '
            update.message.reply_text(
                you_get_head + respon_str + you_get_tail.format(i))
        else:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text='None Found')


def cmd_cell_location(bot, update, args):
    res = requests.get(cell_location_api.format(args[0], args[1]))
    if len(res.content):
        for i in res.json():
            respon = cell_location_res.format(
                i['mnc'], i['lac'], i['ci'],
                i['location']['lat'],
                i['location']['lon'], i['acc'],
                cell_location_api.format(args[0], args[1])
            )
            bot.sendMessage(chat_id=update.message.chat_id,
                            text=respon,
                            parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text='/cell lon lat',
                        parse_mode=telegram.ParseMode.MARKDOWN)


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


def unknown(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id,
                    text="Didn't understand that command.")


def main():
    updater = Updater(token=my_token)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(
        Filters.entity(telegram.MessageEntity.URL), echo))
    dp.add_handler(MessageHandler(Filters.photo, deal_qrcode))
    dp.add_handler(CommandHandler('photo', cmd_send_photo))
    dp.add_handler(CommandHandler('gm5', cmd_gm5, pass_args=True))
    dp.add_handler(CommandHandler('gm5re', cmd_gm5_re, pass_args=True))
    dp.add_handler(CommandHandler('ping', cmd_ping, pass_args=True))
    dp.add_handler(CommandHandler('cmd', cmd_root, pass_args=True))
    dp.add_handler(CommandHandler('bilibili', cmd_bilibili, pass_args=True))
    dp.add_handler(CommandHandler('cell', cmd_cell_location, pass_args=True))
    dp.add_handler(MessageHandler(Filters.command, unknown))
    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()


