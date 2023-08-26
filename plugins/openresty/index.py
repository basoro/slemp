# coding:utf-8

import sys
import io
import os
import time
import threading
import subprocess
import re

sys.path.append(os.getcwd() + "/class/core")
import slemp


app_debug = False

if slemp.isAppleSystem():
    app_debug = True


def getPluginName():
    return 'openresty'


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
            return (False, slemp.returnJson(False, 'Parameters: (' + ck[i] + ') none!'))
    return (True, slemp.returnJson(True, 'ok'))


def clearTemp():
    path_bin = getServerDir() + "/nginx"
    slemp.execShell('rm -rf ' + path_bin + '/client_body_temp')
    slemp.execShell('rm -rf ' + path_bin + '/fastcgi_temp')
    slemp.execShell('rm -rf ' + path_bin + '/proxy_temp')
    slemp.execShell('rm -rf ' + path_bin + '/scgi_temp')
    slemp.execShell('rm -rf ' + path_bin + '/uwsgi_temp')


def getConf():
    path = getServerDir() + "/nginx/conf/nginx.conf"
    return path


def getConfTpl():
    path = getPluginDir() + '/conf/nginx.conf'
    return path


def getOs():
    data = {}
    data['os'] = slemp.getOs()
    ng_exe_bin = getServerDir() + "/nginx/sbin/nginx"
    if checkAuthEq(ng_exe_bin, 'root'):
        data['auth'] = True
    else:
        data['auth'] = False
    return slemp.getJson(data)


def getInitDTpl():
    path = getPluginDir() + "/init.d/nginx.tpl"
    return path


def getFileOwner(filename):
    import pwd
    stat = os.lstat(filename)
    uid = stat.st_uid
    pw = pwd.getpwuid(uid)
    return pw.pw_name


def checkAuthEq(file, owner='root'):
    fowner = getFileOwner(file)
    if (fowner == owner):
        return True
    return False


def confReplace():
    service_path = os.path.dirname(os.getcwd())
    content = slemp.readFile(getConfTpl())
    content = content.replace('{$SERVER_PATH}', service_path)

    user = 'www'
    user_group = 'www'

    if slemp.getOs() == 'darwin':
        # macosx do
        user = slemp.execShell(
            "who | sed -n '2, 1p' |awk '{print $1}'")[0].strip()
        # user = 'root'
        user_group = 'staff'
        content = content.replace('{$EVENT_MODEL}', 'kqueue')
    else:
        content = content.replace('{$EVENT_MODEL}', 'epoll')

    content = content.replace('{$OS_USER}', user)
    content = content.replace('{$OS_USER_GROUP}', user_group)

    # ng_conf_md5 = ''
    # ng_conf_md5_file = getServerDir() + '/nginx_conf.md5'
    # if not os.path.exists(ng_conf_md5_file):
    #     ng_conf_md5 = slemp.md5(content)
    #     slemp.writeFile(ng_conf_md5_file, ng_conf_md5)
    # else:
    #     ng_conf_md5 = slemp.writeFile(ng_conf_md5_file).strip()

    nconf = getServerDir() + '/nginx/conf/nginx.conf'
    slemp.writeFile(nconf, content)

    lua_conf_dir = slemp.getServerDir() + '/web_conf/nginx/lua'
    if not os.path.exists(lua_conf_dir):
        slemp.execShell('mkdir -p ' + lua_conf_dir)

    lua_conf = lua_conf_dir + '/lua.conf'
    lua_conf_tpl = getPluginDir() + '/conf/lua.conf'
    lua_content = slemp.readFile(lua_conf_tpl)
    lua_content = lua_content.replace('{$SERVER_PATH}', service_path)
    slemp.writeFile(lua_conf, lua_content)

    empty_lua = lua_conf_dir + '/empty.lua'
    if not os.path.exists(empty_lua):
        slemp.writeFile(empty_lua, '')

    slemp.opLuaMakeAll()

    php_conf = slemp.getServerDir() + '/web_conf/php/conf'
    if not os.path.exists(php_conf):
        slemp.execShell('mkdir -p ' + php_conf)
    static_conf = slemp.getServerDir() + '/web_conf/php/conf/enable-php-00.conf'
    if not os.path.exists(static_conf):
        slemp.writeFile(static_conf, 'set $PHP_ENV 0;')

    # give nginx root permission
    ng_exe_bin = getServerDir() + "/nginx/sbin/nginx"
    if not checkAuthEq(ng_exe_bin, 'root'):
        args = getArgs()
        sudoPwd = args['pwd']
        cmd_own = 'chown -R ' + 'root:' + user_group + ' ' + ng_exe_bin
        os.system('echo %s|sudo -S %s' % (sudoPwd, cmd_own))
        cmd_mod = 'chmod 755 ' + ng_exe_bin
        os.system('echo %s|sudo -S %s' % (sudoPwd, cmd_mod))
        cmd_s = 'chmod u+s ' + ng_exe_bin
        os.system('echo %s|sudo -S %s' % (sudoPwd, cmd_s))


    # vhost
    vhost_dir = slemp.getServerDir() + '/web_conf/nginx/vhost'
    vhost_tpl_dir = getPluginDir() + '/conf/vhost'
    # print(vhost_dir, vhost_tpl_dir)
    vhost_list = ['0.websocket.conf', '0.nginx_status.conf']
    for f in vhost_list:
        a_conf = vhost_dir + '/' + f
        a_conf_tpl = vhost_tpl_dir + '/' + f
        if not os.path.exists(a_conf):
            slemp.writeFile(a_conf, slemp.readFile(a_conf_tpl))

def initDreplace():

    file_tpl = getInitDTpl()
    service_path = os.path.dirname(os.getcwd())

    initD_path = getServerDir() + '/init.d'

    # OpenResty is not installed
    if not os.path.exists(getServerDir()):
        print("ok")
        exit(0)

    # init.d
    file_bin = initD_path + '/' + getPluginName()
    if not os.path.exists(initD_path):
        os.mkdir(initD_path)

        # initd replace
        content = slemp.readFile(file_tpl)
        content = content.replace('{$SERVER_PATH}', service_path)
        slemp.writeFile(file_bin, content)
        slemp.execShell('chmod +x ' + file_bin)

        # config replace
        confReplace()

    # systemd
    # /usr/lib/systemd/system
    systemDir = slemp.systemdCfgDir()
    systemService = systemDir + '/openresty.service'
    systemServiceTpl = getPluginDir() + '/init.d/openresty.service.tpl'
    if os.path.exists(systemDir) and not os.path.exists(systemService):
        se_content = slemp.readFile(systemServiceTpl)
        se_content = se_content.replace('{$SERVER_PATH}', service_path)
        slemp.writeFile(systemService, se_content)
        slemp.execShell('systemctl daemon-reload')

    return file_bin


def status():
    data = slemp.execShell(
        "ps -ef|grep openresty |grep -v grep | grep -v python | awk '{print $2}'")
    if data[0] == '':
        return 'stop'
    return 'start'


def restyOp(method):
    file = initDreplace()

    check = getServerDir() + "/bin/openresty -t"
    check_data = slemp.execShell(check)
    if not check_data[1].find('test is successful') > -1:
        return check_data[1]

    if not slemp.isAppleSystem():
        data = slemp.execShell('systemctl ' + method + ' openresty')
        if data[1] == '':
            return 'ok'
        return data[1]

    data = slemp.execShell(file + ' ' + method)
    if data[1] == '':
        return 'ok'
    return data[1]


def op_submit_systemctl_restart():
    slemp.execShell('systemctl restart openresty')


def op_submit_init_restart(file):
    slemp.execShell(file + ' restart')


def restyOp_restart():
    file = initDreplace()

    check = getServerDir() + "/bin/openresty -t"
    check_data = slemp.execShell(check)
    if not check_data[1].find('test is successful') > -1:
        return 'ERROR: configuration error<br><a style="color:red;">' + check_data[1].replace("\n", '<br>') + '</a>'

    if not slemp.isAppleSystem():
        threading.Timer(2, op_submit_systemctl_restart, args=()).start()
        # submit_restart1()
        return 'ok'

    threading.Timer(2, op_submit_init_restart, args=(file,)).start()
    # submit_restart2(file)
    return 'ok'


def start():
    return restyOp('start')


def stop():
    return restyOp('stop')


def restart():
    return restyOp_restart()


def reload():
    return restyOp('reload')


def initdStatus():

    if slemp.isAppleSystem():
        return "Apple Computer does not support"

    shell_cmd = 'systemctl status openresty | grep loaded | grep "enabled;"'
    data = slemp.execShell(shell_cmd)
    if data[0] == '':
        return 'fail'
    return 'ok'


def initdInstall():
    if slemp.isAppleSystem():
        return "Apple Computer does not support"

    slemp.execShell('systemctl enable openresty')
    return 'ok'


def initdUinstall():
    if slemp.isAppleSystem():
        return "Apple Computer does not support"

    slemp.execShell('systemctl disable openresty')
    return 'ok'


def runInfo():
    try:
        url = 'http://127.0.0.1/nginx_status'
        result = slemp.httpGet(url, timeout=1)
        tmp = result.split()
        data = {}
        data['active'] = tmp[2]
        data['accepts'] = tmp[9]
        data['handled'] = tmp[7]
        data['requests'] = tmp[8]
        data['Reading'] = tmp[11]
        data['Writing'] = tmp[13]
        data['Waiting'] = tmp[15]
        return slemp.getJson(data)
    except Exception as e:

        url = 'http://' + slemp.getHostAddr() + '/nginx_status'
        result = slemp.httpGet(url)
        tmp = result.split()
        data = {}
        data['active'] = tmp[2]
        data['accepts'] = tmp[9]
        data['handled'] = tmp[7]
        data['requests'] = tmp[8]
        data['Reading'] = tmp[11]
        data['Writing'] = tmp[13]
        data['Waiting'] = tmp[15]
        return slemp.getJson(data)
    except Exception as e:
        return 'oprenresty not started'


def errorLogPath():
    return getServerDir() + '/nginx/logs/error.log'


def getCfg():
    cfg = getConf()
    content = slemp.readFile(cfg)

    unitrep = "[kmgKMG]"
    cfg_args = [
        {"name": "worker_processes", "ps": "Processing process, auto means automatic, number means the number of processes", 'type': 2},
        {"name": "worker_connections", "ps": "Maximum number of concurrent connections", 'type': 2},
        {"name": "keepalive_timeout", "ps": "Connection timeout", 'type': 2},
        {"name": "gzip", "ps": "Whether to enable compressed transmission", 'type': 1},
        {"name": "gzip_min_length", "ps": "Minimal zip file", 'type': 2},
        {"name": "gzip_comp_level", "ps": "Compression ratio", 'type': 2},
        {"name": "client_max_body_size", "ps": "Maximum uploaded files", 'type': 2},
        {"name": "server_names_hash_bucket_size", "ps": "The hash table size of the server name", 'type': 2},
        {"name": "client_header_buffer_size", "ps": "Client request header buffer size", 'type': 2},
    ]

    rdata = []
    for i in cfg_args:
        rep = "(%s)\s+(\w+)" % i["name"]
        k = re.search(rep, content)
        if not k:
            return slemp.returnJson(False, "Failed to get key {}".format(k))
        k = k.group(1)
        v = re.search(rep, content)
        if not v:
            return slemp.returnJson(False, "Failed to get value {}".format(v))
        v = v.group(2)

        if re.search(unitrep, v):
            u = str.upper(v[-1])
            v = v[:-1]
            if len(u) == 1:
                psstr = u + "B，" + i["ps"]
            else:
                psstr = u + "，" + i["ps"]
        else:
            u = ""

        kv = {"name": k, "value": v, "unit": u,
              "ps": i["ps"], "type": i["type"]}
        rdata.append(kv)

    return slemp.returnJson(True, "ok", rdata)


def setCfg():

    args = getArgs()
    data = checkArgs(args, [
        'worker_processes', 'worker_connections', 'keepalive_timeout',
        'gzip', 'gzip_min_length', 'gzip_comp_level', 'client_max_body_size',
        'server_names_hash_bucket_size', 'client_header_buffer_size'
    ])
    if not data[0]:
        return data[1]

    cfg = getConf()
    slemp.backFile(cfg)
    content = slemp.readFile(cfg)

    unitrep = "[kmgKMG]"
    cfg_args = [
        {"name": "worker_processes", "ps": "Processing process, auto means automatic, number means the number of processes", 'type': 2},
        {"name": "worker_connections", "ps": "Maximum number of concurrent connections", 'type': 2},
        {"name": "keepalive_timeout", "ps": "Connection timeout", 'type': 2},
        {"name": "gzip", "ps": "Whether to enable compressed transmission", 'type': 1},
        {"name": "gzip_min_length", "ps": "Minimal zip file", 'type': 2},
        {"name": "gzip_comp_level", "ps": "Compression ratio", 'type': 2},
        {"name": "client_max_body_size", "ps": "Maximum uploaded files", 'type': 2},
        {"name": "server_names_hash_bucket_size", "ps": "The hash table size of the server name", 'type': 2},
        {"name": "client_header_buffer_size", "ps": "Client request header buffer size", 'type': 2},
    ]

    # print(args)
    for k, v in args.items():
        # print(k, v)
        rep = "%s\s+[^kKmMgG\;\n]+" % k
        if k == "worker_processes" or k == "gzip":
            if not re.search("auto|on|off|\d+", v):
                return slemp.returnJson(False, 'Wrong parameter value')
        else:
            if not re.search("\d+", v):
                return slemp.returnJson(False, 'The parameter value is wrong, please enter a numeric integer')

        if re.search(rep, content):
            newconf = "%s %s" % (k, v)
            content = re.sub(rep, newconf, content)
        elif re.search(rep, content):
            newconf = "%s %s" % (k, v)
            content = re.sub(rep, newconf, content)

    slemp.writeFile(cfg, content)
    isError = slemp.checkWebConfig()
    if (isError != True):
        slemp.restoreFile(cfg)
        return slemp.returnJson(False, 'ERROR: configuration error<br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')

    slemp.restartWeb()
    return slemp.returnJson(True, 'Successfully set')


def installPreInspection():
    return 'ok'


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
    elif func == 'install_pre_inspection':
        print(installPreInspection())
    elif func == 'conf':
        print(getConf())
    elif func == 'get_os':
        print(getOs())
    elif func == 'run_info':
        print(runInfo())
    elif func == 'error_log':
        print(errorLogPath())
    elif func == 'get_cfg':
        print(getCfg())
    elif func == 'set_cfg':
        print(setCfg())
    else:
        print('error')
