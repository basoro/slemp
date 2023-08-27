# coding:utf-8

import sys
import io
import os
import time

sys.path.append(os.getcwd() + "/class/core")
import slemp

app_debug = False
if slemp.isAppleSystem():
    app_debug = True


def getPluginName():
    return 'swap'


def getPluginDir():
    return slemp.getPluginDir() + '/' + getPluginName()


def getServerDir():
    return slemp.getServerDir() + '/' + getPluginName()


def getInitDFile():
    if app_debug:
        return '/tmp/' + getPluginName()
    return '/etc/init.d/' + getPluginName()


def getInitDTpl():
    path = getPluginDir() + "/init.d/" + getPluginName() + ".tpl"
    return path


def getArgs():
    args = sys.argv[2:]
    tmp = {}
    args_len = len(args)

    if args_len == 1:
        t = args[0].strip('{').strip('}')
        t = t.split(':')
        tmp[t[0]] = t[1]
    elif args_len > 1:
        for i in range(len(args)):
            t = args[i].split(':')
            tmp[t[0]] = t[1]

    return tmp


def checkArgs(data, ck=[]):
    for i in range(len(ck)):
        if not ck[i] in data:
            return (False, slemp.returnJson(False, 'Parameter: (' + ck[i] + ') none!'))
    return (True, slemp.returnJson(True, 'ok'))


def status():
    data = slemp.execShell("free -m|grep Swap|awk '{print $2}'")
    if data[0].strip() == '0':
        return 'stop'
    return 'start'

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
        content = content.replace(
            '{$SERVER_PATH}', getServerDir() + '/swapfile')
        slemp.writeFile(file_bin, content)
        slemp.execShell('chmod +x ' + file_bin)

    # systemd
    systemDir = slemp.systemdCfgDir()
    systemService = systemDir + '/swap.service'
    systemServiceTpl = getPluginDir() + '/init.d/swap.service.tpl'
    if os.path.exists(systemDir) and not os.path.exists(systemService):
        swapon_bin = slemp.execShell('which swapon')[0].strip()
        swapoff_bin = slemp.execShell('which swapoff')[0].strip()
        service_path = slemp.getServerDir()
        se_content = slemp.readFile(systemServiceTpl)
        se_content = se_content.replace('{$SERVER_PATH}', service_path)
        se_content = se_content.replace('{$SWAPON_BIN}', swapon_bin)
        se_content = se_content.replace('{$SWAPOFF_BIN}', swapoff_bin)
        slemp.writeFile(systemService, se_content)
        slemp.execShell('systemctl daemon-reload')

    return file_bin


def swapOp(method):
    file = initDreplace()

    if not slemp.isAppleSystem():
        data = slemp.execShell('systemctl ' + method + ' swap')
        if data[1] == '':
            return 'ok'
        return 'fail'

    data = slemp.execShell(file + ' ' + method)
    if data[1] == '':
        return 'ok'
    return 'fail'


def start():
    return swapOp('start')


def stop():
    return swapOp('stop')


def restart():
    return swapOp('restart')


def reload():
    return 'ok'


def initdStatus():
    if slemp.isAppleSystem():
        return "Apple Computer does not support"

    shell_cmd = 'systemctl status swap | grep loaded | grep "enabled;"'
    data = slemp.execShell(shell_cmd)
    if data[0] == '':
        return 'fail'
    return 'ok'


def initdInstall():
    if slemp.isAppleSystem():
        return "Apple Computer does not support"

    slemp.execShell('systemctl enable swap')
    return 'ok'


def initdUinstall():
    if slemp.isAppleSystem():
        return "Apple Computer does not support"

    slemp.execShell('systemctl disable swap')
    return 'ok'


def swapStatus():
    sfile = getServerDir() + '/swapfile'

    if os.path.exists(sfile):
        size = os.path.getsize(sfile) / 1024 / 1024
    else:
        size = '218'
    data = {'size': size}
    return slemp.returnJson(True, "ok", data)


def changeSwap():
    args = getArgs()
    data = checkArgs(args, ['size'])
    if not data[0]:
        return data[1]

    size = args['size']
    swapOp('stop')

    gsdir = getServerDir()

    cmd = 'dd if=/dev/zero of=' + gsdir + '/swapfile bs=1M count=' + size
    cmd += ' && mkswap ' + gsdir + '/swapfile && chmod 600 ' + gsdir + '/swapfile'
    msg = slemp.execShell(cmd)
    swapOp('start')

    return slemp.returnJson(True, "Successfully modified:\n" + msg[0])

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
    elif func == "swap_status":
        print(swapStatus())
    elif func == "change_swap":
        print(changeSwap())
    else:
        print('error')
