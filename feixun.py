#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import requests
import base64
import json

loginUrl = 'http://192.168.2.1/cgi-bin/'
data = {
    "method":"set",
    "module":
    {
        "security":
        {
            "login":
            {
                "username":"admin",
                "password":"YWRtaW4="
            }
        }
    },
    "_deviceType":"pc"
}
headers = {
    'Content-Type':'application/json',
    'Host':'192.168.2.1',
    'Origin':'http://192.168.2.1',
    'Referer':'http://192.168.2.1/cgi-bin',
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'
}
session = requests.Session()
username = ['root','admin']
password = ['123456', 'root', 'admin', 'rootroot']

for u in username:
    for p in password:
        data['module']['security']['login']['username'] = u
        data['module']['security']['login']['password'] = base64.b64encode(p.encode('utf-8')).decode('utf-8')
        req = session.post(loginUrl, data=json.dumps(data), headers=headers)
        print(u, p, req.json(), sep=' | ')
