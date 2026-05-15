# coding:utf-8

import sys
import io
import os
import time
import shutil

sys.path.append(os.getcwd() + "/class/core")
import slemp

app_debug = False
if slemp.isAppleSystem():
    app_debug = True


def getPluginName():
    return 'pm2'


def getPluginDir():
    return slemp.getPluginDir() + '/' + getPluginName()


def getServerDir():
    return slemp.getServerDir() + '/' + getPluginName()


def getInitDFile():
    if app_debug:
        return '/tmp/' + getPluginName()
    return '/etc/init.d/' + getPluginName()


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
            return (False, slemp.returnJson(False, 'Parameters: (' + ck[i] + ') no!'))
    return (True, slemp.returnJson(True, 'ok'))


def status():
    cmd = "ps -ef|grep pm2 |grep -v grep | grep -v python | awk '{print $2}'"
    data = slemp.execShell(cmd)
    if data[0] == '':
        return 'stop'
    return 'start'


def rootDir():
    path = '/root'
    if slemp.isAppleSystem():
        user = slemp.execShell(
            "who | sed -n '2, 1p' |awk '{print $1}'")[0].strip()
        path = '/Users/' + user
    return path


def pm2NVMDir():
    path = rootDir() + '/.nvm'
    return path

__SR = '''#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
export HOME=%s
source %s/nvm.sh && ''' % (rootDir(), pm2NVMDir())
__path = getServerDir() + '/list'


def pm2LogDir():
    path = rootDir() + '/.pm2'
    return path


def pm2Log():
    path = pm2LogDir() + '/pm2.log'
    return path

def __pm2GetList():
    return pm2GetList()

def pm2GetList():
    try:
        import json
        tmp = slemp.execShell(__SR + "pm2 jlist")
        try:
            data = json.loads(tmp[0])
        except:
            return []
            
        result = []
        tmp_lsof = slemp.execShell('lsof -c node -P|grep LISTEN')
        plist = tmp_lsof[0].split('\n')
        
        for app in data:
            appInfo = {}
            appInfo['name'] = app.get('name', 'N/A')
            appInfo['id'] = str(app.get('pm_id', '0'))
            
            pm2_env = app.get('pm2_env', {})
            monit = app.get('monit', {})
            
            appInfo['mode'] = pm2_env.get('exec_mode', 'N/A')
            appInfo['pid'] = str(app.get('pid', '0'))
            appInfo['status'] = pm2_env.get('status', 'stopped')
            appInfo['restart'] = str(pm2_env.get('restart_time', '0'))
            
            # Format uptime
            uptime = pm2_env.get('pm_uptime', 0)
            if uptime > 0:
                diff = int(time.time() * 1000) - uptime
                if diff > 0:
                    appInfo['uptime'] = slemp.toSize(diff / 1000) # This is a bit hacky, let's just use seconds or similar
                else:
                    appInfo['uptime'] = '0s'
            else:
                appInfo['uptime'] = '0s'
            
            appInfo['cpu'] = str(monit.get('cpu', '0')) + '%'
            appInfo['mem'] = slemp.toSize(monit.get('memory', 0))
            appInfo['user'] = pm2_env.get('username', 'N/A')
            appInfo['watching'] = 'enabled' if pm2_env.get('watch', False) else 'disabled'
            appInfo['port'] = 'OFF'
            appInfo['path'] = 'OFF'
            
            for p in plist:
                ptmp = p.split()
                if len(ptmp) < 8:
                    continue
                if ptmp[1] == appInfo['pid']:
                    # Extract port from lsof output
                    addr = ptmp[8]
                    if ':' in addr:
                        appInfo['port'] = addr.split(':')[-1]
            
            if os.path.exists(__path + '/' + appInfo['name']):
                appInfo['path'] = slemp.readFile(__path + '/' + appInfo['name'])
            
            result.append(appInfo)
        return result
    except Exception as e:
        return []


def pm2List():
    result = pm2GetList()
    return slemp.returnJson(True, 'ok', result)


def pm2Add():
    args = getArgs()
    data = checkArgs(args, ['path', 'run', 'pname'])
    if not data[0]:
        return data[1]

    path = args['path']
    run = args['run']
    pname = args['pname']

    runFile = (path + '/' + run).replace('//', '/')
    if not os.path.exists(runFile):
        return slemp.returnJson(False, 'The specified file does not exist!')

    nlist = pm2GetList()
    for node in nlist:
        if pname == node['name']:
            return slemp.returnJson(False, 'The specified project name already exists!')
    if os.path.exists(path + '/package.json') and not os.path.exists(path + '/package-lock.json'):
        slemp.execShell(__SR + "cd " + path + ' && npm install -s')
    slemp.execShell(__SR + 'cd ' + path + ' && pm2 start ' +
                 runFile + ' --name "' + pname + '"|grep ' + pname)
    slemp.execShell(__SR + 'pm2 save && pm2 startup')
    if not os.path.exists(__path):
        slemp.execShell('mkdir -p ' + __path)
    slemp.writeFile(__path + '/' + pname, path)
    return slemp.returnJson(True, 'Added successfully!')


def pm2Delete():
    args = getArgs()
    data = checkArgs(args, ['pname'])
    if not data[0]:
        return data[1]

    pname = args['pname']
    cmd = 'pm2 stop "' + pname + '" && pm2 delete "' + \
        pname + '" | grep "' + pname + '"'
    result = slemp.execShell(__SR + cmd)[0]
    if result.find('✓') != -1:
        slemp.execShell(__SR + 'pm2 save && pm2 startup')
        if os.path.exists(__path + '/' + pname):
            os.remove(__path + '/' + pname)
        return slemp.returnJson(True, 'Successfully deleted!')
    return slemp.returnJson(False, 'Failed to delete!')


def pm2Stop():
    args = getArgs()
    data = checkArgs(args, ['pname'])
    if not data[0]:
        return data[1]

    pname = args['pname']
    result = slemp.execShell(__SR + 'pm2 stop "' +
                          pname + '"|grep ' + pname)[0]
    if result.find('stoped') != -1:
        return slemp.returnJson(True, 'Project ['+pname+'] stopped!')
    return slemp.returnJson(True, 'Project ['+pname+'] stop failed!')


def pm2Start():
    args = getArgs()
    data = checkArgs(args, ['pname'])
    if not data[0]:
        return data[1]

    pname = args['pname']
    result = slemp.execShell(
        __SR + 'pm2 start "' + pname + '"|grep ' + pname)[0]
    if result.find('online') != -1:
        return slemp.returnJson(True, 'Project ['+pname+'] started!')
    return slemp.returnJson(False, 'Project ['+pname+'] failed to start!')


def pm2VerList():
    # Get a list of Node versions
    import re
    result = {}
    rep = r'v\d+\.\d+\.\d+'

    cmd = __SR + ' nvm ls-remote|grep -v v0|grep -v iojs'
    # print cmd
    tmp = slemp.execShell(cmd)
    result['list'] = re.findall(rep, tmp[0])
    tmp = slemp.execShell(__SR + "nvm version")
    result['version'] = tmp[0].strip()
    return slemp.returnJson(True, 'ok', result)


def setNodeVersion():
    args = getArgs()
    data = checkArgs(args, ['version'])
    if not data[0]:
        return data[1]
    # Switch Node version
    version = args['version'].replace('v', '')
    estr = '''
export NVM_NODEJS_ORG_MIRROR=https://cdn.npmmirror.com/binaries/node && nvm install %s
nvm use %s
nvm alias default %s
oldreg=`npm get registry`
npm config set registry https://registry.npmmirror.com/
npm install pm2 -g
npm config set registry $oldreg
''' % (version, version, version)
    cmd = __SR + estr
    slemp.execShell(cmd)
    return slemp.returnJson(True, 'Switched to [' + version + ']')


def getMod():
    cmd = __SR + "npm list --depth=0 -global"
    tmp = slemp.execShell(cmd)
    modList = tmp[0].replace("│", "").replace("└", "").replace(
        "─", "").replace("┴", "").replace("┘", "").strip().split()
    result = []
    for m in modList:
        mod = {}
        tmp = m.split('@')
        if len(tmp) < 2:
            continue
        mod['name'] = tmp[0]
        mod['version'] = tmp[1]
        result.append(mod)

    return slemp.returnJson(True, 'OK', result)


# Install the library
def installMod():
    args = getArgs()
    data = checkArgs(args, ['mname'])
    if not data[0]:
        return data[1]

    mname = args['mname']
    slemp.execShell(__SR + 'npm install ' + mname + ' -g')
    return slemp.returnJson(True, 'Successful installation!')


def uninstallMod():
    args = getArgs()
    data = checkArgs(args, ['mname'])
    if not data[0]:
        return data[1]

    mname = args['mname']
    myNot = ['pm2', 'npm']
    if mname in myNot:
        return slemp.returnJson(False, 'Cannot uninstall ['+mname+']')
    slemp.execShell(__SR + 'npm uninstall ' + mname + ' -g')
    return slemp.returnJson(True, 'Uninstalled successfully!')


def nodeLogRun():
    args = getArgs()
    data = checkArgs(args, ['pname'])
    if not data[0]:
        return data[1]

    pname = args['pname']
    return pm2LogDir() + '/logs/' + pname + '-out.log'


def nodeLogErr():
    args = getArgs()
    data = checkArgs(args, ['pname'])
    if not data[0]:
        return data[1]

    pname = args['pname']
    return pm2LogDir() + '/logs/' + pname + '-error.log'


def nodeLogClearRun():
    args = getArgs()
    data = checkArgs(args, ['pname'])
    if not data[0]:
        return data[1]

    pname = args['pname']
    path = pm2LogDir() + '/logs/' + pname + '-out.log'
    slemp.execShell('rm -rf ' + path + '&& touch ' + path)
    return slemp.returnJson(True, 'Clear run successfully')


def nodeLogClearErr():
    args = getArgs()
    data = checkArgs(args, ['pname'])
    if not data[0]:
        return data[1]
    pname = args['pname']
    path = pm2LogDir() + '/logs/' + pname + '-error.log'
    slemp.execShell('rm -rf ' + path + '&& touch ' + path)
    return slemp.returnJson(True, 'Clear error succeeded')

if __name__ == "__main__":
    func = sys.argv[1]
    if func == 'status':
        print(status())
    elif func == 'restart':
        print(restart())
    elif func == 'reload':
        print(reload())
    elif func == 'list':
        print(pm2List())
    elif func == 'add':
        print(pm2Add())
    elif func == 'delete':
        print(pm2Delete())
    elif func == 'stop':
        print(pm2Stop())
    elif func == 'start':
        print(pm2Start())
    elif func == 'get_logs':
        print(pm2Log())
    elif func == 'node_log_run':
        print(nodeLogRun())
    elif func == 'node_log_err':
        print(nodeLogErr())
    elif func == 'node_log_clear_run':
        print(nodeLogClearRun())
    elif func == 'node_log_clear_err':
        print(nodeLogClearErr())
    elif func == 'versions':
        print(pm2VerList())
    elif func == 'set_node_version':
        print(setNodeVersion())
    elif func == 'mod_list':
        print(getMod())
    elif func == 'install_mod':
        print(installMod())
    elif func == 'uninstall_mod':
        print(uninstallMod())
    else:
        print('error')
