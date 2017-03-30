
import os
import json
import hashlib
import base64
import binascii

from Crypto.Cipher import AES
from http.cookiejar import LWPCookieJar
import requests

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

modulus = ('00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7'
           'b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280'
           '104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932'
           '575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b'
           '3ece0462db0a22b8e7')
nonce = '0CoJUm6Qyw8W8jud'
pubKey = '010001'

def encrypted_request(text):
    text = json.dumps(text)
    secKey = createSecretKey(16)
    encText = aesEncrypt(aesEncrypt(text, nonce), secKey)
    encSecKey = rsaEncrypt(secKey, pubKey, modulus)
    data = {'params': encText, 'encSecKey': encSecKey}
    return data


def aesEncrypt(text, secKey):
    pad = 16 - len(text) % 16
    text = text + chr(pad) * pad
    encryptor = AES.new(secKey, 2, '0102030405060708')
    ciphertext = encryptor.encrypt(text)
    ciphertext = base64.b64encode(ciphertext).decode('utf-8')
    return ciphertext


def rsaEncrypt(text, pubKey, modulus):
    text = text[::-1]
    rs = pow(int(binascii.hexlify(text), 16),
             int(pubKey, 16), int(modulus, 16))
    return format(rs, 'x').zfill(256)


def createSecretKey(size):
    return binascii.hexlify(os.urandom(size))[:16]



username = 'testtest@163.com‘
password = 'abcdefg'
local_password = hashlib.md5(password.encode('utf-8')).hexdigest()

session = requests.Session()
session.cookies = LWPCookieJar('./cooktest')

url = 'https://music.163.com/weapi/login?csrf_token='
text = {
            'username': username,
            'password': local_password,
            'rememberLogin': 'true'
        }
data = encrypted_request(text)
r = session.post(url, data=data, headers=header) 
session.cookies.save()



session.cookies.load()
csrf = ''
for cookie in session.cookies:
    if cookie.name == '__csrf':
        csrf = cookie.value
    

action = 'http://music.163.com/weapi/song/enhance/player/url?csrf_token='
action += csrf
music_ids = [462686590]
text = {'ids': music_ids, 'br': 320000, 'csrf_token': csrf}
data = encrypted_request(text)
r = session.post(action, data=data, headers=header)
result = json.loads(r.text)
result['data'][0]['url']
