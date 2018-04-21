#!/usr/bin/env python3
# -*-coding: utf-8 -*-

import urllib.parse
import base64
import logzero
import subprocess
import json
import requests
import time

logger = logzero.setup_logger('get proxy', logfile='/home/Downloads/proxy.log')

socks5Plan = 'socks5://{user}{pass}{server}:{port}'

ssrProxy = 'socks5://127.0.0.1:1080'
ssrProxies = {
    'http': ssrProxy,
    'https': ssrProxy,
}


ssrJsonPath = '/etc/sslocal.json'
ssrLogPath = '/home/Downloads/ss.log'

ssrCMD = 'python ~/shadowsocksr/shadowsocks/local.py -c {} -d restart'.format(ssrJsonPath)

# #!/bin/bash

# pgrep ss-local | xargs kill -9
# nohup ss-local -c /etc/sslocal.json -v &>>/home/Downloads/ss.log &
ssrLibCMD = '/root/sslocal.sh'

testIP_URL = 'http://httpbin.org/ip'


def startSSR_Server():
    p = subprocess.Popen(ssrCMD, stdout=subprocess.PIPE, shell=True)
    time.sleep(3)
    output, err = p.communicate()
    if not err:
        logger.info(output.decode('utf-8'))
        return True
    else:
        logger.waring('ssr server start failed')
        return False


def startSSR_Server_lib():
    p = subprocess.run(ssrLibCMD, shell=True)
    time.sleep(3)
    return True



def testSProxy(proxies):
    try:
        req = requests.get(testIP_URL, proxies=proxies, timeout=10)
        if req.status_code == 200:
            logger.info(req.json())
            return True
    except requests.exceptions.ReadTimeout:
        logger.exception('proxy test failed | timeout | {}'.format(proxies))
        return False
    except:
        logger.exception('proxy test failed | other | {}'.format(proxies))
        return False

def getSocksProxyFromTG(tgSocks5Link):
    proxies = {}
    tgParseResult = urllib.parse.urlparse(tgSocks5Link)
    tgQueryList = urllib.parse.parse_qsl(tgParseResult.query)
    tgSocks5Info = {i[0]: i[1] for i in tgQueryList}
    if tgSocks5Info.get('user', '') == '':
        tgSocks5Info['user'] = ''
        tgSocks5Info['pass'] = ''
    else:
        tgSocks5Info['user'] += ':'
        tgSocks5Info['pass'] += '@'
    socksProxy = socks5Plan.format(**tgSocks5Info)
    proxies['http'] = socksProxy
    proxies['https'] = socksProxy
    if testSProxy(proxies):
        logger.debug('tg proxy success | {}'.format(tgSocks5Link))
        return proxies
    else:
        logger.debug('tg proxy failed | {}'.format(tgSocks5Link))
        return None


def base64Decode(s):
    try:
        b = base64.urlsafe_b64decode(s + '=' * 3).decode('utf-8')
    except UnicodeDecodeError:
        logger.exception('decode failed | {}'.format(s))
        return ''
    return b


def genSSRJsonFromLink(ssrLink):
    ssrParams = {
        "local_address": "127.0.0.1",
        "local_port": 1080,
        "timeout": 300,
        "workers": 1,
    }
    try:
        ssrNetloc = urllib.parse.urlparse(ssrLink).netloc
        ssrInfo_0 = base64.urlsafe_b64decode(
            ssrNetloc + '=' * 3).decode('utf-8').split(':')

        ssrParams['server'] = ssrInfo_0[0]
        ssrParams['server_port'] = ssrInfo_0[1]
        ssrParams['protocol'] = ssrInfo_0[2]
        ssrParams['method'] = ssrInfo_0[3]
        ssrParams['obfs'] = ssrInfo_0[4]

        ssrParseResult = urllib.parse.urlparse(ssrInfo_0[5])
        ssrQueryList = urllib.parse.parse_qs(ssrParseResult.query)
        if ssrQueryList:
            ssrParams['password'] = base64Decode(ssrParseResult.path[:-1])
        else:
            ssrParams['password'] = base64Decode(ssrParseResult.path)
        ssrParams['obfs_param'] = base64Decode(
            ssrQueryList.get('obfsparam', [''])[0])
        ssrParams['protocol_param'] = base64Decode(
            ssrQueryList.get('protoparam', [''])[0])
        with open(ssrJsonPath, 'w') as f:
            json.dump(ssrParams, f, indent=4, sort_keys=True)
    except:
        logger.exception('generate ssr config json form ssr link failed | {}'.format(ssrLink))
        return False
    else:
        return True



def getSocksProxyFromSSRLink(ssrLink):
    if genSSRJsonFromLink(ssrLink):
        # if startSSR_Server():
        if startSSR_Server_lib():
            if testSProxy(ssrProxies):
                logger.debug('ssr proxy success | {}'.format(ssrLink))
                return ssrProxies
    else:
        logger.debug('ssr proxy failed | {}'.format(ssrLink))
        return None

