#!/usr/bin/env python3
# -*-coding: utf-8 -*-
# pip3 list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1  |
# xargs -n1 pip3 install -U

import requests
import bs4
import re
import time
import requests
import logzero
from threading import Thread
import random
import os
import cfscrape


threadNum = 4
targetNum = 1

logger = logzero.setup_logger(name='guo',
                              logfile='/home/Downloads/guosocksdownload.log',
                              maxBytes=2e6,
                              backupCount=100)

# proxies = {
#     'http': 'socks5://user:passwd@server:port',
#     'https': 'socks5://user:passwd@server:port'
# }
proxies = None


startUrl = 'https://www.guo.media/'
loginUrl = 'https://www.guo.media/includes/ajax/core/signin.php'
loadUrl = 'https://www.guo.media/includes/ajax/data/load.php'

loginData = {
    'username_email':'username',
    'password':'password'
}

loadData = {
    'get':'newsfeed',
    'filter':'all',
    'offset':'1'
}

startHeaders = {
    'referer':'https://www.guo.media/',
    'upgrade-insecure-requests':'1',
    'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
}


loginHeaders = {
    'accept':'application/json, text/javascript, */*; q=0.01',
    'accept-encoding':'gzip, deflate, br',
    'accept-language':'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,en-GB;q=0.6',
    'content-length':'48',
    'authority':'www.guo.media',
    'origin':'https://www.guo.media',
    'referer':'https://www.guo.media/',
    'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
    'x-requested-with':'XMLHttpRequest',
}

downloadsHeaders = {
    'upgrade-insecure-requests':'1',
    'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
}



def findDownloadTarget():
    # session = requests.Session()
    session = cfscrape.create_scraper(delay=10)
    session.get(startUrl)
    startReq = session.get(startUrl, headers=startHeaders, proxies=proxies)
    loginReq = session.post(loginUrl, headers=loginHeaders, data=loginData, proxies=proxies)
    logger.info('session cookies:\n{}'.format(session.cookies.items()))
    startReq = session.get(startUrl, headers=startHeaders, proxies=proxies)
    soup= bs4.BeautifulSoup(startReq.content, 'lxml')
    srcList = []
    for i in soup.findAll('source'):
            if i.attrs['src'] not in srcList:
                logger.info('find | {}'.format(i.attrs['src']))
                srcList.append(i.attrs['src'])
    for i in range(50):
        loadData['offset'] = str(i)
        loadReq = session.post(loadUrl, headers=loginHeaders, data=loadData)
        try:
            soup= bs4.BeautifulSoup(loadReq.json()['data'], 'lxml')
        except:
            logger.exception('failed get loadReq | {}'.format(i))
            logger.error(loadReq.text)
            continue
        for j in soup.findAll('source'):
            if j.attrs['src'] not in srcList:
                logger.info('find | {} | {}'.format(i, j.attrs['src']))
                srcList.append(j.attrs['src'])
    with open('/home/Downloads/guo.txt', 'w') as f:
        _ = [f.write(k + '\r\n') for k in srcList]
    return srcList



def download_file(url):
    downloadLength = 0
    local_filename = os.devnull
    # NOTE the stream=True parameter
    r = requests.get(url, headers=downloadsHeaders, stream=True, proxies=proxies)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024*8):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                downloadLength += len(chunk)
    return  downloadLength


def downloadMission(urlList, num):
    for _ in range(num):
        random.shuffle(urlList)
        for url in urlList:
            logger.info('start download | url | {} '.format(url))
            startTime = time.time()
            downloadLength = download_file(url)
            costTime = time.time() - startTime
            logger.info('finish download | length | {} | time | {} | num | {}'.format(downloadLength, costTime, num))



targetList = findDownloadTarget()
while True:
    try:
        downloadMission(targetList, targetNum)
        time.sleep(10)
    except KeyboardInterrupt:
        logger.info('KeyboardInterrupt | {}'.format(targetList))
        break
    except:
        logger.exception('download failed | {}'.format(targetList))
    else:
        if targetList:
            logger.info('download finish | {}'.format(targetList))
        else:
            logger.info('retry get download target')
            try:
                targetList = findDownloadTarget()
            except:
                logger.exception('find download target filed')

