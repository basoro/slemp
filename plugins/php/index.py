# coding:utf-8

import sys
import io
import os
import time
import re
import json
import shutil

# reload(sys)
# sys.setdefaultencoding('utf8')

sys.path.append(os.getcwd() + "/class/core")
# sys.path.append("/usr/local/lib/python3.6/site-packages")

import slemp

if slemp.isAppleSystem():
    cmd = 'ls /usr/local/lib/ | grep python  | cut -d \\  -f 1 | awk \'END {print}\''
    info = slemp.execShell(cmd)
    p = "/usr/local/lib/" + info[0].strip() + "/site-packages"
    sys.path.append(p)

app_debug = False
if slemp.isAppleSystem():
    app_debug = True


def getPluginName():
    return 'php'


def getPluginDir():
    return slemp.getPluginDir() + '/' + getPluginName()


def getServerDir():
    return slemp.getServerDir() + '/' + getPluginName()


def getInitDFile(version):
    if app_debug:
        return '/tmp/' + getPluginName()
    return '/etc/init.d/' + getPluginName() + version


def getArgs():
    args = sys.argv[3:]
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
            return (False, slemp.returnJson(False, '参数:(' + ck[i] + ')没有!'))
    return (True, slemp.returnJson(True, 'ok'))


def getConf(version):
    path = getServerDir() + '/' + version + '/etc/php.ini'
    return path


def getFpmConfFile(version):
    return getServerDir() + '/' + version + '/etc/php-fpm.d/www.conf'


def status_progress(version):
    # ps -ef|grep 'php/81' |grep -v grep | grep -v python | awk '{print $2}
    cmd = "ps -ef|grep 'php/" + version + \
        "' |grep -v grep | grep -v python | awk '{print $2}'"
    data = slemp.execShell(cmd)
    if data[0] == '':
        return 'stop'
    return 'start'


def getPhpSocket(version):
    path = getFpmConfFile(version)
    content = slemp.readFile(path)
    rep = 'listen\s*=\s*(.*)'
    tmp = re.search(rep, content)
    return tmp.groups()[0].strip()


def status(version):
    '''
    sock file to determine whether to start
    '''
    sock = getPhpSocket(version)
    if sock.find(':'):
        return status_progress(version)

    if not os.path.exists(sock):
        return 'stop'
    return 'start'


def contentReplace(content, version):
    service_path = slemp.getServerDir()
    content = content.replace('{$ROOT_PATH}', slemp.getRootDir())
    content = content.replace('{$SERVER_PATH}', service_path)
    content = content.replace('{$PHP_VERSION}', version)
    content = content.replace('{$LOCAL_IP}', slemp.getLocalIp())

    if slemp.isAppleSystem():
        # user = slemp.execShell(
        #     "who | sed -n '2, 1p' |awk '{print $1}'")[0].strip()
        content = content.replace('{$PHP_USER}', 'nobody')
        content = content.replace('{$PHP_GROUP}', 'nobody')

        rep = 'listen.owner\s*=\s*(.+)\r?\n'
        val = ';listen.owner = nobody\n'
        content = re.sub(rep, val, content)

        rep = 'listen.group\s*=\s*(.+)\r?\n'
        val = ';listen.group = nobody\n'
        content = re.sub(rep, val, content)

        rep = 'user\s*=\s*(.+)\r?\n'
        val = ';user = nobody\n'
        content = re.sub(rep, val, content)

        rep = r'[^\.]group\s*=\s*(.+)\r?\n'
        val = ';group = nobody\n'
        content = re.sub(rep, val, content)

    else:
        content = content.replace('{$PHP_USER}', 'www')
        content = content.replace('{$PHP_GROUP}', 'www')
    return content


def makeOpenrestyConf():
    phpversions = ['00', '52', '53', '54', '55', '56',
                   '70', '71', '72', '73', '74', '80', '81', '82']

    sdir = slemp.getServerDir()

    dst_dir = sdir + '/web_conf/php'
    dst_dir_conf = sdir + '/web_conf/php/conf'
    if not os.path.exists(dst_dir):
        slemp.execShell('mkdir -p ' + dst_dir)

    if not os.path.exists(dst_dir_conf):
        slemp.execShell('mkdir -p ' + dst_dir_conf)

    d_pathinfo = sdir + '/web_conf/php/pathinfo.conf'
    if not os.path.exists(d_pathinfo):
        s_pathinfo = getPluginDir() + '/conf/pathinfo.conf'
        shutil.copyfile(s_pathinfo, d_pathinfo)

    info = getPluginDir() + '/info.json'
    content = slemp.readFile(info)
    content = json.loads(content)
    versions = content['versions']
    tpl = getPluginDir() + '/conf/enable-php.conf'
    tpl_content = slemp.readFile(tpl)
    for x in phpversions:
        dfile = sdir + '/web_conf/php/conf/enable-php-' + x + '.conf'
        if not os.path.exists(dfile):
            if x == '00':
                slemp.writeFile(dfile, 'set $PHP_ENV 0;')
            else:
                w_content = contentReplace(tpl_content, x)
                slemp.writeFile(dfile, w_content)

    # php-fpm status
    # for version in phpversions:
    #     dfile = sdir + '/web_conf/php/status/phpfpm_status_' + version + '.conf'
    #     tpl = getPluginDir() + '/conf/phpfpm_status.conf'
    #     if not os.path.exists(dfile):
    #         content = slemp.readFile(tpl)
    #         content = contentReplace(content, version)
    #         slemp.writeFile(dfile, content)


def phpPrependFile(version):
    app_start = getServerDir() + '/app_start.php'
    if not os.path.exists(app_start):
        tpl = getPluginDir() + '/conf/app_start.php'
        content = slemp.readFile(tpl)
        content = contentReplace(content, version)
        slemp.writeFile(app_start, content)


def phpFpmReplace(version):
    desc_php_fpm = getServerDir() + '/' + version + '/etc/php-fpm.conf'
    if not os.path.exists(desc_php_fpm):
        tpl_php_fpm = getPluginDir() + '/conf/php-fpm.conf'
        content = slemp.readFile(tpl_php_fpm)
        content = contentReplace(content, version)
        slemp.writeFile(desc_php_fpm, content)
    else:
        if version == '52':
            tpl_php_fpm = tpl_php_fpm = getPluginDir() + '/conf/php-fpm-52.conf'
            content = slemp.readFile(tpl_php_fpm)
            slemp.writeFile(desc_php_fpm, content)


def phpFpmWwwReplace(version):
    service_php_fpm_dir = getServerDir() + '/' + version + '/etc/php-fpm.d/'

    if not os.path.exists(service_php_fpm_dir):
        os.mkdir(service_php_fpm_dir)

    service_php_fpmwww = service_php_fpm_dir + '/www.conf'
    if not os.path.exists(service_php_fpmwww):
        tpl_php_fpmwww = getPluginDir() + '/conf/www.conf'
        content = slemp.readFile(tpl_php_fpmwww)
        content = contentReplace(content, version)
        slemp.writeFile(service_php_fpmwww, content)


def makePhpIni(version):
    dst_ini = getConf(version)
    if not os.path.exists(dst_ini):
        src_ini = getPluginDir() + '/conf/php' + version[0:1] + '.ini'
        # shutil.copyfile(s_ini, d_ini)
        content = slemp.readFile(src_ini)
        if version == '52':
            content = content + "auto_prepend_file=/home/slemp/server/php/app_start.php"

        content = contentReplace(content, version)
        slemp.writeFile(dst_ini, content)


def initReplace(version):
    makeOpenrestyConf()
    makePhpIni(version)

    initD_path = getServerDir() + '/init.d'
    if not os.path.exists(initD_path):
        os.mkdir(initD_path)

    file_bin = initD_path + '/php' + version
    if not os.path.exists(file_bin):
        file_tpl = getPluginDir() + '/init.d/php.tpl'

        if version == '52':
            file_tpl = getPluginDir() + '/init.d/php52.tpl'

        content = slemp.readFile(file_tpl)
        content = contentReplace(content, version)

        slemp.writeFile(file_bin, content)
        slemp.execShell('chmod +x ' + file_bin)

    phpPrependFile(version)
    phpFpmWwwReplace(version)
    phpFpmReplace(version)

    session_path = getServerDir() + '/tmp/session'
    if not os.path.exists(session_path):
        slemp.execShell('mkdir -p ' + session_path)
        slemp.execShell('chown -R www:www ' + session_path)

    upload_path = getServerDir() + '/tmp/upload'
    if not os.path.exists(upload_path):
        slemp.execShell('mkdir -p ' + upload_path)
        slemp.execShell('chown -R www:www ' + upload_path)

    # systemd
    systemDir = slemp.systemdCfgDir()
    systemService = systemDir + '/php' + version + '.service'
    systemServiceTpl = getPluginDir() + '/init.d/php.service.tpl'
    if version == '52':
        systemServiceTpl = getPluginDir() + '/init.d/php.service.52.tpl'

    if os.path.exists(systemDir) and not os.path.exists(systemService):
        service_path = slemp.getServerDir()
        se_content = slemp.readFile(systemServiceTpl)
        se_content = se_content.replace('{$VERSION}', version)
        se_content = se_content.replace('{$SERVER_PATH}', service_path)
        slemp.writeFile(systemService, se_content)
        slemp.execShell('systemctl daemon-reload')

    return file_bin


def phpOp(version, method):
    file = initReplace(version)

    if not slemp.isAppleSystem():
        if method == 'stop' or method == 'restart':
            slemp.execShell(file + ' ' + 'stop')

        data = slemp.execShell('systemctl ' + method + ' php' + version)
        if data[1] == '':
            return 'ok'
        return data[1]

    data = slemp.execShell(file + ' ' + method)
    if data[1] == '':
        return 'ok'
    return data[1]


def start(version):
    return phpOp(version, 'start')


def stop(version):
    status = phpOp(version, 'stop')

    if version == '52':
        file = initReplace(version)
        data = slemp.execShell(file + ' ' + 'stop')
        if data[1] == '':
            return 'ok'
    return status


def restart(version):
    return phpOp(version, 'restart')


def reload(version):
    if version == '52':
        return phpOp(version, 'restart')
    return phpOp(version, 'reload')


def initdStatus(version):
    if slemp.isAppleSystem():
        return "Apple Computer does not support"

    shell_cmd = 'systemctl status php' + version + ' | grep loaded | grep "enabled;"'
    data = slemp.execShell(shell_cmd)
    if data[0] == '':
        return 'fail'
    return 'ok'


def initdInstall(version):
    if slemp.isAppleSystem():
        return "Apple Computer does not support"

    slemp.execShell('systemctl enable php' + version)
    return 'ok'


def initdUinstall(version):
    if slemp.isAppleSystem():
        return "Apple Computer does not support"

    slemp.execShell('systemctl disable php' + version)
    return 'ok'


def fpmLog(version):
    return getServerDir() + '/' + version + '/var/log/php-fpm.log'


def fpmSlowLog(version):
    return getServerDir() + '/' + version + '/var/log/www-slow.log'


def getPhpConf(version):
    gets = [
        {'name': 'short_open_tag', 'type': 1, 'ps': 'Short tag support'},
        {'name': 'asp_tags', 'type': 1, 'ps': 'ASP tag support'},
        {'name': 'max_execution_time', 'type': 2, 'ps': 'Maximum script run time'},
        {'name': 'max_input_time', 'type': 2, 'ps': 'Maximum input time'},
        {'name': 'max_input_vars', 'type': 2, 'ps': 'Maximum number of inputs'},
        {'name': 'memory_limit', 'type': 2, 'ps': 'Script memory limit'},
        {'name': 'post_max_size', 'type': 2, 'ps': 'POST data maximum size'},
        {'name': 'file_uploads', 'type': 1, 'ps': 'Whether to allow uploading of files'},
        {'name': 'upload_max_filesize', 'type': 2, 'ps': 'Maximum size allowed to upload files'},
        {'name': 'max_file_uploads', 'type': 2, 'ps': 'Maximum number of files allowed to be uploaded at the same time'},
        {'name': 'default_socket_timeout', 'type': 2, 'ps': 'Socket timeout'},
        {'name': 'error_reporting', 'type': 3, 'ps': 'Error level'},
        {'name': 'display_errors', 'type': 1, 'ps': 'Whether to output detailed error information'},
        {'name': 'cgi.fix_pathinfo', 'type': 0, 'ps': 'Whether to enable pathinfo'},
        {'name': 'date.timezone', 'type': 3, 'ps': 'Time zone'}
    ]
    phpini = slemp.readFile(getConf(version))
    result = []
    for g in gets:
        rep = g['name'] + '\s*=\s*([0-9A-Za-z_& ~]+)(\s*;?|\r?\n)'
        tmp = re.search(rep, phpini)
        if not tmp:
            continue
        g['value'] = tmp.groups()[0]
        result.append(g)
    return slemp.getJson(result)


def submitPhpConf(version):
    gets = ['display_errors', 'cgi.fix_pathinfo', 'date.timezone', 'short_open_tag',
            'asp_tags', 'max_execution_time', 'max_input_time', 'max_input_vars', 'memory_limit',
            'post_max_size', 'file_uploads', 'upload_max_filesize', 'max_file_uploads',
            'default_socket_timeout', 'error_reporting']
    args = getArgs()
    filename = getServerDir() + '/' + version + '/etc/php.ini'
    phpini = slemp.readFile(filename)
    for g in gets:
        if g in args:
            rep = g + '\s*=\s*(.+)\r?\n'
            val = g + ' = ' + args[g] + '\n'
            phpini = re.sub(rep, val, phpini)
    slemp.writeFile(filename, phpini)
    # slemp.execShell(getServerDir() + '/init.d/php' + version + ' reload')
    reload(version)
    return slemp.returnJson(True, '设置成功')


def getLimitConf(version):
    fileini = getConf(version)
    phpini = slemp.readFile(fileini)
    filefpm = getFpmConfFile(version)
    phpfpm = slemp.readFile(filefpm)

    # print fileini, filefpm
    data = {}
    try:
        rep = "upload_max_filesize\s*=\s*([0-9]+)M"
        tmp = re.search(rep, phpini).groups()
        data['max'] = tmp[0]
    except:
        data['max'] = '50'

    try:
        rep = "request_terminate_timeout\s*=\s*([0-9]+)\n"
        tmp = re.search(rep, phpfpm).groups()
        data['maxTime'] = tmp[0]
    except:
        data['maxTime'] = 0

    try:
        rep = r"\n;*\s*cgi\.fix_pathinfo\s*=\s*([0-9]+)\s*\n"
        tmp = re.search(rep, phpini).groups()

        if tmp[0] == '1':
            data['pathinfo'] = True
        else:
            data['pathinfo'] = False
    except:
        data['pathinfo'] = False

    return slemp.getJson(data)


def setMaxTime(version):
    args = getArgs()
    data = checkArgs(args, ['time'])
    if not data[0]:
        return data[1]

    time = args['time']
    if int(time) < 30 or int(time) > 86400:
        return slemp.returnJson(False, 'Please fill in the value between 30-86400!')

    filefpm = getFpmConfFile(version)
    conf = slemp.readFile(filefpm)
    rep = "request_terminate_timeout\s*=\s*([0-9]+)\n"
    conf = re.sub(rep, "request_terminate_timeout = " + time + "\n", conf)
    slemp.writeFile(filefpm, conf)

    fileini = getServerDir() + "/" + version + "/etc/php.ini"
    phpini = slemp.readFile(fileini)
    rep = "max_execution_time\s*=\s*([0-9]+)\r?\n"
    phpini = re.sub(rep, "max_execution_time = " + time + "\n", phpini)
    rep = "max_input_time\s*=\s*([0-9]+)\r?\n"
    phpini = re.sub(rep, "max_input_time = " + time + "\n", phpini)
    slemp.writeFile(fileini, phpini)
    return slemp.returnJson(True, 'Set successfully!')


def setMaxSize(version):
    args = getArgs()
    data = checkArgs(args, ['max'])
    if not data[0]:
        return data[1]

    maxVal = args['max']
    if int(maxVal) < 2:
        return slemp.returnJson(False, 'Upload size limit cannot be less than 2MB!')

    path = getConf(version)
    conf = slemp.readFile(path)
    rep = u"\nupload_max_filesize\s*=\s*[0-9]+M"
    conf = re.sub(rep, u'\nupload_max_filesize = ' + maxVal + 'M', conf)
    rep = u"\npost_max_size\s*=\s*[0-9]+M"
    conf = re.sub(rep, u'\npost_max_size = ' + maxVal + 'M', conf)
    slemp.writeFile(path, conf)

    msg = slemp.getInfo('Set PHP-{1} maximum upload size to [{2}MB]!', (version, maxVal,))
    slemp.writeLog('Plugin Management [PHP]', msg)
    return slemp.returnJson(True, 'Set successfully!')


def getFpmConfig(version):

    filefpm = getServerDir() + '/' + version + '/etc/php-fpm.d/www.conf'
    conf = slemp.readFile(filefpm)
    data = {}
    rep = "\s*pm.max_children\s*=\s*([0-9]+)\s*"
    tmp = re.search(rep, conf).groups()
    data['max_children'] = tmp[0]

    rep = "\s*pm.start_servers\s*=\s*([0-9]+)\s*"
    tmp = re.search(rep, conf).groups()
    data['start_servers'] = tmp[0]

    rep = "\s*pm.min_spare_servers\s*=\s*([0-9]+)\s*"
    tmp = re.search(rep, conf).groups()
    data['min_spare_servers'] = tmp[0]

    rep = "\s*pm.max_spare_servers \s*=\s*([0-9]+)\s*"
    tmp = re.search(rep, conf).groups()
    data['max_spare_servers'] = tmp[0]

    rep = "\s*pm\s*=\s*(\w+)\s*"
    tmp = re.search(rep, conf).groups()
    data['pm'] = tmp[0]
    return slemp.getJson(data)


def setFpmConfig(version):
    args = getArgs()
    # if not 'max' in args:
    #     return 'missing time args!'

    version = args['version']
    max_children = args['max_children']
    start_servers = args['start_servers']
    min_spare_servers = args['min_spare_servers']
    max_spare_servers = args['max_spare_servers']
    pm = args['pm']

    file = getServerDir() + '/' + version + '/etc/php-fpm.d/www.conf'
    conf = slemp.readFile(file)

    rep = "\s*pm.max_children\s*=\s*([0-9]+)\s*"
    conf = re.sub(rep, "\npm.max_children = " + max_children, conf)

    rep = "\s*pm.start_servers\s*=\s*([0-9]+)\s*"
    conf = re.sub(rep, "\npm.start_servers = " + start_servers, conf)

    rep = "\s*pm.min_spare_servers\s*=\s*([0-9]+)\s*"
    conf = re.sub(rep, "\npm.min_spare_servers = " +
                  min_spare_servers, conf)

    rep = "\s*pm.max_spare_servers \s*=\s*([0-9]+)\s*"
    conf = re.sub(rep, "\npm.max_spare_servers = " +
                  max_spare_servers + "\n", conf)

    rep = "\s*pm\s*=\s*(\w+)\s*"
    conf = re.sub(rep, "\npm = " + pm + "\n", conf)

    slemp.writeFile(file, conf)
    reload(version)

    msg = slemp.getInfo('Set PHP-{1} concurrency settings,max_children={2},start_servers={3},min_spare_servers={4},max_spare_servers={5}', (version, max_children,
                                                                                                                      start_servers, min_spare_servers, max_spare_servers,))
    slemp.writeLog('Plugin Management [PHP]', msg)
    return slemp.returnJson(True, 'Set successfully!')


# def checkFpmStatusFile(version):
#     if not slemp.isInstalledWeb():
#         return False

#     dfile = getServerDir() + '/nginx/conf/php_status/phpfpm_status_' + version + '.conf'
#     if not os.path.exists(dfile):
#         tpl = getPluginDir() + '/conf/phpfpm_status.conf'
#         content = slemp.readFile(tpl)
#         content = contentReplace(content, version)
#         slemp.writeFile(dfile, content)
#         slemp.restartWeb()
#     return True


def getFpmAddress(version):
    fpm_address = '/tmp/php-cgi-{}.sock'.format(version)
    php_fpm_file = getFpmConfFile(version)
    try:
        content = readFile(php_fpm_file)
        tmp = re.findall(r"listen\s*=\s*(.+)", content)
        if not tmp:
            return fpm_address
        if tmp[0].find('sock') != -1:
            return fpm_address
        if tmp[0].find(':') != -1:
            listen_tmp = tmp[0].split(':')
            if bind:
                fpm_address = (listen_tmp[0], int(listen_tmp[1]))
            else:
                fpm_address = ('127.0.0.1', int(listen_tmp[1]))
        else:
            fpm_address = ('127.0.0.1', int(tmp[0]))
        return fpm_address
    except:
        return fpm_address


def getFpmStatus(version):

    if version == '52':
        return slemp.returnJson(False, 'PHP[' + version + '] not support!!!')

    stat = status(version)
    if stat == 'stop':
        return slemp.returnJson(False, 'PHP[' + version + '] have not started!!!')

    sock_file = getFpmAddress(version)
    try:
        sock_data = slemp.requestFcgiPHP(
            sock_file, '/phpfpm_status_' + version + '?json')
    except Exception as e:
        return slemp.returnJson(False, str(e))

    # print(data)
    result = str(sock_data, encoding='utf-8')
    data = json.loads(result)
    fTime = time.localtime(int(data['start time']))
    data['start time'] = time.strftime('%Y-%m-%d %H:%M:%S', fTime)
    return slemp.returnJson(True, "OK", data)


def getSessionConf(version):
    filename = getConf(version)
    if not os.path.exists(filename):
        return slemp.returnJson(False, 'The specified PHP version does not exist!')

    phpini = slemp.readFile(filename)

    rep = r'session.save_handler\s*=\s*([0-9A-Za-z_& ~]+)(\s*;?|\r?\n)'
    save_handler = re.search(rep, phpini)
    if save_handler:
        save_handler = save_handler.group(1)
    else:
        save_handler = "files"

    reppath = r'\nsession.save_path\s*=\s*"tcp\:\/\/([\d\.]+):(\d+).*\r?\n'
    passrep = r'\nsession.save_path\s*=\s*"tcp://[\w\.\?\:]+=(.*)"\r?\n'
    memcached = r'\nsession.save_path\s*=\s*"([\d\.]+):(\d+)"'
    save_path = re.search(reppath, phpini)
    if not save_path:
        save_path = re.search(memcached, phpini)
    passwd = re.search(passrep, phpini)
    port = ""
    if passwd:
        passwd = passwd.group(1)
    else:
        passwd = ""
    if save_path:
        port = save_path.group(2)
        save_path = save_path.group(1)

    else:
        save_path = ""

    data = {"save_handler": save_handler, "save_path": save_path,
            "passwd": passwd, "port": port}
    return slemp.returnJson(True, 'ok', data)


def setSessionConf(version):

    args = getArgs()

    ip = args['ip']
    port = args['port']
    passwd = args['passwd']
    save_handler = args['save_handler']

    if save_handler != "file":
        iprep = r"(2(5[0-5]{1}|[0-4]\d{1})|[0-1]?\d{1,2})\.(2(5[0-5]{1}|[0-4]\d{1})|[0-1]?\d{1,2})\.(2(5[0-5]{1}|[0-4]\d{1})|[0-1]?\d{1,2})\.(2(5[0-5]{1}|[0-4]\d{1})|[0-1]?\d{1,2})"
        if not re.search(iprep, ip):
            return slemp.returnJson(False, 'Please enter the correct IP address')

        try:
            port = int(port)
            if port >= 65535 or port < 1:
                return slemp.returnJson(False, 'Please enter the correct port number')
        except:
            return slemp.returnJson(False, 'Please enter the correct port number')
        prep = r"[\~\`\/\=]"
        if re.search(prep, passwd):
            return slemp.returnJson(False, 'Please do not enter the following special characters " ~ ` / = "')

    filename = getConf(version)
    if not os.path.exists(filename):
        return slemp.returnJson(False, 'The specified PHP version does not exist!')
    phpini = slemp.readFile(filename)

    session_tmp = getServerDir() + "/tmp/session"

    rep = r'session.save_handler\s*=\s*(.+)\r?\n'
    val = r'session.save_handler = ' + save_handler + '\n'
    phpini = re.sub(rep, val, phpini)

    if save_handler == "memcached":
        if not re.search("memcached.so", phpini):
            return slemp.returnJson(False, 'Please install the %s extension first' % save_handler)
        rep = r'\nsession.save_path\s*=\s*(.+)\r?\n'
        val = r'\nsession.save_path = "%s:%s" \n' % (ip, port)
        if re.search(rep, phpini):
            phpini = re.sub(rep, val, phpini)
        else:
            phpini = re.sub('\n;session.save_path = "' + session_tmp + '"',
                            '\n;session.save_path = "' + session_tmp + '"' + val, phpini)

    if save_handler == "memcache":
        if not re.search("memcache.so", phpini):
            return slemp.returnJson(False, 'Please install the %s extension first' % save_handler)
        rep = r'\nsession.save_path\s*=\s*(.+)\r?\n'
        val = r'\nsession.save_path = "%s:%s" \n' % (ip, port)
        if re.search(rep, phpini):
            phpini = re.sub(rep, val, phpini)
        else:
            phpini = re.sub('\n;session.save_path = "' + session_tmp + '"',
                            '\n;session.save_path = "' + session_tmp + '"' + val, phpini)

    if save_handler == "redis":
        if not re.search("redis.so", phpini):
            return slemp.returnJson(False, 'Please install the %s extension first' % save_handler)
        if passwd:
            passwd = "?auth=" + passwd
        else:
            passwd = ""
        rep = r'\nsession.save_path\s*=\s*(.+)\r?\n'
        val = r'\nsession.save_path = "tcp://%s:%s%s"\n' % (ip, port, passwd)
        res = re.search(rep, phpini)
        if res:
            phpini = re.sub(rep, val, phpini)
        else:
            phpini = re.sub('\n;session.save_path = "' + session_tmp + '"',
                            '\n;session.save_path = "' + session_tmp + '"' + val, phpini)

    if save_handler == "file":
        rep = r'\nsession.save_path\s*=\s*(.+)\r?\n'
        val = r'\nsession.save_path = "' + session_tmp + '"\n'
        if re.search(rep, phpini):
            phpini = re.sub(rep, val, phpini)
        else:
            phpini = re.sub('\n;session.save_path = "' + session_tmp + '"',
                            '\n;session.save_path = "' + session_tmp + '"' + val, phpini)

    slemp.writeFile(filename, phpini)
    reload(version)
    return slemp.returnJson(True, 'Set successfully!')


def getSessionCount_Origin(version):
    session_tmp = getServerDir() + "/tmp/session"
    d = [session_tmp]
    count = 0
    for i in d:
        if not os.path.exists(i):
            slemp.execShell('mkdir -p %s' % i)
        list = os.listdir(i)
        for l in list:
            if os.path.isdir(i + "/" + l):
                l1 = os.listdir(i + "/" + l)
                for ll in l1:
                    if "sess_" in ll:
                        count += 1
                continue
            if "sess_" in l:
                count += 1

    s = "find /tmp -mtime +1 |grep 'sess_' | wc -l"
    old_file = int(slemp.execShell(s)[0].split("\n")[0])

    s = "find " + session_tmp + " -mtime +1 |grep 'sess_'|wc -l"
    old_file += int(slemp.execShell(s)[0].split("\n")[0])
    return {"total": count, "oldfile": old_file}


def getSessionCount(version):
    data = getSessionCount_Origin(version)
    return slemp.returnJson(True, 'ok!', data)


def cleanSessionOld(version):
    s = "find /tmp -mtime +1 |grep 'sess_'|xargs rm -f"
    slemp.execShell(s)

    session_tmp = getServerDir() + "/tmp/session"
    s = "find " + session_tmp + " -mtime +1 |grep 'sess_' |xargs rm -f"
    slemp.execShell(s)
    old_file_conf = getSessionCount_Origin(version)["oldfile"]
    if old_file_conf == 0:
        return slemp.returnJson(True, 'Cleaned up successfully')
    else:
        return slemp.returnJson(True, 'Cleanup failed')


def getDisableFunc(version):
    filename = getConf(version)
    if not os.path.exists(filename):
        return slemp.returnJson(False, 'The specified PHP version does not exist!')

    phpini = slemp.readFile(filename)
    data = {}
    rep = "disable_functions\s*=\s{0,1}(.*)\n"
    tmp = re.search(rep, phpini).groups()
    data['disable_functions'] = tmp[0]
    return slemp.getJson(data)


def setDisableFunc(version):
    filename = getConf(version)
    if not os.path.exists(filename):
        return slemp.returnJson(False, 'The specified PHP version does not exist!')

    args = getArgs()
    disable_functions = args['disable_functions']

    phpini = slemp.readFile(filename)
    rep = "disable_functions\s*=\s*.*\n"
    phpini = re.sub(rep, 'disable_functions = ' +
                    disable_functions + "\n", phpini)

    msg = slemp.getInfo('Modify the disabled function of PHP-{1} to [{2}]', (version, disable_functions,))
    slemp.writeLog('Plugin Management [PHP]', msg)
    slemp.writeFile(filename, phpini)
    reload(version)
    return slemp.returnJson(True, 'Set successfully!')


def getPhpinfo(version):
    stat = status(version)
    if stat == 'stop':
        return 'PHP[' + version + '] not activated, not accessible!!!'

    sock_file = getFpmAddress(version)
    root_dir = slemp.getRootDir() + '/phpinfo'

    slemp.execShell("rm -rf " + root_dir)
    slemp.execShell("mkdir -p " + root_dir)
    slemp.writeFile(root_dir + '/phpinfo.php', '<?php phpinfo(); ?>')
    sock_data = slemp.requestFcgiPHP(sock_file, '/phpinfo.php', root_dir)
    os.system("rm -rf " + root_dir)
    phpinfo = str(sock_data, encoding='utf-8')
    return phpinfo


def get_php_info(args):
    return getPhpinfo(args['version'])


def getLibConf(version):
    fname = getConf(version)
    if not os.path.exists(fname):
        return slemp.returnJson(False, 'The specified PHP version does not exist!')

    phpini = slemp.readFile(fname)

    libpath = getPluginDir() + '/versions/phplib.conf'
    phplib = json.loads(slemp.readFile(libpath))

    libs = []
    tasks = slemp.M('tasks').where(
        "status!=?", ('1',)).field('status,name').select()
    for lib in phplib:
        lib['task'] = '1'
        for task in tasks:
            tmp = slemp.getStrBetween('[', ']', task['name'])
            if not tmp:
                continue
            tmp1 = tmp.split('-')
            if tmp1[0].lower() == lib['name'].lower():
                lib['task'] = task['status']
                lib['phpversions'] = []
                lib['phpversions'].append(tmp1[1])
        if phpini.find(lib['check']) == -1:
            lib['status'] = False
        else:
            lib['status'] = True
        libs.append(lib)
    return slemp.returnJson(True, 'OK!', libs)


def installLib(version):
    args = getArgs()
    data = checkArgs(args, ['name'])
    if not data[0]:
        return data[1]

    name = args['name']
    execstr = "cd " + getPluginDir() + "/versions && /bin/bash  common.sh " + \
        version + ' install ' + name

    rettime = time.strftime('%Y-%m-%d %H:%M:%S')
    insert_info = (None, 'Install [' + name + '-' + version + ']',
                   'execshell', '0', rettime, execstr)
    slemp.M('tasks').add('id,name,type,status,addtime,execstr', insert_info)

    slemp.triggerTask()
    return slemp.returnJson(True, 'Download task added to queue!')


def uninstallLib(version):
    args = getArgs()
    data = checkArgs(args, ['name'])
    if not data[0]:
        return data[1]

    name = args['name']
    execstr = "cd " + getPluginDir() + "/versions && /bin/bash  common.sh " + \
        version + ' uninstall ' + name

    data = slemp.execShell(execstr)
    # data[0] == '' and
    if data[1] == '':
        return slemp.returnJson(True, 'Uninstalled successfully!')
    else:
        return slemp.returnJson(False, 'Unload info![Channel 0]:' + data[0] + "[Channel 0]:" + data[1])


def getConfAppStart():
    pstart = slemp.getServerDir() + '/php/app_start.php'
    return pstart


def installPreInspection(version):
    if version != '52':
        return 'ok'

    sys = slemp.execShell(
        "cat /etc/*-release | grep PRETTY_NAME |awk -F = '{print $2}' | awk -F '\"' '{print $2}'| awk '{print $1}'")

    if sys[1] != '':
        return 'System modification is not supported'

    sys_id = slemp.execShell(
        "cat /etc/*-release | grep VERSION_ID | awk -F = '{print $2}' | awk -F '\"' '{print $2}'")

    sysName = sys[0].strip().lower()
    sysId = sys_id[0].strip()

    if sysName == 'ubuntu':
        return 'Ubuntu can\'t be installed'

    if sysName == 'debian' and int(sysId) > 10:
        return 'debian10 can be installed'

    if sysName == 'centos' and int(sysId) > 8:
        return 'centos[{}] cannot be installed'.format(sysId)

    if sysName == 'fedora':
        sys_id = slemp.execShell(
            "cat /etc/*-release | grep VERSION_ID | awk -F = '{print $2}'")
        sysId = sys_id[0].strip()
        if int(sysId) > 31:
            return 'fedora[{}]not installable'.format(sysId)
    return 'ok'

if __name__ == "__main__":

    if len(sys.argv) < 3:
        print('missing parameters')
        exit(0)

    func = sys.argv[1]
    version = sys.argv[2]

    if func == 'status':
        print(status(version))
    elif func == 'start':
        print(start(version))
    elif func == 'stop':
        print(stop(version))
    elif func == 'restart':
        print(restart(version))
    elif func == 'reload':
        print(reload(version))
    elif func == 'install_pre_inspection':
        print(installPreInspection(version))
    elif func == 'initd_status':
        print(initdStatus(version))
    elif func == 'initd_install':
        print(initdInstall(version))
    elif func == 'initd_uninstall':
        print(initdUinstall(version))
    elif func == 'fpm_log':
        print(fpmLog(version))
    elif func == 'fpm_slow_log':
        print(fpmSlowLog(version))
    elif func == 'conf':
        print(getConf(version))
    elif func == 'app_start':
        print(getConfAppStart())
    elif func == 'get_php_conf':
        print(getPhpConf(version))
    elif func == 'get_fpm_conf_file':
        print(getFpmConfFile(version))
    elif func == 'submit_php_conf':
        print(submitPhpConf(version))
    elif func == 'get_limit_conf':
        print(getLimitConf(version))
    elif func == 'set_max_time':
        print(setMaxTime(version))
    elif func == 'set_max_size':
        print(setMaxSize(version))
    elif func == 'get_fpm_conf':
        print(getFpmConfig(version))
    elif func == 'set_fpm_conf':
        print(setFpmConfig(version))
    elif func == 'get_fpm_status':
        print(getFpmStatus(version))
    elif func == 'get_session_conf':
        print(getSessionConf(version))
    elif func == 'set_session_conf':
        print(setSessionConf(version))
    elif func == 'get_session_count':
        print(getSessionCount(version))
    elif func == 'clean_session_old':
        print(cleanSessionOld(version))
    elif func == 'get_disable_func':
        print(getDisableFunc(version))
    elif func == 'set_disable_func':
        print(setDisableFunc(version))
    elif func == 'get_phpinfo':
        print(getPhpinfo(version))
    elif func == 'get_lib_conf':
        print(getLibConf(version))
    elif func == 'install_lib':
        print(installLib(version))
    elif func == 'uninstall_lib':
        print(uninstallLib(version))
    else:
        print("fail")
