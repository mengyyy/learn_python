#!/bin/bash

apt install firefox fonts-noto-cjk fonts-wqy-zenhei
pip3 install -U logzero selenium
pip3 list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1  | xargs -n1 pip3 install -U
