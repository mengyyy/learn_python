#! /usr/bin/env python3
# -*- coding:utf-8 -*-
# pip3 list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1  |
# xargs -n1 pip3 install -U

from telethon import TelegramClient
from telethon.tl.types import PeerUser, PeerChat, PeerChannel
import time

api_id = 12345
api_hash = '1234567890abcdefghijklmnopqrstuv'

client = TelegramClient('mengytgclient', api_id, api_hash, proxy=None)
client.start()

print(client.get_me().stringify())

clipBoardChat = client.get_entity(PeerUser('username'))
client.send_message(clipBoardChat, message='test client')

tg = 'https://t.me/testgroup'
tc = 'https://t.me/testchannel'
tc_plan = 'from | {from_id}\nmessage | {message}'

idNum = 0
while True:
    for i in client.iter_messages(tg, limit=None, min_id=idNum):
        idNum += 1
        print('get message id | {} | total | {}'.format(i.to_dict()['id'], idNum))
        if i.to_dict().get('message', None):
            client.send_message(tc, tc_plan.format(**i.to_dict()))
    time.sleep(1)
