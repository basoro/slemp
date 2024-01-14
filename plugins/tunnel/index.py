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
    return 'tunnel'

def getServerDir():
    return slemp.getServerDir() + '/' + getPluginName()

def status():
    data = slemp.execShell("ps -ef | grep metro.basoro.id | grep -v grep | grep -v python | awk '{print $2}'")
    if data[0] == '':
        return 'stop'
    return 'start'

def start():
    serverdir = getServerDir()
    key = slemp.readFile(getServerDir() + "/key.pl")
    slemp.execShell(serverdir + '/client -s metro.basoro.id -p 4900 -k ' + key + ' > /dev/null 2>&1 &')
    return 'ok'

def stop():
    data = slemp.execShell("ps -ef | grep metro.basoro.id | grep -v grep | grep -v python | awk '{print $2}'")
    if data[0] != '':
        slemp.execShell("kill -9 " + data[0])
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
    path = getServerDir() + "/key.pl"
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
