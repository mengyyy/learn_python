#! /usr/bin/python3
# -*- coding:utf-8 -*-
# pip3 list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1  |
# xargs -n1 pip3 install -U

import telegram
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram.ext import RegexHandler
from telegram.ext import BaseFilter
import pprint
import re
import bs4
import requests
import os
import logzero
import subprocess
import time
import json
import sqlite3
import hashlib
from weasyprint import HTML

ROOT = '/home/Downloads/vk_bot/'
log_file_enable = True

if log_file_enable:
    log_time_str = time.strftime('%Y_%m_%d_%H_%M', time.localtime())
    log_path = '/home/Downloads/vk_bot/vk_bot_{}.log'.format(log_time_str)
    logger = logzero.setup_logger(name='vk_bot', logfile=log_path)
else:
    logger = logzero.setup_logger(name='vk_bot')


with open('/root/vk-config.json') as data_file:
    data = json.load(data_file)

chat_id = data['chat_id']
my_token = data['my_token']

RE_VK_URL = re.compile('http(s)?://(m\.)?vk\.com/doc.*')
RE_WECHAT_URL = re.compile('http(s)?://mp.weixin\.qq\.com/s/.*')

bot = telegram.Bot(my_token)
bot.send_message(chat_id=chat_id, text="Hello World")
updates = bot.get_updates()

SPLIT_SIZE = 49
cmd_7z = '7z a -v' + str(SPLIT_SIZE) + "m -y '{}' '{}' -mx0"
os.chdir(ROOT)


sql_command_create = """
    CREATE TABLE IF NOT EXISTS vk_bot_ha (
    file_hash TEXT PRIMARY KEY,
    file_name TEXT ,
    file_link TEXT,
    file_size INTEGER,
    file_id TEXT);
    """

sql_command_insert = '''INSERT INTO vk_bot_ha
    (file_hash, file_name, file_link, file_size, file_id)
    VALUES (?, ?, ?, ?, ?)'''

sql_command_show_all = 'SELECT * FROM vk_bot_ha'
sql_command_show_row = 'SELECT {} FROM vk_bot_ha'
sql_command_chech_hash = 'SELECT file_id FROM vk_bot_ha WHERE file_hash = "{}"'


db_path = os.path.join(ROOT, 'vk_bot_ha.db')
logger.info('db path is {}'.format(db_path))
connection = sqlite3.connect(db_path)
cursor = connection.cursor()
cursor.execute(sql_command_create)
cursor.close()
connection.close()


def sha256Checksum(filePath):
    with open(filePath, 'rb') as fh:
        m = hashlib.sha256()
        while True:
            data = fh.read(8192)
            if not data:
                break
            m.update(data)
        return m.hexdigest()


def file_split_7z(file, split_size=SPLIT_SIZE):
    fz = os.path.getsize(file) / 1024 / 1024
    pa = round(fz / split_size + 0.5)
    fn = os.path.splitext(file)[0].replace('.', '_')
    subprocess.call(cmd_7z.format(fn, file), shell=True)
    file_list = []
    for i in range(pa):
        file_list.append('{}.7z.{:03d}'.format(fn, i + 1))
    os.remove(file)
    return file_list


def get_url_from_message(message, refilter=RE_VK_URL):
    url_list = []
    for entity in message.entities:
        offset = entity.offset
        length = entity.length
        url = message.text[offset: offset + length]
        if refilter.match(url):
            logger.info('get valid url | {} | {}'.format(refilter, url))
            url_list.append(url)
    return url_list


def dealFileWithSqlAndBot(file, file_link, db_path, bot, update):
    try:
        file_hash = sha256Checksum(file)
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        cursor.execute(sql_command_chech_hash.format(file_hash))
        al_file_hash = cursor.fetchall()
        cursor.close()
        connection.close()
        if al_file_hash:
            os.remove(file)
            logger.info('already download file | {}'.format(al_file_hash))
            file_id = al_file_hash[0][0]
            bot.send_chat_action(chat_id=update.message.chat_id,
                                 action=telegram.ChatAction.UPLOAD_DOCUMENT)
            cc = update.message.reply_document(document=file_id,
                                               timeout=120,
                                               caption=file)
            update.message.reply_text(file_id)
            logger.info('send success {}'.format(file))
        else:
            logger.info('new file | {} | {} | {}'.format(file, fileLink, file_hash))
            bot.send_chat_action(chat_id=update.message.chat_id,
                                 action=telegram.ChatAction.UPLOAD_DOCUMENT)
            cc = update.message.reply_document(document=open(file, 'rb'),
                                               timeout=120,
                                               caption=file)
            file_id = cc.document.file_id
            update.message.reply_text(file_id)
            logger.info('send success {}'.format(file))
            file_size = os.path.getsize(file)
            os.remove(file)
            file_info = (file_hash, file, file_link,
                         file_size, file_id)
            connection = sqlite3.connect(db_path)
            with connection:
                connection.execute(sql_command_insert, file_info)
    except sqlite3.IntegrityError:
        logger.error('could not add twice {}'.format(file_info))
        return True
    except:
        logger.exception('message')
        return False
    else:
        return True

class VK_Filter(BaseFilter):

    def filter(self, message):
        logger.info('check vk link {}'.format(message.text))
        if RE_VK_URL.search(message.text):
            return True


vk_filter = VK_Filter()


def deal_vk_file_url(vk_url):
    try:
        req = requests.get(vk_url, stream=True)
        if req.headers['Content-Type'].startswith('text/html'):
            req = requests.get(vk_url)
            bso = bs4.BeautifulSoup(req.content, 'html.parser')
            file_name = bso.title.text
            surl = bso.find('iframe').attrs['src']
            req = requests.get(surl, stream=True)
        else:
            hl = req.history[-1].headers['Location']
            hlo = requests.compat.urlparse(hl)
            file_name = hlo.path.split('/')[-1]
        with open(file_name, 'wb') as f:
            for chunk in req.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
        req.close()
        if os.path.getsize(file_name) > SPLIT_SIZE * 1024 * 1024:
            file_name_list = file_split_7z(file_name)
        else:
            file_name_list = [file_name]
    except Exception as e:
        logger.exception('message')
    else:
        logger.info('{} downloaded'.format(file_name_list))
        return file_name_list, vk_url


def vk_send_file(bot, update, vk_url_list):
    gg = [deal_vk_file_url(i) for i in vk_url_list]
    logger.info('gg is |\n{}'.format(pprint.pformat(gg)))
    if len(gg) == 1 and gg[0][0] == None:
        update.message.reply_text('link is invaild point to error page')
    try:
        for fnlvu in gg:
            file_list, vk_url = fnlvu
            for file in file_list:
                dealFileWithSqlAndBot(file, vk_url, db_path, bot, update)
    except:
        logger.exception('vk_send_file failed')


def deal_vk_link(bot, update):
    update.message.reply_text('get vk link and start download ...')
    vk_url_list = get_url_from_message(update.message)
    vk_send_file(bot, update, vk_url_list)


def get_file_by_id(bot, update, args):
    logger.debug('args is {}'.format(args))
    if len(args) == 0:
        update.message.reply_text(
            'usage:\n/file BQADBQADBwADjBfoVthU7XOsRwP2Ag')
    for i in args:
        try:
            update.message.reply_document(document=i,
                                          timeout=60)
        except Exception as e:
            logger.exception('message')
            update.message.reply_text('file id error')


def mg_vk_deal(url):
    try:
        req = requests.get(url)
        bso = bs4.BeautifulSoup(req.content, 'html.parser')
        vk_bso_list = bso.findAll('div', {'class': 'vk-att-item'})
        vk_url_list = [i.a.attrs['href'] for i in vk_bso_list]
    except Exception as e:
        logger.exception('message')
    else:
        logger.info('get vk link {}'.format(vk_url_list))
        return vk_url_list


def wget_file_send(bot, update, args):
    logger.info('wget args is {}'.format(args))
    for i in args:
        wargs = ['wget', '-o', 'w.log', '--content-disposition',  i]
        try:
            subprocess.check_call(wargs)
            logger.info('wget success {}'.format(i))
            with open('w.log', 'r') as f:
                data = f.read()
            cc = data.split('\n\n')
            file_name = re.compile('.*‘(.*)’ saved').match(cc[-2]).groups()[0]
            if os.path.getsize(file_name) > SPLIT_SIZE * 1024 * 1024:
                file_name_list = file_split_7z(file_name)
            else:
                file_name_list = [file_name]
            logger.debug('file_name_list is {}'.format(file_name_list))
            for file in file_name_list:
                logger.info('try send file {}'.format(file))
                dealFileWithSqlAndBot(file, i, db_path, bot, update)
        except CalledProcessError:
            logger.exception('wget return code error')
            update.message.reply_text('wget error')
        except:
            logger.exception('wget other error')


class WECHAT_Filter(BaseFilter):

    def filter(self, message):
        logger.info('check wechat link {}'.format(message.text))
        if RE_WECHAT_URL.search(message.text):
            return True


wechat_filter = WECHAT_Filter()


def deal_wechat_link(bot, update):
    update.message.reply_text('get wechat link and start convert ...')
    wechat_url_list = get_url_from_message(update.message, refilter=RE_WECHAT_URL)
    wechat_send_file(bot, update, wechat_url_list)


def wechat_send_file(bot, update, wechat_url_list):
    for wechat_url in wechat_url_list:
        reqText = requests.get(wechat_url).text
        soup = bs4.BeautifulSoup(reqText, 'lxml')
        file = soup.title.text + '.pdf'
        htmlText = reqText.replace('data-src=', 'src=')
        html = HTML(string=htmlText)
        html.write_pdf(file)
        dealFileWithSqlAndBot(file, wechat_url, db_path, bot, update)


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


if __name__ == '__main__':
    # updater = Updater(token=my_token, request_kwargs=request_kwargs)
    updater = Updater(token=my_token)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(vk_filter, deal_vk_link))
    dp.add_handler(MessageHandler(wechat_filter, deal_wechat_link))
    dp.add_handler(CommandHandler('file', get_file_by_id,
                                  pass_args=True,))
    dp.add_handler(CommandHandler('wget', wget_file_send, pass_args=True))

    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()


# updater.stop()
# updater, dp = (0, 0)



