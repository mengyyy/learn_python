#! /usr/bin/python
# -*- coding:utf-8 -*-

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
import logging
import subprocess
import time
import json
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import pytesseract


log_file_enable = True
logger = logging.getLogger('tcp_test')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s')

if log_file_enable:
    log_time_str = time.strftime('%Y_%m_%d_%H_%M', time.localtime())
    log_path = '/home/Downloads/vk_bot_{}.log'.format(log_time_str)
    fh = logging.FileHandler(log_path)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)

with open('/root/vk-config.json') as data_file:
    data = json.load(data_file)

chat_id = data['chat_id']
my_token = data['my_token']

vk_url_re = re.compile('https://(m\.)?vk\.com/doc\d*_\d*')

bot = telegram.Bot(my_token)
bot.send_message(chat_id=chat_id, text="Hello World")
updates = bot.get_updates()

cmd_7z = "7z a -v49m -y '{}' '{}' -mx0"
os.chdir('/home/Downloads')

vk_feed_list = [chat_id]

cov = [slice(11, 30),
       slice(31, 48),
       slice(49, 69),
       slice(70, 81),
       slice(82, 94),
       slice(95, 121),
       slice(125, 140),
       slice(140, 150)]

lan = ['莫讲话我系一等良民',
       '就算你砌我生猪肉',
       '我都大把钱揾啲大状帮我',
       '我谂我唔洗指意坐监嗝',
       '你咪以为有钱大嗮啊',
       'Sorry，有钱真系大嗮',
       '不过我谂佢唔会明呢个意境',
       '哈哈哈哈 佢点会明啊']

font = ImageFont.truetype(font='/home/Downloads/deal_image/NotoSansCJKsc-hinted/NotoSansCJKsc-Regular.otf', size=13)
# font = ImageFont.truetype(font='/home/Downloads/deal_image/Cairo/Cairo-Regular.ttf', size=13)

def file_split_7z(file, split_size=49):
    fz = os.path.getsize(file) / 1024 / 1024
    pa = round(fz / split_size + 0.5)
    fn = os.path.splitext(file)[0]
    subprocess.call(cmd_7z.format(fn, file), shell=True)
    file_list = []
    for i in range(pa):
        file_list.append('{}.7z.{:03d}'.format(fn, i + 1))
    os.remove(file)
    return file_list


def get_url_from_message(message):
    url_list = []
    for entity in message.entities:
        offset = entity.offset
        length = entity.length
        url_list.append(message.text[offset: offset + length])
    return url_list


class VK_Filter(BaseFilter):

    def filter(self, message):
        logger.info('check vk link {}'.format(message.text))
        if vk_url_re.search(message.text):
            return True


vk_filter = VK_Filter()


def deal_vk_file_url(vk_url):
    try:
        req = requests.get(vk_url)
        if req.headers['Content-Type'].startswith('text/html'):
            bso = bs4.BeautifulSoup(req.content, 'html.parser')
            file_name = bso.title.text
            surl = bso.find('iframe').attrs['src']
            req = requests.get(surl)
        else:
            hl = req.history[-1].headers['Location']
            hlo = requests.compat.urlparse(hl)
            file_name = hlo.path.split('/')[-1]
        with open(file_name, 'wb') as f:
            f.write(req.content)
        if len(req.content) > 49 * 1024 * 1024:
            file_name_list = file_split_7z(file_name)
        else:
            file_name_list = [file_name]
    except Exception as e:
        logger.exception('message')
    else:
        logger.info('{} downloaded'.format(file_name_list))
        return file_name_list


def vk_send_file(bot, update, vk_url_list):
    gg = [deal_vk_file_url(i) for i in vk_url_list]
    logger.info('gg is\n')
    logger.info(pprint.pformat(gg))
    for file_list in gg:
        for file in file_list:
            try:
                bot.send_chat_action(chat_id=update.message.chat_id,
                                     action=telegram.ChatAction.UPLOAD_DOCUMENT)
                cc = update.message.reply_document(document=open(file, 'rb'),
                                                   timeout=60)
                update.message.reply_text(cc.document.file_id)
            except Exception as e:
                logger.exception('message')
            finally:
                os.remove(file)


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


def deal_image_ocr(bot, update):
    ocr_str = ''
    try:
        file_id = update.message.photo[-1].file_id
        tf = bot.getFile(file_id)
        file_name = tf.file_path.split('/')[-1]
        logger.info('get file {}'.format(file_name))
        with open(file_name, 'wb+') as f:
            tf.download(out=f)
            image = Image.open(f)
            image.load()
        os.remove(file_name)
        ocr_str = pytesseract.image_to_string(image, lang='eng+chi_sim')
        if ocr_str:
            logger.info('OCR result {}'.format(ocr_str))
            update.message.reply_text(ocr_str)
    except Exception as e:
        logger.exception('message')
        update.message.reply_text('ocr failed~')


def deal_document_ocr(bot, update):
    ocr_str = ''
    logger.info(pprint.pformat(update.message.to_dict()))
    dc = update.message.document
    try:
        if dc.mime_type.startswith('image') and dc.file_size < 50 * 1024 * 1024:
            tf = bot.getFile(dc.file_id)
            tf.download(dc.file_name)
            logger.info('start ocr deal')
            ocr_str = pytesseract.image_to_string(
                Image.open(dc.file_name), lang='eng+chi_sim')
            os.remove(dc.file_name)
        if ocr_str:
            logger.info('OCR result {}'.format(ocr_str))
            update.message.reply_text(ocr_str)
    except Exception as e:
        logger.exception('message')
        update.message.reply_text('ocr failed~')


def deal_url_ocr(bot, update, args):
    ocr_str = ''
    logger.info('agrs in orc command is {}'.format(args))
    if len(args) == 0:
        update.message.reply_text('/ocr image_url')
    for i in args:
        try:
            logger.info('try get image from {}'.format(i))
            heq = requests.head(i)
            if heq.headers['Content-Type'].startswith('image'):
                req = requests.get(i, stream=True)
                req.raw.decode_content = True
                img = Image.open(req.raw)
                bot.send_chat_action(chat_id=update.message.chat_id,
                                     action=telegram.ChatAction.TYPING)
                ocr_str = pytesseract.image_to_string(img, lang='eng+chi_sim')
                if ocr_str:
                    logger.info('OCR result {}'.format(ocr_str))
                    update.message.reply_text(ocr_str)
        except Exception as e:
            logger.exception('message')
            update.message.reply_text('ocr failed~')


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


def sorry_gif(bot, update):
    logger.debug('get text {}'.format(update.message.text))
    try:
        lan_get = update.message.text.split('\n')
        lan_len = len(lan_get)
        if  lan_len< 8:
            [lan_get.append(lan[lan_len+i]) for i in range(8-lan_len)]
        logger.debug('lan_get is {}'.format(lan_get))
        frame_list = [Image.open('/home/Downloads/deal_image/gif_frame/{}.gif'.format(i)) for i in range(152)]
        img_list = [i.convert("RGBA") for i in frame_list]
        draw_list = [ImageDraw.Draw(i) for i in img_list]
        for i in draw_list:
            i.rectangle((0,154,320,170), (0,0,0))
        for co, la in zip(cov,lan_get[:8]):
            for draw in draw_list[co]:
                width = font.getsize(la)[0]
                draw.text(((320-width)/2,152), la, (255,255,255), font=font)
        frame_list[0].save('/home/Downloads/ggg.gif', save_all=True, append_images=img_list[1:])
        bot.send_chat_action(chat_id=update.message.chat_id,
                                     action=telegram.ChatAction.UPLOAD_DOCUMENT)
        update.message.reply_document(open('/home/Downloads/ggg.gif', 'rb'), timeout=60)
        os.remove('/home/Downloads/ggg.gif')   
    except:
        logger.exception('error because\n')


def deal_start(bot, update):
    update.message.reply_text('请输入八句对白 回车分割 下面是个例子', timeout=10)
    bot.send_chat_action(chat_id=update.message.chat_id,
                         action=telegram.ChatAction.UPLOAD_DOCUMENT)
    update.message.reply_document('CgADBQADFgADkCrAV_5RgRW7RjPwAg', timeout=60)


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


if __name__ == '__main__':
    # updater = Updater(token=my_token, request_kwargs=request_kwargs)
    updater = Updater(token=my_token)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.photo, deal_image_ocr))
    dp.add_handler(MessageHandler(Filters.document, deal_document_ocr))
    dp.add_handler(CommandHandler('ocr', deal_url_ocr, pass_args=True))

    dp.add_handler(MessageHandler(Filters.text, sorry_gif))
    dp.add_handler(CommandHandler('start', deal_start))
    dp.add_error_handler(error)


    updater.start_polling()
    updater.idle()


