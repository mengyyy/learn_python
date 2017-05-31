#! /usr/bin/python3
# -*- coding:utf-8 -*-
# 用法bot内 `/kuaidi 单号`

import requests
from requests.compat import urljoin, quote_plus
import telegram
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import Job
import logging


my_chatid = [1234567890]
my_token = '1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ'

code = '440205524883'
com_url = 'https://www.kuaidi100.com/autonumber/autoComNum?text={}'
klog_url = 'https://www.kuaidi100.com/query?type={}&postid={}'
kuaidi_plan = '时间:*{}*\n`{}`'
sent_dict = {}

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger()

# debug
# bot = telegram.Bot(my_token)
# chat_id = my_chatid[0]
# bot.send_message(chat_id=chat_id, text="中文")
# bot.send_message(chat_id=chat_id, text="Hello World")
# bot.send_message(chat_id=chat_id,
#                  text="*bold* _italic_ `fixed width font` [link](http://google.com).",
#                  parse_mode=telegram.ParseMode.MARKDOWN)
# bot.send_message(chat_id=chat_id,
#                  text='<b>bold</b> <i>italic</i> <a href="http://google.com">link</a>.',
#                  parse_mode=telegram.ParseMode.HTML)


def kuaidi(code):
    # comCode 快递商家中文拼音名
    comCode = requests.post(com_url.format(code)).json()['auto'][0]['comCode']
    klog = requests.get(klog_url.format(comCode, code))
    kkl  = [(i['time'],i['context']) for i in klog.json()['data']]
    return kkl


def callback_kuaidi_do(bot, job):
    logger.info('job.context is {}'.format(job.context))
    sent_list = sent_dict[job.context]
    kd_list = kuaidi(job.context)
    # https://stackoverflow.com/questions/3462143/get-difference-between-two-lists
    sent_set = set(sent_list)
    diff_kd_sent = [x for x in kd_list if x not in sent_set]
    for i in diff_kd_sent[::-1]:
        sent_list.append(i)
        bot.send_message(chat_id=chat_id,
                         text=kuaidi_plan.format(*i),
                         parse_mode=telegram.ParseMode.MARKDOWN)
    logger.info('total get {} info have sent {}'.format(
        len(kd_list), len(sent_list)))


def callback_kuaidi(bot, update, job_queue, args):
    logger.info('args is {}'.format(args[0]))
    sent_dict[args[0]] = []
    bot.send_message(chat_id=update.message.chat_id,
                     text='Setting a timer for 1 minute!')
    job_queue.run_repeating(callback_kuaidi_do, 30, 2, context=args[0])
    

updater = Updater(token=my_token)
dp = updater.dispatcher

kuaidi_handler = CommandHandler(
    'kuaidi', callback_kuaidi, pass_args=True, pass_job_queue=True)
dp.add_handler(kuaidi_handler)

updater.start_polling()
