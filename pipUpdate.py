#! /usr/bin/python3
# -*- coding:utf-8 -*-
# pip3 list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1  |
# xargs -n1 pip3 install -U

import subprocess
import json
import pprint
import logzero

logger = logzero.logger

checkCMD = 'pip3 list --outdate --format=json'
updateCMDPlan = 'pip3 install -U {}'

p = subprocess.Popen(checkCMD, stdout=subprocess.PIPE, shell=True)
output, err = p.communicate()
if not err:
    poutput = pprint.pformat(json.loads(output.decode('utf-8')))
    logger.info('new package | \n{}'.format(poutput))
    packageList = [i['name'] for i in json.loads(output.decode('utf-8'))]
    if packageList:
        updateCMD = updateCMDPlan.format(' '.join(packageList))
        p = subprocess.Popen(updateCMD, shell=True)
        output, err = p.communicate()
    else:
        logger.info('all is up to date')
