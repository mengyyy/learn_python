#! /usr/bin/python3
# -*- coding:utf-8 -*-

import telegram
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram.ext import RegexHandler
import logging
import cfscrape  # apt-get install nodejs pip3 install cfscrape pycrypto
import bs4
import re
import os
import json
import pprint

my_chatid = [1234567890]
my_token = '1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ'
ARIA2_TOKEN = 'aria_token'

re_dmhy = re.compile('http://share\.dmhy\.org/topics/view/.*html')
re_magnet = re.compile('magnet:\?.*')

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




def get_torrent_link(url):
    req = requests_flare.get(url)
    bsObj = bs4.BeautifulSoup(req.text, 'html.parser')
    taga = bsObj.find('a', href=re.compile('.*\.torrent'))
    link = 'http:' + taga['href']
    logger.info('torrent link is  {}'.format(link))
    return link


def add_mission_2aria2(link):
    '''
    Only add one link one time
    According :
    https://aria2.github.io/manual/en/html/aria2c.html?highlight=token#methods
    '''
    jsonreq = json.dumps({'jsonrpc': '2.0', 'id': '1',
                          'method': 'aria2.addUri',
                          'params': ["token:{}".format(ARIA2_TOKEN), [link]]})
    c = requests_flare.post('http://localhost:6800/jsonrpc', data=jsonreq)
    return c

# share dmhy org
def dmhy_deal(bot, update):
    logger.info('share_dmhy url {}'.format(update.message.text))
    url = update.message.text
    link = get_torrent_link(url)
    c = add_mission_2aria2(link)
    gid = c.json()['result']
    update.message.reply_text('gid is {}'.format(gid))
    return gid


def magnet_deal(bot, update):
    logger.info('magnet link {}'.format(update.message.text))
    magnet_link = update.message.text
    c = add_mission_2aria2(magnet_link)
    gid = c.json()['result']
    update.message.reply_text('gid is {}'.format(gid))
    return gid


def deal_json(d):
    if 'error' in d.keys():
        error_msg = d['error']['message']
        return error_msg
    if 'result' in d.keys():
        result = d['result'][0]
        completedLength = int(result['completedLength']) / 1024 / 1024
        status = result['status']
        totalLength = int(result['totalLength']) / 1024 / 1024
        file_path = [x['path'] for x in result['files']]
        return 'status {} comple {}M  total {}M done{}%\n file path {}'.format(
            status,
            completedLength,
            totalLength,
            completedLength / totalLength * 100,
            file_path)


def tell_active(bot, update):
    logger.info('tell active miassion')
    bot.sendChatAction(chat_id=update.message.chat_id,
                       action=telegram.ChatAction.TYPING)
    jsonreq = json.dumps({'jsonrpc': '2.0', 'id': '1',
                          'method': 'aria2.tellActive',
                          'params': ["token:{}".format(ARIA2_TOKEN)]})
    d = requests_flare.post('http://localhost:6800/jsonrpc', data=jsonreq)
    e = deal_json(d.json())
    bot.sendMessage(chat_id=update.message.chat_id,
                    text=e)


def tell_stoped(bot, update):
    logger.info('tell stoped mission')
    bot.sendChatAction(chat_id=update.message.chat_id,
                       action=telegram.ChatAction.TYPING)
    jsonreq = json.dumps({'jsonrpc': '2.0', 'id': '1',
                          'method': 'aria2.tellStopped',
                          'params': ["token:{}".format(ARIA2_TOKEN), 0, 3, ['gid',
                                                                            'dir',
                                                                            'totalLength',
                                                                            'completedLength',
                                                                            'status']]})
    d = requests_flare.post('http://localhost:6800/jsonrpc', data=jsonreq)
    pprint.pprint(d.json())
    e = pprint.pformat(d.json())
    bot.sendMessage(chat_id=update.message.chat_id,
                    text=e)

requests_flare = cfscrape.create_scraper()
updater = Updater(token=my_token)
dp = updater.dispatcher
dp.add_handler(RegexHandler(re_dmhy, dmhy_deal))
dp.add_handler(RegexHandler(re_magnet, magnet_deal))
dp.add_handler(CommandHandler('tell_active', tell_active))
dp.add_handler(CommandHandler('tell_stoped', tell_stoped))
updater.start_polling()
