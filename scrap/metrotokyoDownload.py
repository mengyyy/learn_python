#!/usr/bin/env python3
# -*-coding: utf-8 -*-
# pip3 list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1  |
# xargs -n1 pip3 install -U

import requests
import bs4
import logzero

logger = logzero.setup_logger('tokyo download')
url = 'http://www.metro.tokyo.jp/CHINESE/GUIDE/BOSAI/index.htm'

req = requests.get(url)
soup = bs4.BeautifulSoup(req.content, 'lxml')
adata = soup.findAll('a', class_='linkPdf01')

headers = {
    'Cache-Control':'no-cache',
    'Connection':'keep-alive',
    'Host':'www.bousai.metro.tokyo.jp',
    'Pragma':'no-cache',
    'Referer':'http://www.metro.tokyo.jp/CHINESE/GUIDE/BOSAI/index.htm',
    'Upgrade-Insecure-Requests':'1',
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
}


for i in adata:
    url = i.attrs['href'].replace('\n', '')
    filename = i.text + '-' + url.split('/')[-1]
    logger.info('{} | {}'.format(url, filename))
    req = requests.get(url, headers=headers)
    logger.info('{} | {}'.format(req.status_code, len(req.content)))
    with open(filename, 'wb') as f:
        f.write(req.content)


