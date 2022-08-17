# coding: utf-8

import sys
import os
import json
import time
import threading
import psutil

if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')


sys.path.append(os.getcwd() + "/class/core")
import slemp
import db

global pre, timeoutCount, logPath, isTask, oldEdate, isCheck
pre = 0
timeoutCount = 0
isCheck = 0
oldEdate = None

logPath = os.getcwd() + '/tmp/panelExec.log'
isTask = os.getcwd() + '/tmp/panelTask.pl'

if not os.path.exists(os.getcwd() + "/tmp"):
    os.system('mkdir -p ' + os.getcwd() + "/tmp")

if not os.path.exists(logPath):
    os.system("touch " + logPath)


def service_cmd(method):
    cmd = '/etc/init.d/slemp'
    if os.path.exists(cmd):
        execShell(cmd + ' ' + method)
        return

    cmd = slemp.getRunDir() + '/scripts/init.d/slemp'
    if os.path.exists(cmd):
        execShell(cmd + ' ' + method)
        return


def slemp_async(f):
    def wrapper(*args, **kwargs):
        thr = threading.Thread(target=f, args=args, kwargs=kwargs)
        thr.start()
    return wrapper


@slemp_async
def restartSlemp():
    time.sleep(1)
    cmd = slemp.getRunDir() + '/scripts/init.d/slemp reload &'
    slemp.execShell(cmd)


def execShell(cmdstring, cwd=None, timeout=None, shell=True):
    try:
        global logPath
        import shlex
        import datetime
        import subprocess

        if timeout:
            end_time = datetime.datetime.now() + datetime.timedelta(seconds=timeout)

        cmd = cmdstring + ' > ' + logPath + ' 2>&1'
        sub = subprocess.Popen(
            cmd, cwd=cwd, stdin=subprocess.PIPE, shell=shell, bufsize=4096)
        while sub.poll() is None:
            time.sleep(0.1)

        data = sub.communicate()
        if isinstance(data[0], bytes):
            t1 = str(data[0], encoding='utf-8')

        if isinstance(data[1], bytes):
            t2 = str(data[1], encoding='utf-8')
        return (t1, t2)
    except Exception as e:
        return (None, None)


def downloadFile(url, filename):
    try:
        import urllib
        import socket
        socket.setdefaulttimeout(60)
        urllib.request.urlretrieve(
            url, filename=filename, reporthook=downloadHook)

        if not slemp.isAppleSystem():
            os.system('chown www.www ' + filename)

        writeLogs('done')
    except Exception as e:
        writeLogs(str(e))


def downloadHook(count, blockSize, totalSize):
    global pre
    used = count * blockSize
    pre1 = int((100.0 * used / totalSize))
    if pre == (100 - pre1):
        return
    speed = {'total': totalSize, 'used': used, 'pre': pre1}
    writeLogs(json.dumps(speed))


def writeLogs(logMsg):
    try:
        global logPath
        fp = open(logPath, 'w+')
        fp.write(logMsg)
        fp.close()
    except:
        pass


def runTask():
    global isTask
    try:
        if os.path.exists(isTask):
            sql = db.Sql()
            sql.table('tasks').where(
                "status=?", ('-1',)).setField('status', '0')
            taskArr = sql.table('tasks').where("status=?", ('0',)).field(
                'id,type,execstr').order("id asc").select()
            for value in taskArr:
                start = int(time.time())
                if not sql.table('tasks').where("id=?", (value['id'],)).count():
                    continue
                sql.table('tasks').where("id=?", (value['id'],)).save(
                    'status,start', ('-1', start))
                if value['type'] == 'download':
                    argv = value['execstr'].split('|slemp|')
                    downloadFile(argv[0], argv[1])
                elif value['type'] == 'execshell':
                    execShell(value['execstr'])
                end = int(time.time())
                sql.table('tasks').where("id=?", (value['id'],)).save(
                    'status,end', ('1', end))

                if(sql.table('tasks').where("status=?", ('0')).count() < 1):
                    os.system('rm -f ' + isTask)

            sql.close()
    except Exception as e:
        print(str(e))

    siteEdate()


def startTask():
    try:
        while True:
            runTask()
            time.sleep(2)
    except Exception as e:
        time.sleep(60)
        startTask()


def siteEdate():
    global oldEdate
    try:
        if not oldEdate:
            oldEdate = slemp.readFile('data/edate.pl')
        if not oldEdate:
            oldEdate = '0000-00-00'
        mEdate = time.strftime('%Y-%m-%d', time.localtime())
        if oldEdate == mEdate:
            return False
        edateSites = slemp.M('sites').where('edate>? AND edate<? AND (status=? OR status=?)',
                                         ('0000-00-00', mEdate, 1, 'running')).field('id,name').select()
        import site_api
        for site in edateSites:
            site_api.site_api().stop(site['id'], site['name'])
        oldEdate = mEdate
        slemp.writeFile('data/edate.pl', mEdate)
    except Exception as e:
        print(str(e))


def systemTask():
    try:
        import system_api
        import psutil
        sm = system_api.system_api()
        filename = 'data/control.conf'

        sql = db.Sql().dbfile('system')
        csql = slemp.readFile('data/sql/system.sql')
        csql_list = csql.split(';')
        for index in range(len(csql_list)):
            sql.execute(csql_list[index], ())

        cpuIo = cpu = {}
        cpuCount = psutil.cpu_count()
        used = count = 0
        reloadNum = 0
        network_up = network_down = diskio_1 = diskio_2 = networkInfo = cpuInfo = diskInfo = None
        while True:
            if not os.path.exists(filename):
                time.sleep(10)
                continue

            day = 30
            try:
                day = int(slemp.readFile(filename))
                if day < 1:
                    time.sleep(10)
                    continue
            except:
                day = 30

            tmp = {}
            tmp['used'] = psutil.cpu_percent(interval=1)

            if not cpuInfo:
                tmp['mem'] = sm.getMemUsed()
                cpuInfo = tmp

            if cpuInfo['used'] < tmp['used']:
                tmp['mem'] = sm.getMemUsed()
                cpuInfo = tmp

            networkIo = psutil.net_io_counters()[:4]
            if not network_up:
                network_up = networkIo[0]
                network_down = networkIo[1]
            tmp = {}
            tmp['upTotal'] = networkIo[0]
            tmp['downTotal'] = networkIo[1]
            tmp['up'] = round(float((networkIo[0] - network_up) / 1024), 2)
            tmp['down'] = round(float((networkIo[1] - network_down) / 1024), 2)
            tmp['downPackets'] = networkIo[3]
            tmp['upPackets'] = networkIo[2]

            network_up = networkIo[0]
            network_down = networkIo[1]

            if not networkInfo:
                networkInfo = tmp
            if (tmp['up'] + tmp['down']) > (networkInfo['up'] + networkInfo['down']):
                networkInfo = tmp
            diskio_2 = psutil.disk_io_counters()
            if not diskio_1:
                diskio_1 = diskio_2
            tmp = {}
            tmp['read_count'] = diskio_2.read_count - diskio_1.read_count
            tmp['write_count'] = diskio_2.write_count - diskio_1.write_count
            tmp['read_bytes'] = diskio_2.read_bytes - diskio_1.read_bytes
            tmp['write_bytes'] = diskio_2.write_bytes - diskio_1.write_bytes
            tmp['read_time'] = diskio_2.read_time - diskio_1.read_time
            tmp['write_time'] = diskio_2.write_time - diskio_1.write_time

            if not diskInfo:
                diskInfo = tmp
            else:
                diskInfo['read_count'] += tmp['read_count']
                diskInfo['write_count'] += tmp['write_count']
                diskInfo['read_bytes'] += tmp['read_bytes']
                diskInfo['write_bytes'] += tmp['write_bytes']
                diskInfo['read_time'] += tmp['read_time']
                diskInfo['write_time'] += tmp['write_time']
            diskio_1 = diskio_2

            if count >= 12:
                try:
                    addtime = int(time.time())
                    deltime = addtime - (day * 86400)

                    data = (cpuInfo['used'], cpuInfo['mem'], addtime)
                    sql.table('cpuio').add('pro,mem,addtime', data)
                    sql.table('cpuio').where("addtime<?", (deltime,)).delete()

                    data = (networkInfo['up'] / 5, networkInfo['down'] / 5, networkInfo['upTotal'], networkInfo[
                        'downTotal'], networkInfo['downPackets'], networkInfo['upPackets'], addtime)
                    sql.table('network').add(
                        'up,down,total_up,total_down,down_packets,up_packets,addtime', data)
                    sql.table('network').where(
                        "addtime<?", (deltime,)).delete()
                    # if os.path.exists('/proc/diskstats'):
                    data = (diskInfo['read_count'], diskInfo['write_count'], diskInfo['read_bytes'], diskInfo[
                        'write_bytes'], diskInfo['read_time'], diskInfo['write_time'], addtime)
                    sql.table('diskio').add(
                        'read_count,write_count,read_bytes,write_bytes,read_time,write_time,addtime', data)
                    sql.table('diskio').where(
                        "addtime<?", (deltime,)).delete()

                    # LoadAverage
                    load_average = sm.getLoadAverage()
                    lpro = round(
                        (load_average['one'] / load_average['max']) * 100, 2)
                    if lpro > 100:
                        lpro = 100
                    sql.table('load_average').add('pro,one,five,fifteen,addtime', (lpro, load_average[
                        'one'], load_average['five'], load_average['fifteen'], addtime))

                    lpro = None
                    load_average = None
                    cpuInfo = None
                    networkInfo = None
                    diskInfo = None
                    count = 0
                    reloadNum += 1
                    if reloadNum > 1440:
                        reloadNum = 0
                        slemp.writeFile('logs/sys_interrupt.pl',
                                     "reload num:" + str(reloadNum))
                        restartSlemp()
                except Exception as ex:
                    print(str(ex))
                    slemp.writeFile('logs/sys_interrupt.pl', str(ex))

            del(tmp)
            time.sleep(5)
            count += 1
    except Exception as ex:
        print(str(ex))
        slemp.writeFile('logs/sys_interrupt.pl', str(ex))

        restartSlemp()

        time.sleep(30)
        systemTask()


def check502Task():
    try:
        while True:
            if os.path.exists(slemp.getRunDir() + '/data/502Task.pl'):
                check502()
            time.sleep(30)
    except:
        time.sleep(30)
        check502Task()


def check502():
    try:
        verlist = ['52', '53', '54', '55', '56', '70',
                   '71', '72', '73', '74', '80', '81']
        for ver in verlist:
            sdir = slemp.getServerDir()
            php_path = sdir + '/php/' + ver + '/sbin/php-fpm'
            if not os.path.exists(php_path):
                continue
            if checkPHPVersion(ver):
                continue
            if startPHPVersion(ver):
                print('PHP-'+ver+' processing exception detected, fixed automatically!')
                slemp.writeLog('PHP daemon', 'Detected PHP-' + ver + ' handling exception, fixed automatically!')
    except Exception as e:
        print(str(e))


def startPHPVersion(version):
    sdir = slemp.getServerDir()
    try:

        # system
        phpService = slemp.systemdCfgDir() + '/php' + version + '.service'
        if os.path.exists(phpService):
            slemp.execShell("systemctl restart php" + version)
            if checkPHPVersion(version):
                return True

        # initd
        fpm = sdir + '/php/init.d/php' + version
        php_path = sdir + '/php/' + version + '/sbin/php-fpm'
        if not os.path.exists(php_path):
            if os.path.exists(fpm):
                os.remove(fpm)
            return False

        if not os.path.exists(fpm):
            return False

        os.system(fpm + ' reload')
        if checkPHPVersion(version):
            return True

        cgi = '/tmp/php-cgi-' + version + '.sock'
        pid = sdir + '/php/' + version + '/var/run/php-fpm.pid'
        data = slemp.execShell("ps -ef | grep php/" + version +
                            " | grep -v grep|grep -v python |awk '{print $2}'")
        if data[0] != '':
            os.system("ps -ef | grep php/" + version +
                      " | grep -v grep|grep -v python |awk '{print $2}' | xargs kill ")
        time.sleep(0.5)
        if not os.path.exists(cgi):
            os.system('rm -f ' + cgi)
        if not os.path.exists(pid):
            os.system('rm -f ' + pid)
        os.system(fpm + ' start')
        if checkPHPVersion(version):
            return True

        if os.path.exists(cgi):
            return True
    except Exception as e:
        print(str(e))
        return True


def getFpmConfFile(version):
    return slemp.getServerDir() + '/php/' + version + '/etc/php-fpm.d/www.conf'


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


def checkPHPVersion(version):
    try:
        sock = getFpmAddress(version)
        data = slemp.requestFcgiPHP(sock, '/phpfpm_status_' + version + '?json')
        result = str(data, encoding='utf-8')
    except Exception as e:
        result = 'Bad Gateway'

    if result.find('Bad Gateway') != -1:
        return False
    if result.find('HTTP Error 404: Not Found') != -1:
        return False

    if result.find('Connection refused') != -1:
        global isTask
        if os.path.exists(isTask):
            isStatus = slemp.readFile(isTask)
            if isStatus == 'True':
                return True

        # systemd
        systemd = slemp.systemdCfgDir() + '/openresty.service'
        if os.path.exists(systemd):
            execShell('systemctl reload openresty')
            return True
        # initd
        initd = '/etc/init.d/openresty'
        if os.path.exists(initd):
            os.system(initd + ' reload')
    return True

def openrestyAutoRestart():
    try:
        while True:
            odir = slemp.getServerDir() + '/openresty'
            if not os.path.exists(odir):
                time.sleep(86400)
                continue

            # systemd
            systemd = '/lib/systemd/system/openresty.service'
            initd = '/etc/init.d/openresty'
            if os.path.exists(systemd):
                execShell('systemctl reload openresty')
            elif os.path.exists(initd):
                os.system(initd + ' reload')
            time.sleep(86400)
    except Exception as e:
        print(str(e))
        time.sleep(86400)

def restartPanelService():
    restartTip = 'data/restart.pl'
    while True:
        if os.path.exists(restartTip):
            os.remove(restartTip)
            service_cmd('restart_panel')
        time.sleep(1)

def setDaemon(t):
    if sys.version_info.major == 3 and sys.version_info.minor >= 10:
        t.daemon = True
    else:
        t.setDaemon(True)
    return t

if __name__ == "__main__":

    sysTask = threading.Thread(target=systemTask)
    sysTask = setDaemon(sysTask)
    sysTask.start()

    php502 = threading.Thread(target=check502Task)
    php502 = setDaemon(php502)
    php502.start()

    oar = threading.Thread(target=openrestyAutoRestart)
    oar = setDaemon(oar)
    oar.start()

    rps = threading.Thread(target=restartPanelService)
    rps = setDaemon(rps)
    rps.start()

    startTask()
