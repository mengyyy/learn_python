#! /usr/bin/python3
# -*- coding:utf-8 -*-
# pip3 list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1  |
# xargs -n1 pip3 install -U

import requests
import re
import threading
import logging
import openpyxl
import time
import concurrent.futures

file_name_replan = re.compile('.*filename=(.*)')
A_stock_replan = re.compile('\n(6\d{5})\t')
THREAD_NUM = 25
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/55.0.2883.87 Safari/537.36',
    'Host': 'query.sse.com.cn',
    'Referer': 'http://www.sse.com.cn/assortment/stock/list/share/',
}

# zcfzb_url = 'http://quotes.money.163.com/service/zcfzb_603789.html'
# lrb_url = 'http://quotes.money.163.com/service/lrb_600001.html'
# xjllb_url = 'http://quotes.money.163.com/service/xjllb_600001.html'
m163_plan = 'http://quotes.money.163.com/service/{zlx}_{num}.html'
SH_list_url = 'http://query.sse.com.cn/security/stock/downloadStockListFile.do?csrcCode=&stockCode=&areaName=&stockType=1'
SZ_list_url = 'http://www.szse.cn/szseWeb/ShowReport.szse?SHOWTYPE=xlsx&CATALOGID=1110&tab1PAGENO=1&ENCODE=1&TABKEY=tab1'

logger = logging.getLogger('163_stock')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s  - %(levelname)s - %(message)s')

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)


def download_from_url(url):
    file_name = ''
    try:
        req = requests.get(url)
        file_name = file_name_replan.search(
            req.headers['Content-Disposition']).group(1)
    except:
        logger.exception('requests error in {}'.format(url))
    else:
        if file_name:
            with open(file_name, 'wb') as f:
                f.write(req.content)
            logger.info('downloaded {}'.format(url))


def download_one(i):
    download_from_url(m163_plan.format(zlx='zcfzb', num=i))
    download_from_url(m163_plan.format(zlx='lrb', num=i))
    download_from_url(m163_plan.format(zlx='xjllb', num=i))


def download_list(ll):
    for i in ll:
        download_one(i)


if __name__ == '__main__':
    if os.path.exists('target_num.txt'):
        with open('target_num.txt', 'r') as f:
            stock_list = f.read().split()
    else:
        # shanghai
        sh_req = requests.get(SH_list_url, headers=headers)
        sh_stock_list = A_stock_replan.findall(sh_req.text)
        logger.info('SH has {} items'.format(len(sh_stock_list)))
        # shenzhen
        sz_req = requests.get(SZ_list_url)
        with open('SZ.xlsx', 'wb') as f:
            f.write(sz_req.content)
        W = openpyxl.load_workbook('SZ.xlsx')
        sz_stock_list = [i.value for i in W.worksheets[0]['A0']][1:]
        logger.info('SZ has {} items'.format(len(sz_stock_list)))
        # zonggong
        stock_list = sh_stock_list + sz_stock_list
        logger.info('Totally {} items'.format(len(stock_list)))
        with open('target_num.txt', 'w') as f:
            _ = [f.write(i + '\r\n') for i in stock_list]
    logging.info('start~~~~')
    start_t = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=THREAD_NUM) as executor:
        _ = [executor.submit(download_one, i) for i in stock_list]
    end_t = time.time()
    logger.info('All subprocesses done in {} S'.format(end_t - start_t))
