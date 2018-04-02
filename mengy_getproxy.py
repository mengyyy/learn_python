#!/usr/bin/env python3
# -*-coding: utf-8 -*-

import urllib.parse
import base64
import logzero
import subprocess
import json
import requests

logger = logzero.setup_logger('get proxy')

socks5Plan = 'socks5://{user}:{pass}@{server}:{port}'

ssrProxy = 'socks5://127.0.0.1:1080'
ssrProxies = {
    'http': ssrProxy,
    'https': ssrProxy,
}


ssrJsonPath = '/etc/sslocal.json'
ssrCMD = 'python ~/shadowsocksr/shadowsocks/local.py -c {} -d restart'.format(
    ssrJsonPath)
testIP_URL = 'http://httpbin.org/ip'


def startSSR_Server():
    p = subprocess.Popen(ssrCMD, stdout=subprocess.PIPE, shell=True)
    output, err = p.communicate()
    if not err:
        logger.info(output.decode('utf-8'))
        return True
    else:
        logger.waring('ssr server start failed')
        return False


def testSProxy(proxies):
    try:
        req = requests.get(testIP_URL, proxies=proxies, timeout=10)
        if req.status_code == 200:
            logger.info(req.json())
            return True
    except requests.exceptions.ReadTimeout:
        logger.exception('ssr server failed | timeout')
        return False
    except:
        logger.exception('ssr server failed | timeout')
        return False

def getSocksProxyFromTG(tgSocks5Link):
    proxies = {}
    tgParseResult = urllib.parse.urlparse(tgSocks5Link)
    tgQueryList = urllib.parse.parse_qsl(tgParseResult.query)
    tgSocks5Info = {i[0]: i[1] for i in tgQueryList}
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

        ssrParams['password'] = base64Decode(ssrParseResult.path[:-1])
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
        if startSSR_Server():
            if testSProxy(ssrProxies):
                logger.debug('tg proxy success | {}'.format(ssrLink))
                return ssrProxies
    else:
        logger.debug('tg proxy failed | {}'.format(ssrLink))
        return None



# tgSocks5Link = 'tg://socks?server=127.0.0.1&port=1080&user=user&pass=passwd'
# Proxies = getSocksProxyFromTG(tgSocks5Link)

# ssrLink = 'ssr://MTI3LjAuMC4xOjQ0MzphdXRoX2FlczEyOF9tZDU6YWVzLTEyOC1jZmI6dGxzMS4yX3RpY2tldF9hdXRoOmNHRnpjM2R2Y21RLz9vYmZzcGFyYW09YjJKbWMxOXdZWEpoYlEmcHJvdG9wYXJhbT1jSEp2ZEc5amIyeGZjR0Z5WVcwJnJlbWFya3M9Y21WdFlYSnJjdyZncm91cD1aM0p2ZFhB'
# Proxies = getSocksProxyFromSSRLink(ssrLink)

