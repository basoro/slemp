# coding:utf-8

import sys
import io
import os
import time
import re
import json

sys.path.append(os.getcwd() + "/class/core")
import slemp
import site_api

app_debug = False
if slemp.isAppleSystem():
    app_debug = True


def getPluginName():
    return 'phpmyadmin'


def getPluginDir():
    return slemp.getPluginDir() + '/' + getPluginName()


def getServerDir():
    return slemp.getServerDir() + '/' + getPluginName()


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


def getConf():
    return slemp.getServerDir() + '/web_conf/nginx/vhost/phpmyadmin.conf'


def getConfInc():
    return getServerDir() + "/" + getCfg()['path'] + '/config.inc.php'


def getPort():
    file = getConf()
    content = slemp.readFile(file)
    rep = 'listen\s*(.*);'
    tmp = re.search(rep, content)
    return tmp.groups()[0].strip()


def getHomePage():
    try:
        port = getPort()
        ip = '127.0.0.1'
        if not slemp.isAppleSystem():
            ip = slemp.getLocalIp()
        url = 'http://' + ip + ':' + port + \
            '/' + getCfg()['path'] + '/index.php'
        return slemp.returnJson(True, 'OK', url)
    except Exception as e:
        return slemp.returnJson(False, 'Plugin not started!')


def getPhpVer(expect=55):
    v = site_api.site_api().getPhpVersion()
    is_find = False
    for i in range(len(v)):
        t = str(v[i]['version'])
        if (t == expect):
            is_find = True
            return str(t)
    if not is_find:
        if len(v) > 1:
            return v[1]['version']
        return v[0]['version']
    return str(expect)


def getCachePhpVer():
    cacheFile = getServerDir() + '/php.pl'
    v = ''
    if os.path.exists(cacheFile):
        v = slemp.readFile(cacheFile)
    else:
        v = getPhpVer()
        slemp.writeFile(cacheFile, v)
    return v


def contentReplace(content):
    service_path = slemp.getServerDir()
    php_ver = getCachePhpVer()
    tmp = slemp.execShell(
        'cat /dev/urandom | head -n 32 | md5sum | head -c 16')
    blowfish_secret = tmp[0].strip()
    # print php_ver
    php_conf_dir = slemp.getServerDir() + '/web_conf/php/conf'
    content = content.replace('{$ROOT_PATH}', slemp.getRootDir())
    content = content.replace('{$SERVER_PATH}', service_path)
    content = content.replace('{$PHP_CONF_PATH}', php_conf_dir)
    content = content.replace('{$PHP_VER}', php_ver)
    content = content.replace('{$BLOWFISH_SECRET}', blowfish_secret)

    cfg = getCfg()

    if cfg['choose'] == "mysql":
        content = content.replace('{$CHOOSE_DB}', 'mysql')
        content = content.replace('{$CHOOSE_DB_DIR}', 'mysql')
    elif cfg['choose'] == "mysql-apt":
        content = content.replace('{$CHOOSE_DB}', 'mysql')
        content = content.replace('{$CHOOSE_DB_DIR}', 'mysql-apt')
    elif cfg['choose'] == "mysql-yum":
        content = content.replace('{$CHOOSE_DB}', 'mysql')
        content = content.replace('{$CHOOSE_DB_DIR}', 'mysql-yum')
    else:
        content = content.replace('{$CHOOSE_DB}', 'MariaDB')
        content = content.replace('{$CHOOSE_DB_DIR}', 'mariadb')

    content = content.replace('{$PMA_PATH}', cfg['path'])

    port = cfg["port"]
    rep = 'listen\s*(.*);'
    content = re.sub(rep, "listen " + port + ';', content)
    return content


def initCfg():
    cfg = getServerDir() + "/cfg.json"
    if not os.path.exists(cfg):
        data = {}
        data['port'] = '888'
        data['choose'] = 'mysql'
        data['path'] = ''
        data['username'] = 'admin'
        data['password'] = 'admin'
        slemp.writeFile(cfg, json.dumps(data))


def setCfg(key, val):
    cfg = getServerDir() + "/cfg.json"
    data = slemp.readFile(cfg)
    data = json.loads(data)
    data[key] = val
    slemp.writeFile(cfg, json.dumps(data))


def getCfg():
    cfg = getServerDir() + "/cfg.json"
    data = slemp.readFile(cfg)
    data = json.loads(data)
    return data


def returnCfg():
    cfg = getServerDir() + "/cfg.json"
    data = slemp.readFile(cfg)
    return data


def status():
    conf = getConf()
    conf_inc = getServerDir() + "/" + getCfg()["path"] + '/config.inc.php'
    if os.path.exists(conf) and os.path.exists(conf_inc):
        return 'start'
    return 'stop'


def start():
    initCfg()

    pma_dir = getServerDir() + "/phpmyadmin"
    if os.path.exists(pma_dir):
        rand_str = slemp.getRandomString(6)
        rand_str = rand_str.lower()
        pma_dir_dst = pma_dir + "_" + rand_str
        slemp.execShell("mv " + pma_dir + " " + pma_dir_dst)
        setCfg('path', 'phpmyadmin_' + rand_str)

    file_tpl = getPluginDir() + '/conf/phpmyadmin.conf'
    file_run = getConf()
    if not os.path.exists(file_run):
        centent = slemp.readFile(file_tpl)
        centent = contentReplace(centent)
        slemp.writeFile(file_run, centent)

    pma_path = getServerDir() + '/pma.pass'
    if not os.path.exists(pma_path):
        username = slemp.getRandomString(10)
        pass_cmd = username + ':' + slemp.hasPwd(username)
        setCfg('username', username)
        setCfg('password', username)
        slemp.writeFile(pma_path, pass_cmd)

    tmp = getServerDir() + "/" + getCfg()["path"] + '/tmp'
    if not os.path.exists(tmp):
        os.mkdir(tmp)
        slemp.execShell("chown -R www:www " + tmp)

    conf_run = getServerDir() + "/" + getCfg()["path"] + '/config.inc.php'
    if not os.path.exists(conf_run):
        conf_tpl = getPluginDir() + '/conf/config.inc.php'
        centent = slemp.readFile(conf_tpl)
        centent = contentReplace(centent)
        slemp.writeFile(conf_run, centent)

    log_a = accessLog()
    log_e = errorLog()

    for i in [log_a, log_e]:
        if os.path.exists(i):
            cmd = "echo '' > " + i
            slemp.execShell(cmd)

    slemp.restartWeb()
    return 'ok'


def stop():
    conf = getConf()
    if os.path.exists(conf):
        os.remove(conf)
    slemp.restartWeb()
    return 'ok'


def restart():
    return start()


def reload():
    file_tpl = getPluginDir() + '/conf/phpmyadmin.conf'
    file_run = getConf()
    if os.path.exists(file_run):
        centent = slemp.readFile(file_tpl)
        centent = contentReplace(centent)
        slemp.writeFile(file_run, centent)
    return start()


def setPhpVer():
    args = getArgs()

    if not 'phpver' in args:
        return 'phpver missing'

    cacheFile = getServerDir() + '/php.pl'
    slemp.writeFile(cacheFile, args['phpver'])

    file_tpl = getPluginDir() + '/conf/phpmyadmin.conf'
    file_run = getConf()

    content = slemp.readFile(file_tpl)
    content = contentReplace(content)
    slemp.writeFile(file_run, content)

    slemp.restartWeb()
    return 'ok'


def getSetPhpVer():
    cacheFile = getServerDir() + '/php.pl'
    if os.path.exists(cacheFile):
        return slemp.readFile(cacheFile).strip()
    return ''


def getPmaOption():
    data = getCfg()
    return slemp.returnJson(True, 'ok', data)


def getPmaPort():
    try:
        port = getPort()
        return slemp.returnJson(True, 'OK', port)
    except Exception as e:
        # print(e)
        return slemp.returnJson(False, 'Plugin not started!')


def setPmaPort():
    args = getArgs()
    data = checkArgs(args, ['port'])
    if not data[0]:
        return data[1]

    port = args['port']
    if port == '80':
        return slemp.returnJson(False, '80 can not be used!')

    file = getConf()
    if not os.path.exists(file):
        return slemp.returnJson(False, 'Plugin not started!')
    content = slemp.readFile(file)
    rep = 'listen\s*(.*);'
    content = re.sub(rep, "listen " + port + ';', content)
    slemp.writeFile(file, content)

    setCfg("port", port)
    slemp.restartWeb()
    return slemp.returnJson(True, 'Successfully modified!')


def setPmaChoose():
    args = getArgs()
    data = checkArgs(args, ['choose'])
    if not data[0]:
        return data[1]

    choose = args['choose']
    setCfg('choose', choose)

    pma_path = getCfg()['path']
    conf_run = getServerDir() + "/" + pma_path + '/config.inc.php'

    conf_tpl = getPluginDir() + '/conf/config.inc.php'
    content = slemp.readFile(conf_tpl)
    content = contentReplace(content)
    slemp.writeFile(conf_run, content)

    slemp.restartWeb()
    return slemp.returnJson(True, 'Successfully modified!')


def setPmaUsername():
    args = getArgs()
    data = checkArgs(args, ['username'])
    if not data[0]:
        return data[1]

    username = args['username']
    setCfg('username', username)

    cfg = getCfg()
    pma_path = getServerDir() + '/pma.pass'
    username = slemp.getRandomString(10)
    pass_cmd = cfg['username'] + ':' + slemp.hasPwd(cfg['password'])
    slemp.writeFile(pma_path, pass_cmd)

    slemp.restartWeb()
    return slemp.returnJson(True, 'Successfully modified!')


def setPmaPassword():
    args = getArgs()
    data = checkArgs(args, ['password'])
    if not data[0]:
        return data[1]

    password = args['password']
    setCfg('password', password)

    cfg = getCfg()
    pma_path = getServerDir() + '/pma.pass'
    username = slemp.getRandomString(10)
    pass_cmd = cfg['username'] + ':' + slemp.hasPwd(cfg['password'])
    slemp.writeFile(pma_path, pass_cmd)

    slemp.restartWeb()
    return slemp.returnJson(True, 'Successfully modified!')


def setPmaPath():
    args = getArgs()
    data = checkArgs(args, ['path'])
    if not data[0]:
        return data[1]

    path = args['path']

    if len(path) < 5:
        return slemp.returnJson(False, 'Cannot be less than 5 digits!')

    old_path = getServerDir() + "/" + getCfg()['path']
    new_path = getServerDir() + "/" + path

    slemp.execShell("mv " + old_path + " " + new_path)
    setCfg('path', path)
    return slemp.returnJson(True, 'Successfully modified!')


def accessLog():
    return getServerDir() + '/access.log'


def errorLog():
    return getServerDir() + '/error.log'


def Version():
    return slemp.readFile(getServerDir() + '/version.pl')


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
    elif func == 'version':
        print(Version())
    elif func == 'get_cfg':
        print(returnCfg())
    elif func == 'config_inc':
        print(getConfInc())
    elif func == 'get_home_page':
        print(getHomePage())
    elif func == 'set_php_ver':
        print(setPhpVer())
    elif func == 'get_set_php_ver':
        print(getSetPhpVer())
    elif func == 'get_pma_port':
        print(getPmaPort())
    elif func == 'set_pma_port':
        print(setPmaPort())
    elif func == 'get_pma_option':
        print(getPmaOption())
    elif func == 'set_pma_choose':
        print(setPmaChoose())
    elif func == 'set_pma_username':
        print(setPmaUsername())
    elif func == 'set_pma_password':
        print(setPmaPassword())
    elif func == 'set_pma_path':
        print(setPmaPath())
    elif func == 'access_log':
        print(accessLog())
    elif func == 'error_log':
        print(errorLog())
    else:
        print('error')
