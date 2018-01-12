#!/bin/bash

ps ax | grep jd_checkin.py | grep -v  grep | cut -c 1-6 | xargs kill -9
wget --no-cache -O jd_checkin.py https://raw.githubusercontent.com/mengyyy/learn_python/master/jd_checkin.py
nohup python3 jd_checkin.py &>/dev/null &
echo you should sent /jdc to your bot
