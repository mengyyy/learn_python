#!/bin/env/python

import json
import hashlib
import base64
import binascii
from Crypto.Cipher import AES
import requests

def encrypted_id(id):
    magic = bytearray('3go8&$8*3*3h0k(2)2', 'u8')
    song_id = bytearray(id, 'u8')
    magic_len = len(magic)
    for i, sid in enumerate(song_id):
        song_id[i] = sid ^ magic[i % magic_len]
    m = hashlib.md5(song_id)
    result = m.digest()
    result = base64.urlsafe_b64encode(result)
    return result.decode('utf-8')
    
    
savePath = '/home/Downloads/{}.mp3'
music_id = 462686590
action = 'http://music.163.com/api/song/detail/?id={}&ids=[{}]'.format(
        music_id, music_id)
s = requests.session()
r = s.get(action)
r.encoding = 'UTF-8'
a = json.loads(r.text)
#提取信息 
songinfo = a['songs'][0]
dlink = songinfo['mp3Url']
dname = songinfo['name']
filePath = savePath.format(dname)
#构造下载链接
hid = songinfo['hMusic']['dfsId']
songNet = 'p' + dlink.split('/')[2][1:]
song_id = str(hid)
enc_id = encrypted_id(song_id)
mp3_url = "http://%s/%s/%s.mp3" % (songNet, enc_id, song_id)
#执行下载
dl = s.get(mp3_url, stream=True, timeout=30)
if dl.status_code == 200:
        with open(filePath,'wb') as f:
            for chunk in dl.iter_content(1024):
                f.write(chunk)
