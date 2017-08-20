#! /usr/bin/python3
# -*- coding:utf-8 -*-
# 用法bot内 `/kd 单号1 单号2 ... 单号n`

import telegram
from telegram.ext import Updater
from telegram.ext import MessageHandler, Filters
from telegram.ext import CommandHandler
import requests
import logging
import pprint
import time
import bs4

my_token = '123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_file_enable = False

if log_file_enable:
    log_path = './{}.log'.format(__name__)
    fh = logging.FileHandler(log_path)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)

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

class Kuaidi100:
    """docstring for Kuaidi100"""
    
    def __init__(self, code):
        self.code = str(code)
        self.com_url = 'https://www.kuaidi100.com'\
                       '/autonumber/autoComNum?text=' + self.code
        self.klog_url_plan = 'https://www.kuaidi100.com/'\
                             'query?type={}&postid=' + self.code
        self.klog_data_plan = '{ftime} | {location} | {context}'
        self.klog_data_init()
        self.com_code_dict = self.get_kuadi_com_dict()
        try:
            self.__com_code = requests.post(
                self.com_url).json()['auto'][0]['comCode']
        except Exception as e:
            logger.error('get code company error\n'.format(repr(e)))
            self.__com_code = 'error'
        else:
            self.klog_url = self.klog_url_plan.format(self.__com_code)
            logger.debug(
                'code {} company is {}'.format(self.code, self.__com_code))
    def get_com_code(self):
        return self.__com_code
    
    def set_com_code(self, comCode):
        self.__com_code = str(comCode)
        self.klog_url = self.klog_url_plan.format(self.__com_code)
        self.klog_data_init()
        self.get_kuaidi_log()
        
    com_code = property(get_com_code, set_com_code)
    
    def klog_data_init(self):
        self.klog_data_old = []
        self.overdue = False 
        
    def get_kuaidi_log(self):
        try:
            req = requests.get(self.klog_url)
            self.klog = req.json()
            self.message = self.klog['message']
        except Exception as e:
            logger.error('get kuaidi log error\n{}'.format(repr(e)))
        else:
            if self.message == 'ok':
                self.klog_data_new = [self.klog_data_plan.format(
                    **i) for i in self.klog['data']]
                self.klog_data_gen = [
                    i for i in self.klog_data_new if i not in self.klog_data_old]
                self.klog_data_old = set(self.klog_data_new)
                cd = datetime.datetime.now() - datetime.datetime.strptime(
                    self.klog['data'][0]['ftime'], '%Y-%m-%d %H:%M:%S')
                if cd.days >= 30:
                    self.overdue = True                
                if self.klog_data_gen:
                    logger.debug('reflash {}'.format(self.klog_data_gen))
                else:
                    logger.debug('klog {}'.format(pprint.pformat(self.klog)))
            else:
                logger.error('get wrong data {}'.format(self.klog))
        return self.klog_data_gen, self.klog, self.overdue
    
    def get_kuadi_com_dict(self):
        try:
            req = requests.get('https://www.kuaidi100.com')
            bso = bs4.BeautifulSoup(req.content, 'html.parser')
            com_item = bso.findAll('a', {'data-code': True})
            iterable = [(i.attrs['data-code'], i.text) for i in com_item]
            com_code_dict = {key: value for (key, value) in iterable}
        except Exception as e:
            logger.error('get com_code list failed {}'.format(repr(e)))
        return com_code_dict
    

def kuadi_job(bot, job):
    chat_id = job.context[0]
    ksend, klog, overdue = job.context[1].get_kuaidi_log()
    logger.debug('kuaidi job send {}'.format(ksend))
    for i in ksend[::-1]:
        bot.send_message(chat_id=chat_id, text=i)
    if klog['ischeck'] == '1' or overdue:
        job.schedule_removal()
        logger.debug('kuadi job {} over'.format(klog['nu']))
        if overdue:
            bot.send_message(chat_id=chat_id, text='{} overdue'.format(klog['nu']))
        if klog['ischeck'] == '1':
            bot.send_message(chat_id=chat_id, text='{} checked'.format(klog['nu']))
        


def kuaidi_do(bot, update, args, job_queue):
    logger.debug('kaudi do args {} len {}'.format(args, len(args)))
    chat_id = update.message.chat_id
    if len(args) == 0:
        update.message.reply_text('please use /kd code')
    else:
        for i in args:
            cc = Kuaidi100(i)
            if cc.com_code != 'error':
                job_context = (chat_id, cc)
                job = job_queue.run_repeating(
                    kuadi_job, 60, 2,
                    context=job_context)
            else:
                update.message.reply_text('get kuadi company code error')


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"' % (update, error))
    

if __name__ == '__main__':
    updater = Updater(token=my_token)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('kd', kuaidi_do,
                                  pass_args=True,
                                  pass_job_queue=True))
    dp.add_error_handler(error)
    updater.start_polling()
