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

def getPluginDir():
    return slemp.getPluginDir() + '/' + getPluginName()

def getServerDir():
    return slemp.getServerDir() + '/' + getPluginName()

def initdStatus():
    if slemp.isAppleSystem():
        return "Apple Computer does not support"

    shell_cmd = 'systemctl status tunnel | grep loaded | grep "enabled;"'
    data = slemp.execShell(shell_cmd)
    if data[0] == '':
        return 'fail'
    return 'ok'


def initdInstall():
    if slemp.isAppleSystem():
        return "Apple Computer does not support"

    slemp.execShell('systemctl enable tunnel')
    return 'ok'


def initdUinstall():
    if slemp.isAppleSystem():
        return "Apple Computer does not support"

    slemp.execShell('systemctl disable tunnel')
    return 'ok'

def status():
    data = slemp.execShell("ps -ef | grep metro.basoro.id | grep -v grep | grep -v python | awk '{print $2}'")
    if data[0].strip() == '':
        return 'stop'
    return 'start'

# def status():
#     data = slemp.execShell("ps -ef | grep metro.basoro.id | grep -v grep | grep -v python | awk '{print $2}'")
#     if data[0] == '':
#         return 'stop'
#     return 'start'

def getInitDTpl():
    path = getPluginDir() + "/init.d/" + getPluginName() + ".tpl"
    return path


def initDreplace():

    file_tpl = getInitDTpl()
    service_path = os.path.dirname(os.getcwd())

    initD_path = getServerDir() + '/init.d'
    if not os.path.exists(initD_path):
        os.mkdir(initD_path)
    file_bin = initD_path + '/' + getPluginName()

    # initd replace
    if not os.path.exists(file_bin):
        content = slemp.readFile(file_tpl)
        slemp.writeFile(file_bin, content)
        slemp.execShell('chmod +x ' + file_bin)

    # systemd
    systemDir = slemp.systemdCfgDir()
    systemService = systemDir + '/tunnel.service'
    systemServiceTpl = getPluginDir() + '/init.d/tunnel.service.tpl'
    if os.path.exists(systemDir) and not os.path.exists(systemService):
        service_path = slemp.getServerDir()
        se_content = slemp.readFile(systemServiceTpl)
        se_content = se_content.replace('{$SERVER_PATH}', service_path)
        slemp.writeFile(systemService, se_content)
        slemp.execShell('systemctl daemon-reload')

    return file_bin


def tunnelOp(method):
    file = initDreplace()

    if not slemp.isAppleSystem():
        data = slemp.execShell('systemctl ' + method + ' tunnel')
        if data[1] == '':
            return 'ok'
        return 'fail'

    data = slemp.execShell(file + ' ' + method)
    if data[1] == '':
        return 'ok'
    return 'fail'

def start():
    # serverdir = getServerDir()
    # key = slemp.readFile(getServerDir() + "/key.pl")
    # slemp.execShell(serverdir + '/client -s metro.basoro.id -p 4900 -k ' + key + ' > /dev/null 2>&1 &')
    # return 'ok'
    return tunnelOp('start')

def stop():
    # data = slemp.execShell("ps -ef | grep metro.basoro.id | grep -v grep | grep -v python | awk '{print $2}'")
    # if data[0] != '':
    #     slemp.execShell("kill -9 " + data[0])
    #     return 'ok'
    # return 'fail'
    return tunnelOp('stop')

def restart():
    # stop()
    # start()
    # return 'ok'
    return tunnelOp('restart')

def reload():
    # stop()
    # start()
    # return 'ok'
    return tunnelOp('reload')

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
    elif func == 'initd_status':
        print(initdStatus())
    elif func == 'initd_install':
        print(initdInstall())
    elif func == 'initd_uninstall':
        print(initdUinstall())
    elif func == 'conf':
        print(getConf())
    else:
        print('error')
