#! /usr/bin/python
# -*- coding:utf-8 -*-

import telegram
from telegram.ext import Updater
from telegram.ext import RegexHandler
import logging
import requests
import re
import json
import hashlib
import base64

test_163 = 'http://music.163.com/#/song/462686590'
re163 = re.compile(
    '(http://music\.163\.com/(#/)*song)(/)*(\?id=)*(?P<id>\d{1,10})')
header = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip,deflate,sdch',
            'Accept-Language': 'zh-CN,zh;q=0.8,gl;q=0.6,zh-TW;q=0.4',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'music.163.com',
            'Referer': 'http://music.163.com/',
            'User-Agent':
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 Safari/537.36'  # NOQA
        }
        
my_token = '1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ'
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger()


def encrypted_id(id):
    magic = bytearray('3go8&$8*3*3h0k(2)2', 'u8')
    song_id = bytearray(id, 'u8')
    magic_len = len(magic)
    for i, sid in enumerate(song_id):
        song_id[i] = sid ^ magic[i % magic_len]
    m = hashlib.md5(song_id)
    result = m.digest()
    result = base64.urlsafe_b64encode(result)
    result = result.replace(b'/', b'_')
    result = result.replace(b'+', b'-')
    return result.decode('utf-8')


def getid_then_send_song(bot, update, musicID):
    savePath = '/home/Downloads/{}.mp3'
    action = 'http://music.163.com/api/song/detail/?id={}&ids=[{}]'.format(
        musicID, musicID)
    s = requests.session()
    r = s.get(action, headers=header)
    r.encoding = 'UTF-8'
    a = json.loads(r.text)
    songinfo = a['songs'][0]
    dlink = songinfo['mp3Url']
    dname = songinfo['name']
    filePath = savePath.format(dname)
    hid = songinfo['hMusic']['dfsId']
    songNet = 'p' + dlink.split('/')[2][1:]
    song_id = str(hid)
    enc_id = encrypted_id(song_id)
    mp3_url = "http://%s/%s/%s.mp3" % (songNet, enc_id, song_id)
    dl = s.get(mp3_url, stream=True, timeout=30)
    if dl.status_code == 200:
        with open(filePath, 'wb') as f:
            for chunk in dl.iter_content(1024):
                f.write(chunk)
    bot.sendAudio(chat_id=update.message.chat_id, audio=open(filePath, 'rb'))


def download163(bot, update):
    logger.info('163 music url {}'.format(update.message.text))
    fid = re163.match(update.message.text).groups()[-1]
    update.message.reply_text('first id is {}'.format(fid))
    getid_then_send_song(bot, update, int(fid))

updater = Updater(token=my_token)
dp = updater.dispatcher
dp.add_handler(RegexHandler(re163, download163))
updater.start_polling()


    
