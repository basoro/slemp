# coding:utf-8

import sys
import io
import os
import time
import re
import string
import subprocess

sys.path.append(os.getcwd() + "/class/core")
import slemp

def getPluginName():
    return 'wagw'

def getServerDir():
    return slemp.getServerDir() + '/' + getPluginName()

def status():
    data = slemp.execShell("ps -ef | grep /home/slemp/server/wagw/app.js | grep -v grep | grep -v python | awk '{print $2}'")
    if data[0] == '':
        return 'stop'
    return 'start'

def start():
    slemp.execShell('cd /home/slemp/server/wagw && source /root/.nvm/nvm.sh && pm2 start app.js --name WAGW > /dev/null 2>&1 &')
    return 'ok'

def stop():
    data = slemp.execShell("ps -ef | grep /home/slemp/server/wagw/app.js | grep -v grep | grep -v python | awk '{print $2}'")
    if data[0] != '':
        # slemp.execShell("kill -9 " + data[0])
        slemp.execShell('cd /home/slemp/server/wagw && source /root/.nvm/nvm.sh && pm2 stop WAGW > /dev/null 2>&1 &')
        return 'ok'
    return 'fail'

def restart():
    stop()
    start()
    return 'ok'

def reload():
    stop()
    start()
    return 'ok'

def getConf():
    path = getServerDir() + "/port.pl"
    return path

if __name__ == "__main__":
    func = sys.argv[1]
    if func == 'status':
        print(status())
    elif func == 'start':
        print(start())
    elif func == 'stop':
        print(stop())
    elif func == 'restart':
        print(restart())
    elif func == 'reload':
        print(reload())
    elif func == 'conf':
        print(getConf())
    else:
        print('error')
