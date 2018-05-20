#! /usr/bin/python3
# -*- coding:utf-8 -*-

import subprocess
import json
import logzero

logger = logzero.logger

checkCMD = 'pip3 list --outdate --format=json'
updateCMDPlan = 'pip3 install -U {}'
outputLogPlan = '{name:10s} | {version} --> {latest_version}'

p = subprocess.Popen(checkCMD, stdout=subprocess.PIPE, shell=True)
output, err = p.communicate()
if not err:
    outputData = json.loads(output.decode('utf-8'))
    packageList = []
    for i in outputData:
        logger.info(outputLogPlan.format(**i))
        packageList.append(i['name'])
    for package in packageList :
        updateCMD = updateCMDPlan.format(' '.join(package))
        p = subprocess.Popen(updateCMD, shell=True)
        output, err = p.communicate()
    else:
        logger.info('all is up to date')
