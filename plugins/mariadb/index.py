# coding:utf-8

import sys
import io
import os
import time
import subprocess
import re
import json


# reload(sys)
# sys.setdefaultencoding('utf-8')

sys.path.append(os.getcwd() + "/class/core")
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
    return 'mariadb'


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
            return (False, slemp.returnJson(False, 'Parameter:(' + ck[i] + ') none!'))
    return (True, slemp.returnJson(True, 'ok'))


def getBackupDir():
    bk_path = slemp.getBackupDir() + "/database/mariadb"
    if not os.path.isdir(bk_path):
        slemp.execShell("mkdir -p {}".format(bk_path))
    return bk_path


def getConf():
    path = getServerDir() + '/etc/my.cnf'
    return path


def getDataDir():
    file = getConf()
    content = slemp.readFile(file)
    rep = 'datadir\s*=\s*(.*)'
    tmp = re.search(rep, content)
    return tmp.groups()[0].strip()


def getPidFile():
    file = getConf()
    content = slemp.readFile(file)
    rep = 'pid-file\s*=\s*(.*)'
    tmp = re.search(rep, content)
    return tmp.groups()[0].strip()


def getDbPort():
    file = getConf()
    content = slemp.readFile(file)
    rep = 'port\s*=\s*(.*)'
    tmp = re.search(rep, content)
    return tmp.groups()[0].strip()


def getSocketFile():
    file = getConf()
    content = slemp.readFile(file)
    rep = 'socket\s*=\s*(.*)'
    tmp = re.search(rep, content)
    return tmp.groups()[0].strip()


def getInitdTpl(version=''):
    path = getPluginDir() + '/init.d/mariadb' + version + '.tpl'
    if not os.path.exists(path):
        path = getPluginDir() + '/init.d/mariadb.tpl'
    return path


def contentReplace(content):
    service_path = slemp.getServerDir()
    content = content.replace('{$ROOT_PATH}', slemp.getRootDir())
    content = content.replace('{$SERVER_PATH}', service_path)
    content = content.replace('{$SERVER_APP_PATH}', service_path + '/mariadb')
    server_id = int(time.time())
    content = content.replace('{$SERVER_ID}', str(server_id))

    if slemp.isAppleSystem():
        user = slemp.execShell(
            "who | sed -n '2, 1p' |awk '{print $1}'")[0].strip()
        content = content.replace('user = mysql', 'user = ' + user)
    return content


def pSqliteDb(dbname='databases'):
    file = getServerDir() + '/mariadb.db'
    name = 'mysql'

    import_sql = slemp.readFile(getPluginDir() + '/conf/mariadb.sql')
    md5_sql = slemp.md5(import_sql)

    import_sign = False
    save_md5_file = getServerDir() + '/import_sql.md5'
    if os.path.exists(save_md5_file):
        save_md5_sql = slemp.readFile(save_md5_file)
        if save_md5_sql != md5_sql:
            import_sign = True
            slemp.writeFile(save_md5_file, md5_sql)
    else:
        slemp.writeFile(save_md5_file, md5_sql)

    if not os.path.exists(file) or import_sql:
        conn = slemp.M(dbname).dbPos(getServerDir(), name)
        csql_list = import_sql.split(';')
        for index in range(len(csql_list)):
            conn.execute(csql_list[index], ())

    conn = slemp.M(dbname).dbPos(getServerDir(), name)
    return conn


def pMysqlDb(name=''):
    # pymysql
    db = slemp.getMyORM()
    # MySQLdb |
    # db = slemp.getMyORMDb()

    db.setDbConf(getConf())
    db.setPort(getDbPort())
    db.setSocket(getSocketFile())
    db.setDbName(name)

    pwd = pSqliteDb('config').where('id=?', (1,)).getField('mysql_root')
    db.setPwd(pwd)
    return db


def makeInitRsaKey(version=''):
    datadir = getServerDir() + "/data"

    mysql_pem = datadir + "/mysql.pem"
    if not os.path.exists(mysql_pem):
        rdata = slemp.execShell(
            'cd ' + datadir + ' && openssl genrsa -out mysql.pem 1024')
        # print(data)
        rdata = slemp.execShell(
            'cd ' + datadir + ' && openssl rsa -in mysql.pem -pubout -out mysql.pub')
        # print(rdata)

        if not slemp.isAppleSystem():
            slemp.execShell('cd ' + datadir + ' && chmod 400 mysql.pem')
            slemp.execShell('cd ' + datadir + ' && chmod 444 mysql.pub')
            slemp.execShell('cd ' + datadir + ' && chown mysql:mysql mysql.pem')
            slemp.execShell('cd ' + datadir + ' && chown mysql:mysql mysql.pub')


def initDreplace(version=''):
    initd_tpl = getInitdTpl(version)

    mysql_conf_dir = getServerDir() + '/etc'
    if not os.path.exists(mysql_conf_dir):
        os.mkdir(mysql_conf_dir)

    mysql_conf = mysql_conf_dir + '/my.cnf'
    if not os.path.exists(mysql_conf):
        mysql_conf_tpl = getPluginDir() + '/conf/my.cnf'
        content = slemp.readFile(mysql_conf_tpl)
        content = contentReplace(content)
        slemp.writeFile(mysql_conf, content)

    initD_path = getServerDir() + '/init.d'
    if not os.path.exists(initD_path):
        os.mkdir(initD_path)

    file_bin = initD_path + '/' + getPluginName()
    if not os.path.exists(file_bin):
        content = slemp.readFile(initd_tpl)
        content = contentReplace(content)
        slemp.writeFile(file_bin, content)
        slemp.execShell('chmod +x ' + file_bin)

    mysql_tmp = getServerDir() + '/tmp'
    if not os.path.exists(mysql_tmp):
        os.mkdir(mysql_tmp)
        slemp.execShell("chown -R mysql:mysql " + mysql_tmp)

    # systemd
    systemDir = slemp.systemdCfgDir()
    systemService = systemDir + '/mariadb.service'
    systemServiceTpl = getPluginDir() + '/init.d/mariadb.service.tpl'
    if os.path.exists(systemDir) and not os.path.exists(systemService):
        service_path = slemp.getServerDir()
        se_content = slemp.readFile(systemServiceTpl)
        se_content = se_content.replace('{$SERVER_PATH}', service_path)
        slemp.writeFile(systemService, se_content)
        slemp.execShell('systemctl daemon-reload')

    if slemp.getOs() != 'darwin':
        slemp.execShell('chown -R mysql mysql ' + getServerDir())
    return file_bin


def status(version=''):
    try:
        pid = getPidFile()
        if os.path.exists(pid):
            return 'start'
    except Exception as e:
        return 'stop'
    return 'stop'


def binLog():
    args = getArgs()
    conf = getConf()
    con = slemp.readFile(conf)

    if con.find('#log-bin=mysql-bin') != -1:
        if 'status' in args:
            return slemp.returnJson(False, '0')
        con = con.replace('#log-bin=mysql-bin', 'log-bin=mysql-bin')
        con = con.replace('#binlog_format=mixed', 'binlog_format=mixed')
        slemp.execShell('sync')
        restart()
    else:
        path = getDataDir()
        if 'status' in args:
            dsize = 0
            for n in os.listdir(path):
                if len(n) < 9:
                    continue
                if n[0:9] == 'mysql-bin':
                    dsize += os.path.getsize(path + '/' + n)
            return slemp.returnJson(True, dsize)
        con = con.replace('log-bin=mysql-bin', '#log-bin=mysql-bin')
        con = con.replace('binlog_format=mixed', '#binlog_format=mixed')
        slemp.execShell('sync')
        restart()
        slemp.execShell('rm -f ' + path + '/mysql-bin.*')

    slemp.writeFile(conf, con)
    return slemp.returnJson(True, 'Successfully set!')


def cleanBinLog():
    db = pMysqlDb()
    cleanTime = time.strftime('%Y-%m-%d %H:%i:%s', time.localtime())
    db.execute("PURGE MASTER LOGS BEFORE '" + cleanTime + "';")
    return slemp.returnJson(True, 'Cleared BINLOG successfully!')


def setSkipGrantTables(v):
    '''
    Set whether password verification
    '''
    conf = getConf()
    con = slemp.readFile(conf)
    if v:
        if con.find('#skip-grant-tables') != -1:
            con = con.replace('#skip-grant-tables', 'skip-grant-tables')
    else:
        con = con.replace('skip-grant-tables', '#skip-grant-tables')
    slemp.writeFile(conf, con)
    return True


def getErrorLog():
    args = getArgs()
    path = getDataDir()
    filename = ''
    for n in os.listdir(path):
        if len(n) < 5:
            continue
        if n == 'error.log':
            filename = path + '/' + n
            break
    # print filename
    if not os.path.exists(filename):
        return slemp.returnJson(False, 'The specified file does not exist!')
    if 'close' in args:
        slemp.writeFile(filename, '')
        return slemp.returnJson(False, 'Log has been cleared')
    info = slemp.getLastLine(filename, 18)
    return slemp.returnJson(True, 'OK', info)


def getShowLogFile():
    file = getConf()
    content = slemp.readFile(file)
    rep = 'slow-query-log-file\s*=\s*(.*)'
    tmp = re.search(rep, content)
    return tmp.groups()[0].strip()


def pGetDbUser():
    if slemp.isAppleSystem():
        user = slemp.execShell(
            "who | sed -n '2, 1p' |awk '{print $1}'")[0].strip()
        return user
    return 'mysql'


def initMysqlData():
    datadir = getDataDir()
    if not os.path.exists(datadir + '/mysql'):
        serverdir = getServerDir()
        myconf = serverdir + "/etc/my.cnf"
        user = pGetDbUser()
        cmd = 'cd ' + serverdir + ' && ./scripts/mariadb-install-db ' + \
            ' --defaults-file=' + myconf
        data = slemp.execShell(cmd)
        # print(data[0])
        # print(data[1])

        if not slemp.isAppleSystem():
            slemp.execShell('chown -R mysql:mysql ' + serverdir + '/data')
            slemp.execShell('chmod -R 755 ' + serverdir + '/data')
        return False
    return True


def initMariaDbPwd():
    time.sleep(5)

    serverdir = getServerDir()
    myconf = serverdir + "/etc/my.cnf"
    pwd = slemp.getRandomString(16)

    db_option = "-S " + serverdir + "/mysql.sock"
    cmd_pass = serverdir + '/bin/mysql ' + db_option + ' -uroot -e'
    cmd_pass = cmd_pass + \
        "\"flush privileges;use mysql;grant all privileges on *.* to 'root'@'localhost' identified by '" + pwd + "';"
    cmd_pass = cmd_pass + "flush privileges;\""

    # print(cmd_pass)
    data = slemp.execShell(cmd_pass)
    # print(data)
    if data[1].find("ERROR") != -1:
        print("init mariadb password fail:" + data[1])
        exit(1)

    drop_empty_user = serverdir + '/bin/mysql ' + db_option + '-uroot -p' + \
        pwd + ' -e "use mysql;delete from user where USER=\'\'"'
    slemp.execShell(drop_empty_user)

    drop_test_db = serverdir + '/bin/mysql ' + db_option + ' -uroot -p' + \
        pwd + ' -e "drop database test";'
    slemp.execShell(drop_test_db)

    hostname = slemp.execShell('hostname')[0].strip()
    if hostname != 'localhost':
        drop_hostname =  serverdir + '/bin/mysql  --defaults-file=' + \
            myconf + ' -uroot -p' + pwd + ' -e "drop user \'\'@\'' + hostname + '\'";'
        slemp.execShell(drop_hostname)

        drop_root_hostname =  serverdir + '/bin/mysql  --defaults-file=' + \
            myconf + ' -uroot -p' + pwd + ' -e "drop user \'root\'@\'' + hostname + '\'";'
        slemp.execShell(drop_root_hostname)

    pSqliteDb('config').where('id=?', (1,)).save('mysql_root', (pwd,))
    return True


def myOp(version, method):
    # import commands
    init_file = initDreplace()
    cmd = init_file + ' ' + method
    try:
        isInited = initMysqlData()
        if not isInited:
            if slemp.isAppleSystem():
                setSkipGrantTables(True)
                cmd_init_start = init_file + ' start'
                subprocess.Popen(cmd_init_start, stdout=subprocess.PIPE, shell=True,
                                 bufsize=4096, stderr=subprocess.PIPE)

                time.sleep(6)
            else:
                slemp.execShell('systemctl start mariadb')

            initMariaDbPwd()

            if slemp.isAppleSystem():
                setSkipGrantTables(False)
                cmd_init_stop = init_file + ' stop'
                subprocess.Popen(cmd_init_stop, stdout=subprocess.PIPE, shell=True,
                                 bufsize=4096, stderr=subprocess.PIPE)
                time.sleep(3)
            else:
                slemp.execShell('systemctl stop mariadb')

        if slemp.isAppleSystem():
            print
            sub = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True,
                                   bufsize=4096, stderr=subprocess.PIPE)
            sub.wait(5)
        else:
            slemp.execShell('systemctl ' + method + ' mariadb')

        return 'ok'
    except Exception as e:
        return str(e)


def appCMD(version, action):
    makeInitRsaKey(version)
    return myOp(version, action)


def start(version=''):
    return appCMD(version, 'start')


def stop(version=''):
    return appCMD(version, 'stop')


def restart(version=''):
    return appCMD(version, 'restart')


def reload(version=''):
    return appCMD(version, 'reload')


def initdStatus():
    if slemp.isAppleSystem():
        return "Apple Computer does not support"

    shell_cmd = 'systemctl status mariadb | grep loaded | grep "enabled;"'
    data = slemp.execShell(shell_cmd)
    if data[0] == '':
        return 'fail'
    return 'ok'


def initdInstall():
    if slemp.isAppleSystem():
        return "Apple Computer does not support"

    slemp.execShell('systemctl enable mariadb')
    return 'ok'


def initdUinstall():
    if slemp.isAppleSystem():
        return "Apple Computer does not support"

    slemp.execShell('systemctl disable mariadb')
    return 'ok'


def getMyDbPos():
    file = getConf()
    content = slemp.readFile(file)
    rep = 'datadir\s*=\s*(.*)'
    tmp = re.search(rep, content)
    return tmp.groups()[0].strip()


def setMyDbPos():
    args = getArgs()
    data = checkArgs(args, ['datadir'])
    if not data[0]:
        return data[1]

    s_datadir = getMyDbPos()
    t_datadir = args['datadir']
    if t_datadir == s_datadir:
        return slemp.returnJson(False, 'Same as the current storage directory, unable to migrate files!')

    if not os.path.exists(t_datadir):
        slemp.execShell('mkdir -p ' + t_datadir)

    stop()
    slemp.execShell('cp -rf ' + s_datadir + '/* ' + t_datadir + '/')
    slemp.execShell('chown -R mysql mysql ' + t_datadir)
    slemp.execShell('chmod -R 755 ' + t_datadir)
    slemp.execShell('rm -f ' + t_datadir + '/*.pid')
    slemp.execShell('rm -f ' + t_datadir + '/*.err')

    path = getServerDir()
    myfile = path + '/etc/my.cnf'
    mycnf = slemp.readFile(myfile)
    slemp.writeFile(path + '/etc/my_backup.cnf', mycnf)

    mycnf = mycnf.replace(s_datadir, t_datadir)
    slemp.writeFile(myfile, mycnf)
    start()

    result = slemp.execShell(
        'ps aux|grep mysqld| grep -v grep|grep -v python')
    if len(result[0]) > 10:
        slemp.writeFile('data/datadir.pl', t_datadir)
        return slemp.returnJson(True, 'Storage directory migrated successfully!')
    else:
        slemp.execShell('pkill -9 mysqld')
        slemp.writeFile(myfile, slemp.readFile(path + '/etc/my_backup.cnf'))
        start()
        return slemp.returnJson(False, 'File migration failed!')


def getMyPort():
    file = getConf()
    content = slemp.readFile(file)
    rep = 'port\s*=\s*(.*)'
    tmp = re.search(rep, content)
    return tmp.groups()[0].strip()


def setMyPort():
    args = getArgs()
    data = checkArgs(args, ['port'])
    if not data[0]:
        return data[1]

    port = args['port']
    file = getConf()
    content = slemp.readFile(file)
    rep = "port\s*=\s*([0-9]+)\s*\n"
    content = re.sub(rep, 'port = ' + port + '\n', content)
    slemp.writeFile(file, content)
    restart()
    return slemp.returnJson(True, 'Edited successfully!')


def runInfo(version):

    if status(version) == 'stop':
        return slemp.returnJson(False, 'MySQL is not started', [])

    db = pMysqlDb()
    data = db.query('show global status')
    isError = isSqlError(data)
    if isError != None:
        return isError

    gets = ['Max_used_connections', 'Com_commit', 'Com_rollback', 'Questions', 'Innodb_buffer_pool_reads', 'Innodb_buffer_pool_read_requests', 'Key_reads', 'Key_read_requests', 'Key_writes',
            'Key_write_requests', 'Qcache_hits', 'Qcache_inserts', 'Bytes_received', 'Bytes_sent', 'Aborted_clients', 'Aborted_connects',
            'Created_tmp_disk_tables', 'Created_tmp_tables', 'Innodb_buffer_pool_pages_dirty', 'Opened_files', 'Open_tables', 'Opened_tables', 'Select_full_join',
            'Select_range_check', 'Sort_merge_passes', 'Table_locks_waited', 'Threads_cached', 'Threads_connected', 'Threads_created', 'Threads_running', 'Connections', 'Uptime']

    result = {}
    # print(data)
    for d in data:
        vname = d["Variable_name"]
        for g in gets:
            if vname == g:
                result[g] = d["Value"]

    # print(result, int(result['Uptime']))
    result['Run'] = int(time.time()) - int(result['Uptime'])
    tmp = db.query('show master status')
    try:
        result['File'] = tmp[0]["File"]
        result['Position'] = tmp[0]["Position"]
    except:
        result['File'] = 'OFF'
        result['Position'] = 'OFF'
    return slemp.getJson(result)


def myDbStatus():
    result = {}
    db = pMysqlDb()
    data = db.query('show variables')
    isError = isSqlError(data)
    if isError != None:
        return isError

    gets = ['table_open_cache', 'thread_cache_size', 'key_buffer_size', 'tmp_table_size', 'max_heap_table_size', 'innodb_buffer_pool_size',
            'innodb_additional_mem_pool_size', 'innodb_log_buffer_size', 'max_connections', 'sort_buffer_size', 'read_buffer_size', 'read_rnd_buffer_size', 'join_buffer_size', 'thread_stack', 'binlog_cache_size']
    result['mem'] = {}
    for d in data:
        vname = d['Variable_name']
        for g in gets:
            # print(g)
            if vname == g:
                result['mem'][g] = d["Value"]
    return slemp.getJson(result)


def setDbStatus():
    gets = ['key_buffer_size', 'tmp_table_size', 'max_heap_table_size', 'innodb_buffer_pool_size', 'innodb_log_buffer_size', 'max_connections',
            'table_open_cache', 'thread_cache_size', 'sort_buffer_size', 'read_buffer_size', 'read_rnd_buffer_size', 'join_buffer_size', 'thread_stack', 'binlog_cache_size']
    emptys = ['max_connections', 'thread_cache_size', 'table_open_cache']
    args = getArgs()
    conFile = getConf()
    content = slemp.readFile(conFile)
    n = 0
    for g in gets:
        s = 'M'
        if n > 5:
            s = 'K'
        if g in emptys:
            s = ''
        rep = '\s*' + g + '\s*=\s*\d+(M|K|k|m|G)?\n'
        c = g + ' = ' + args[g] + s + '\n'
        if content.find(g) != -1:
            content = re.sub(rep, '\n' + c, content, 1)
        else:
            content = content.replace('[mysqld]\n', '[mysqld]\n' + c)
        n += 1
    slemp.writeFile(conFile, content)
    return slemp.returnJson(True, 'Successfully set!')


def isSqlError(mysqlMsg):
    mysqlMsg = str(mysqlMsg)
    if "MySQLdb" in mysqlMsg:
        return slemp.returnJson(False, 'The MySQLdb component is missing! <br>Enter the SSH command line and enter: pip install mysql-python | pip install mysqlclient==2.0.3')
    if "2002," in mysqlMsg:
        return slemp.returnJson(False, 'The database connection failed, please check whether the database service is started!')
    if "2003," in mysqlMsg:
        return slemp.returnJson(False, "Can't connect to MySQL server on '127.0.0.1' (61)")
    if "using password:" in mysqlMsg:
        return slemp.returnJson(False, 'The database password is wrong, in the management list - click [Repair]!')
    if "1045" in mysqlMsg:
        return slemp.returnJson(False, 'Connection error!')
    if "SQL syntax" in mysqlMsg:
        return slemp.returnJson(False, 'SQL syntax error!')
    if "Connection refused" in mysqlMsg:
        return slemp.returnJson(False, 'The database connection failed, please check whether the database service is started!')
    if "1133" in mysqlMsg:
        return slemp.returnJson(False, 'Database user does not exist!')
    if "1007" in mysqlMsg:
        return slemp.returnJson(False, 'Database already exists!')
    return None


def __createUser(dbname, username, password, address):
    pdb = pMysqlDb('mysql')

    if username == 'root':
        dbname = '*'

    pdb.execute(
        "CREATE USER `%s`@`localhost` IDENTIFIED BY '%s'" % (username, password))
    pdb.execute(
        "grant all privileges on %s.* to `%s`@`localhost`" % (dbname, username))
    for a in address.split(','):
        pdb.execute(
            "CREATE USER `%s`@`%s` IDENTIFIED BY '%s'" % (username, a, password))
        pdb.execute(
            "grant all privileges on %s.* to `%s`@`%s`" % (dbname, username, a))
    pdb.execute("flush privileges")


def getDbBackupListFunc(dbname=''):
    bkDir = getBackupDir()
    blist = os.listdir(bkDir)
    r = []

    bname = 'db_' + dbname
    blen = len(bname)
    for x in blist:
        fbstr = x[0:blen]
        if fbstr == bname:
            r.append(x)
    return r


def setDbBackup():
    args = getArgs()
    data = checkArgs(args, ['name'])
    if not data[0]:
        return data[1]

    scDir = getPluginDir() + '/scripts/backup.py'
    cmd = 'python3 ' + scDir + ' database ' + args['name'] + ' 3'
    os.system(cmd)
    return slemp.returnJson(True, 'ok')


def importDbBackup():
    args = getArgs()
    data = checkArgs(args, ['file', 'name'])
    if not data[0]:
        return data[1]

    file = args['file']
    name = args['name']

    file_path = getBackupDir() + '/' + file
    file_path_sql = getBackupDir() + '/' + file.replace('.gz', '')

    if not os.path.exists(file_path_sql):
        cmd = 'cd ' + slemp.getBackupDir() + '/database/mariadb && gzip -d ' + file
        slemp.execShell(cmd)

    pwd = pSqliteDb('config').where('id=?', (1,)).getField('mysql_root')
    sock = getSocketFile()
    mysql_cmd = getServerDir() + '/bin/mysql -S ' + sock + ' -uroot -p' + pwd + \
        ' ' + name + ' < ' + file_path_sql

    # print(mysql_cmd)
    os.system(mysql_cmd)
    return slemp.returnJson(True, 'ok')


def importDbExternal():
    args = getArgs()
    data = checkArgs(args, ['file', 'name'])
    if not data[0]:
        return data[1]

    file = args['file']
    name = args['name']

    import_dir = slemp.getBackupDir() + '/import/'

    file_path = import_dir + file
    if not os.path.exists(file_path):
        return slemp.returnJson(False, 'File suddenly disappears?')

    exts = ['sql', 'gz', 'zip']
    tmp = file.split('.')
    ext = tmp[len(tmp) - 1]
    if ext not in exts:
        return slemp.returnJson(False, 'Import database format is wrong!')

    tmp = file.split('/')
    tmpFile = tmp[len(tmp) - 1]
    tmpFile = tmpFile.replace('.sql.' + ext, '.sql')
    tmpFile = tmpFile.replace('.' + ext, '.sql')
    tmpFile = tmpFile.replace('tar.', '')

    # print(tmpFile)
    import_sql = ""
    if file.find("sql.gz") > -1:
        cmd = 'cd ' + import_dir + ' && gzip -dc ' + \
            file + " > " + import_dir + tmpFile
        info = slemp.execShell(cmd)
        if info[1] == "":
            import_sql = import_dir + tmpFile

    if file.find(".zip") > -1:
        cmd = 'cd ' + import_dir + ' && unzip -o ' + file
        slemp.execShell(cmd)
        import_sql = import_dir + tmpFile

    if file.find("tar.gz") > -1:
        cmd = 'cd ' + import_dir + ' && tar -zxvf ' + file
        slemp.execShell(cmd)
        import_sql = import_dir + tmpFile

    if import_sql == "":
        return slemp.returnJson(False, 'SQL file not found')

    pwd = pSqliteDb('config').where('id=?', (1,)).getField('mysql_root')
    sock = getSocketFile()

    os.environ["MYSQL_PWD"] = pwd
    mysql_cmd = getServerDir() + '/bin/mysql -S ' + sock + ' -uroot -p' + \
        pwd + ' ' + name + ' < ' + import_sql

    # print(mysql_cmd)
    os.system(mysql_cmd)
    os.remove(import_sql)

    return slemp.returnJson(True, 'ok')


def deleteDbBackup():
    args = getArgs()
    data = checkArgs(args, ['filename', 'path'])
    if not data[0]:
        return data[1]

    path = args['path']
    full_file = ""
    bkDir = getBackupDir()
    full_file = bkDir + '/' + args['filename']
    if path != "":
        full_file = path + "/" + args['filename']
    os.remove(full_file)
    return slemp.returnJson(True, 'ok')


def getDbBackupList():
    args = getArgs()
    data = checkArgs(args, ['name'])
    if not data[0]:
        return data[1]

    r = getDbBackupListFunc(args['name'])
    bkDir = getBackupDir()
    if not os.path.exists(bkDir):
        os.mkdir(bkDir)

    rr = []
    for x in range(0, len(r)):
        p = bkDir + '/' + r[x]
        data = {}
        data['name'] = r[x]

        rsize = os.path.getsize(p)
        data['size'] = slemp.toSize(rsize)

        t = os.path.getctime(p)
        t = time.localtime(t)

        data['time'] = time.strftime('%Y-%m-%d %H:%M:%S', t)
        rr.append(data)

        data['file'] = p

    return slemp.returnJson(True, 'ok', rr)


def getDbBackupImportList():

    bkImportDir = slemp.getBackupDir() + '/import'
    if not os.path.exists(bkImportDir):
        os.mkdir(bkImportDir)

    blist = os.listdir(bkImportDir)

    rr = []
    for x in range(0, len(blist)):
        name = blist[x]
        p = bkImportDir + '/' + name
        data = {}
        data['name'] = name

        rsize = os.path.getsize(p)
        data['size'] = slemp.toSize(rsize)

        t = os.path.getctime(p)
        t = time.localtime(t)

        data['time'] = time.strftime('%Y-%m-%d %H:%M:%S', t)
        rr.append(data)

        data['file'] = p

    rdata = {
        "list": rr,
        "upload_dir": bkImportDir,
    }
    return slemp.returnJson(True, 'ok', rdata)


def getDbList():
    args = getArgs()
    page = 1
    page_size = 10
    search = ''
    data = {}
    if 'page' in args:
        page = int(args['page'])

    if 'page_size' in args:
        page_size = int(args['page_size'])

    if 'search' in args:
        search = args['search']

    conn = pSqliteDb('databases')
    limit = str((page - 1) * page_size) + ',' + str(page_size)
    condition = ''
    if not search == '':
        condition = "name like '%" + search + "%'"
    field = 'id,pid,name,username,password,accept,rw,ps,addtime'
    clist = conn.where(condition, ()).field(
        field).limit(limit).order('id desc').select()

    for x in range(0, len(clist)):
        dbname = clist[x]['name']
        blist = getDbBackupListFunc(dbname)
        # print(blist)
        clist[x]['is_backup'] = False
        if len(blist) > 0:
            clist[x]['is_backup'] = True

    count = conn.where(condition, ()).count()
    _page = {}
    _page['count'] = count
    _page['p'] = page
    _page['row'] = page_size
    _page['tojs'] = 'dbList'
    data['page'] = slemp.getPage(_page)
    data['data'] = clist

    info = {}
    info['root_pwd'] = pSqliteDb('config').where(
        'id=?', (1,)).getField('mysql_root')
    data['info'] = info

    return slemp.getJson(data)


def syncGetDatabases():
    pdb = pMysqlDb()
    psdb = pSqliteDb('databases')
    data = pdb.query('show databases')
    isError = isSqlError(data)
    if isError != None:
        return isError
    users = pdb.query(
        "select User,Host from user where User!='root' AND Host!='localhost' AND Host!=''")
    nameArr = ['information_schema', 'performance_schema', 'mysql', 'sys']
    n = 0

    # print(users)
    for value in data:
        vdb_name = value["Database"]
        b = False
        for key in nameArr:
            if vdb_name == key:
                b = True
                break
        if b:
            continue
        if psdb.where("name=?", (vdb_name,)).count() > 0:
            continue
        host = '127.0.0.1'
        for user in users:
            if vdb_name == user["User"]:
                host = user["Host"]
                break

        ps = slemp.getMsg('INPUT_PS')
        if vdb_name == 'test':
            ps = slemp.getMsg('DATABASE_TEST')
        addTime = time.strftime('%Y-%m-%d %X', time.localtime())
        if psdb.add('name,username,password,accept,ps,addtime', (vdb_name, vdb_name, '', host, ps, addTime)):
            n += 1

    msg = slemp.getInfo('A total of {1} databases have been obtained from the server this time!', (str(n),))
    return slemp.returnJson(True, msg)


def toDbBase(find):
    pdb = pMysqlDb()
    psdb = pSqliteDb('databases')
    if len(find['password']) < 3:
        find['username'] = find['name']
        find['password'] = slemp.md5(str(time.time()) + find['name'])[0:10]
        psdb.where("id=?", (find['id'],)).save(
            'password,username', (find['password'], find['username']))

    result = pdb.execute("create database `" + find['name'] + "`")
    if "using password:" in str(result):
        return -1
    if "Connection refused" in str(result):
        return -1

    password = find['password']
    __createUser(find['name'], find['username'], password, find['accept'])
    return 1


def syncToDatabases():
    args = getArgs()
    data = checkArgs(args, ['type', 'ids'])
    if not data[0]:
        return data[1]

    pdb = pMysqlDb()
    result = pdb.execute("show databases")
    isError = isSqlError(result)
    if isError:
        return isError

    stype = int(args['type'])
    psdb = pSqliteDb('databases')
    n = 0

    if stype == 0:
        data = psdb.field('id,name,username,password,accept').select()
        for value in data:
            result = toDbBase(value)
            if result == 1:
                n += 1
    else:
        data = json.loads(args['ids'])
        for value in data:
            find = psdb.where("id=?", (value,)).field(
                'id,name,username,password,accept').find()
            # print find
            result = toDbBase(find)
            if result == 1:
                n += 1
    msg = slemp.getInfo('{1} databases were synchronized this time!', (str(n),))
    return slemp.returnJson(True, msg)


def setRootPwd(version=''):
    args = getArgs()
    data = checkArgs(args, ['password'])
    if not data[0]:
        return data[1]

    password = args['password']
    try:
        pdb = pMysqlDb('mysql')
        result = pdb.query("show databases")
        isError = isSqlError(result)
        if isError != None:
            return isError

        cmd = "ALTER USER 'root'@'localhost' IDENTIFIED BY '" + password + "';"
        r = pdb.execute(cmd)
        # print(r)

        pSqliteDb('config').where('id=?', (1,)).save('mysql_root', (password,))
        orm = pMysqlDb()
        orm.execute("flush privileges")
        return slemp.returnJson(True, 'Database root password changed successfully!')
    except Exception as ex:
        return slemp.returnJson(False, 'Correct mistakes:' + str(ex))


def setUserPwd(version=''):
    args = getArgs()
    data = checkArgs(args, ['password', 'name', 'id'])
    if not data[0]:
        return data[1]

    newpassword = args['password']
    username = args['name']
    uid = args['id']
    try:
        pdb = pMysqlDb()
        psdb = pSqliteDb('databases')
        data = psdb.field('id,name,accept').where('id=?', (uid,)).find()

        cmd = "SET PASSWORD FOR '" + username + \
            "'@'localhost' = PASSWORD('" + newpassword + "')"
        r = pdb.execute(cmd)
        # print(cmd, r)

        accept = data['accept']
        alist = accept.split(',')
        for x in alist:
            cmd = "SET PASSWORD FOR '" + username + \
                "'@'" + x + "' = PASSWORD('" + newpassword + "')"
            r = pdb.execute(cmd)
            # print(cmd, r)

        psdb.where("id=?", (uid,)).setField('password', newpassword)

        orm = pMysqlDb()
        orm.execute("flush privileges")
        return slemp.returnJson(True, slemp.getInfo('Modify database [{1}] password successfully!', (data['name'],)))
    except Exception as ex:
        return slemp.returnJson(False, slemp.getInfo('Failed to modify database [{1}] password [{2}]!', (data['name'], str(ex),)))


def setDbPs():
    args = getArgs()
    data = checkArgs(args, ['id', 'name', 'ps'])
    if not data[0]:
        return data[1]

    ps = args['ps']
    sid = args['id']
    name = args['name']
    try:
        psdb = pSqliteDb('databases')
        psdb.where("id=?", (sid,)).setField('ps', ps)
        return slemp.returnJson(True, slemp.getInfo('Modify database [{1}] remarks successfully!', (name,)))
    except Exception as e:
        return slemp.returnJson(True, slemp.getInfo('Failed to modify database [{1}] comment!', (name,)))


def addDb():
    args = getArgs()
    data = checkArgs(args,
                     ['password', 'name', 'codeing', 'db_user', 'dataAccess', 'ps'])
    if not data[0]:
        return data[1]

    if not 'address' in args:
        address = ''
    else:
        address = args['address'].strip()

    dbname = args['name'].strip()
    dbuser = args['db_user'].strip()
    codeing = args['codeing'].strip()
    password = args['password'].strip()
    dataAccess = args['dataAccess'].strip()
    ps = args['ps'].strip()

    reg = "^[\w\.-]+$"
    if not re.match(reg, args['name']):
        return slemp.returnJson(False, 'Database names cannot have special symbols!')
    checks = ['root', 'mysql', 'test', 'sys', 'panel_logs']
    if dbuser in checks or len(dbuser) < 1:
        return slemp.returnJson(False, 'The database user name is invalid!')
    if dbname in checks or len(dbname) < 1:
        return slemp.returnJson(False, 'Invalid database name!')

    if len(password) < 1:
        password = slemp.md5(time.time())[0:8]

    wheres = {
        'utf8':   'utf8_general_ci',
        'utf8mb4': 'utf8mb4_general_ci',
        'gbk':    'gbk_chinese_ci',
        'big5':   'big5_chinese_ci'
    }
    codeStr = wheres[codeing]

    pdb = pMysqlDb()
    psdb = pSqliteDb('databases')

    if psdb.where("name=? or username=?", (dbname, dbuser)).count():
        return slemp.returnJson(False, 'Database already exists!')

    result = pdb.execute("create database `" + dbname +
                         "` DEFAULT CHARACTER SET " + codeing + " COLLATE " + codeStr)
    # print result
    isError = isSqlError(result)
    if isError != None:
        return isError

    pdb.execute("drop user '" + dbuser + "'@'localhost'")
    for a in address.split(','):
        pdb.execute("drop user '" + dbuser + "'@'" + a + "'")

    __createUser(dbname, dbuser, password, address)

    addTime = time.strftime('%Y-%m-%d %X', time.localtime())
    psdb.add('pid,name,username,password,accept,ps,addtime',
             (0, dbname, dbuser, password, address, ps, addTime))
    return slemp.returnJson(True, 'Added successfully!')


def delDb():
    args = getArgs()
    data = checkArgs(args, ['id', 'name'])
    if not data[0]:
        return data[1]
    try:
        id = args['id']
        name = args['name']
        psdb = pSqliteDb('databases')
        pdb = pMysqlDb('mysql')
        find = psdb.where("id=?", (id,)).field(
            'id,pid,name,username,password,accept,ps,addtime').find()
        accept = find['accept']
        username = find['username']

        result = pdb.execute("drop database `" + name + "`")

        users = pdb.query("select Host from user where User='" +
                          username + "' AND Host!='localhost'")
        pdb.execute("drop user '" + username + "'@'localhost'")
        for us in users:
            pdb.execute("drop user '" + username + "'@'" + us["Host"] + "'")
        pdb.execute("flush privileges")

        psdb.where("id=?", (id,)).delete()
        return slemp.returnJson(True, 'Successfully deleted!')
    except Exception as ex:
        return slemp.returnJson(False, 'Failed to delete!' + str(ex))


def getDbAccess():
    args = getArgs()
    data = checkArgs(args, ['username'])
    if not data[0]:
        return data[1]
    username = args['username']
    pdb = pMysqlDb('mysql')

    users = pdb.query("select Host from user where User='" +
                      username + "' AND Host!='localhost'")

    isError = isSqlError(users)
    if isError != None:
        return isError

    if len(users) < 1:
        return slemp.returnJson(True, "127.0.0.1")
    accs = []
    for c in users:
        accs.append(c["Host"])
    userStr = ','.join(accs)
    return slemp.returnJson(True, userStr)


def setDbAccess():
    args = getArgs()
    data = checkArgs(args, ['username', 'access'])
    if not data[0]:
        return data[1]
    name = args['username']
    access = args['access']
    pdb = pMysqlDb('mysql')
    psdb = pSqliteDb('databases')

    dbname = psdb.where('username=?', (name,)).getField('name')

    if name == 'root':
        password = pSqliteDb('config').where(
            'id=?', (1,)).getField('mysql_root')
    else:
        password = psdb.where("username=?", (name,)).getField('password')

    users = pdb.query("select Host from user where User='" +
                      name + "' AND Host!='localhost'")

    for us in users:
        pdb.execute("drop user '" + name + "'@'" + us["Host"] + "'")

    __createUser(dbname, name, password, access)

    psdb.where('username=?', (name,)).save('accept,rw', (access, 'rw',))
    return slemp.returnJson(True, 'Successfully set!')


def fixDbAccess(version):
    try:
        pdb = pMysqlDb()
        psdb = pSqliteDb('databases')
        data = pdb.query('show databases')
        isError = isSqlError(data)
        if isError != None:
            appCMD(version, 'stop')
            slemp.execShell("rm -rf " + getServerDir() + "/data")
            appCMD(version, 'start')
            return slemp.returnJson(True, 'Successful repair!')
        return slemp.returnJson(True, 'Normal without repair!')
    except Exception as e:
        return slemp.returnJson(False, 'Repair failed, please try again!')


def setDbRw(version=''):
    args = getArgs()
    data = checkArgs(args, ['username', 'id', 'rw'])
    if not data[0]:
        return data[1]

    username = args['username']
    uid = args['id']
    rw = args['rw']

    pdb = pMysqlDb('mysql')
    psdb = pSqliteDb('databases')
    dbname = psdb.where("id=?", (uid,)).getField('name')
    users = pdb.query(
        "select Host from user where User='" + username + "'")

    # show grants for demo@"127.0.0.1";
    for x in users:
        # REVOKE ALL PRIVILEGES ON `imail`.* FROM 'imail'@'127.0.0.1';

        sql = "REVOKE ALL PRIVILEGES ON `" + dbname + \
            "`.* FROM '" + username + "'@'" + x["Host"] + "';"
        r = pdb.query(sql)
        # print(sql, r)

        if rw == 'rw':
            sql = "GRANT SELECT, INSERT, UPDATE, DELETE ON " + dbname + ".* TO " + \
                username + "@'" + x["Host"] + "'"
        elif rw == 'r':
            sql = "GRANT SELECT ON " + dbname + ".* TO " + \
                username + "@'" + x["Host"] + "'"
        else:
            sql = "GRANT all privileges ON " + dbname + ".* TO " + \
                username + "@'" + x["Host"] + "'"
        pdb.execute(sql)
    pdb.execute("flush privileges")
    r = psdb.where("id=?", (uid,)).setField('rw', rw)
    # print(r)
    return slemp.returnJson(True, 'Switch successfully!')


def getDbInfo():
    args = getArgs()
    data = checkArgs(args, ['name'])
    if not data[0]:
        return data[1]

    db_name = args['name']
    pdb = pMysqlDb()
    # print 'show tables from `%s`' % db_name
    tables = pdb.query('show tables from `%s`' % db_name)

    ret = {}
    sql = "select sum(DATA_LENGTH)+sum(INDEX_LENGTH) as sum_size from information_schema.tables  where table_schema='%s'" % db_name
    data_sum = pdb.query(sql)

    data = 0
    if data_sum[0]['sum_size'] != None:
        data = data_sum[0]['sum_size']

    ret['data_size'] = slemp.toSize(data)
    ret['database'] = db_name

    ret3 = []
    table_key = "Tables_in_" + db_name
    for i in tables:
        tb_sql = "show table status from `%s` where name = '%s'" % (db_name, i[
                                                                    table_key])
        table = pdb.query(tb_sql)

        tmp = {}
        tmp['type'] = table[0]["Engine"]
        tmp['rows_count'] = table[0]["Rows"]
        tmp['collation'] = table[0]["Collation"]

        data_size = 0
        if table[0]['Avg_row_length'] != None:
            data_size = table[0]['Avg_row_length']

        if table[0]['Data_length'] != None:
            data_size = table[0]['Data_length']

        tmp['data_byte'] = data_size
        tmp['data_size'] = slemp.toSize(data_size)
        tmp['table_name'] = table[0]["Name"]
        ret3.append(tmp)

    ret['tables'] = (ret3)

    return slemp.getJson(ret)


def repairTable():
    args = getArgs()
    data = checkArgs(args, ['db_name', 'tables'])
    if not data[0]:
        return data[1]

    db_name = args['db_name']
    tables = json.loads(args['tables'])
    pdb = pMysqlDb()
    mtable = pdb.query('show tables from `%s`' % db_name)

    ret = []
    key = "Tables_in_" + db_name
    for i in mtable:
        for tn in tables:
            if tn == i[key]:
                ret.append(tn)

    if len(ret) > 0:
        for i in ret:
            pdb.execute('REPAIR TABLE `%s`.`%s`' % (db_name, i))
        return slemp.returnJson(True, "Repair completed!")
    return slemp.returnJson(False, "Repair failed!")


def optTable():
    args = getArgs()
    data = checkArgs(args, ['db_name', 'tables'])
    if not data[0]:
        return data[1]

    db_name = args['db_name']
    tables = json.loads(args['tables'])
    pdb = pMysqlDb()
    mtable = pdb.query('show tables from `%s`' % db_name)
    ret = []
    key = "Tables_in_" + db_name
    for i in mtable:
        for tn in tables:
            if tn == i[key]:
                ret.append(tn)

    if len(ret) > 0:
        for i in ret:
            pdb.execute('OPTIMIZE TABLE `%s`.`%s`' % (db_name, i))
        return slemp.returnJson(True, "Optimized successfully!")
    return slemp.returnJson(False, "Optimization failed or has already been optimized!")


def alterTable():
    args = getArgs()
    data = checkArgs(args, ['db_name', 'tables'])
    if not data[0]:
        return data[1]

    db_name = args['db_name']
    tables = json.loads(args['tables'])
    table_type = args['table_type']
    pdb = pMysqlDb()
    mtable = pdb.query('show tables from `%s`' % db_name)

    ret = []
    key = "Tables_in_" + db_name
    for i in mtable:
        for tn in tables:
            if tn == i[key]:
                ret.append(tn)

    if len(ret) > 0:
        for i in ret:
            pdb.execute('alter table `%s`.`%s` ENGINE=`%s`' %
                        (db_name, i, table_type))
        return slemp.returnJson(True, "Change successful!")
    return slemp.returnJson(False, "Change failed!")


def getTotalStatistics():
    st = status()
    data = {}

    isInstall = os.path.exists(getServerDir() + '/version.pl')

    if st == 'start' and isInstall:
        data['status'] = True
        data['count'] = pSqliteDb('databases').count()
        data['ver'] = slemp.readFile(getServerDir() + '/version.pl').strip()
        return slemp.returnJson(True, 'ok', data)
    else:
        data['status'] = False
        data['count'] = 0
        return slemp.returnJson(False, 'fail', data)


def recognizeDbMode():
    conf = getConf()
    con = slemp.readFile(conf)
    rep = r"!include %s/(.*)?\.cnf" % (getServerDir() + "/etc/mode",)
    mode = 'none'
    try:
        data = re.findall(rep, con, re.M)
        mode = data[0]
    except Exception as e:
        pass
    return mode


def getDbrunMode(version=''):
    mode = recognizeDbMode()
    return slemp.returnJson(True, "ok", {'mode': mode})


def setDbrunMode(version=''):
    if version == '5.5':
        return slemp.returnJson(False, "Switching is not supported")

    args = getArgs()
    data = checkArgs(args, ['mode', 'reload'])
    if not data[0]:
        return data[1]

    mode = args['mode']
    dbreload = args['reload']

    if not mode in ['classic', 'gtid']:
        return slemp.returnJson(False, "Invalid value for mode:" + mode)

    origin_mode = recognizeDbMode()
    path = getConf()
    con = slemp.readFile(path)
    rep = r"!include %s/%s\.cnf" % (getServerDir() + "/etc/mode", origin_mode)
    rep_after = "!include %s/%s.cnf" % (getServerDir() + "/etc/mode", mode)
    con = re.sub(rep, rep_after, con)
    slemp.writeFile(path, con)

    if version == '5.6':
        dbreload = 'yes'
    else:
        db = pMysqlDb()
        # The value of @@GLOBAL.GTID_MODE can only be changed one step at a
        # time: OFF <-> OFF_PERMISSIVE <-> ON_PERMISSIVE <-> ON. Also note that
        # this value must be stepped up or down simultaneously on all servers.
        # See the Manual for instructions.
        if mode == 'classic':
            db.query('set global enforce_gtid_consistency=off')
            db.query('set global gtid_mode=on')
            db.query('set global gtid_mode=on_permissive')
            db.query('set global gtid_mode=off_permissive')
            db.query('set global gtid_mode=off')
        elif mode == 'gtid':
            db.query('set global enforce_gtid_consistency=on')
            db.query('set global gtid_mode=off')
            db.query('set global gtid_mode=off_permissive')
            db.query('set global gtid_mode=on_permissive')
            db.query('set global gtid_mode=on')

    if dbreload == "yes":
        restart(version)

    return slemp.returnJson(True, "Switch successfully!")


def findBinlogDoDb():
    conf = getConf()
    con = slemp.readFile(conf)
    rep = r"binlog-do-db\s*?=\s*?(.*)"
    dodb = re.findall(rep, con, re.M)
    return dodb


def findBinlogSlaveDoDb():
    conf = getConf()
    con = slemp.readFile(conf)
    rep = r"replicate-do-db\s*?=\s*?(.*)"
    dodb = re.findall(rep, con, re.M)
    return dodb


def setDbMasterAccess():
    args = getArgs()
    data = checkArgs(args, ['username', 'access'])
    if not data[0]:
        return data[1]
    username = args['username']
    access = args['access']
    pdb = pMysqlDb()
    psdb = pSqliteDb('master_replication_user')
    password = psdb.where("username=?", (username,)).getField('password')
    users = pdb.query("select Host from user where User='" +
                      username + "' AND Host!='localhost'")
    for us in users:
        pdb.execute("drop user '" + username + "'@'" + us["Host"] + "'")

    dbname = '*'
    for a in access.split(','):
        pdb.execute(
            "CREATE USER `%s`@`%s` IDENTIFIED BY '%s'" % (username, a, password))
        pdb.execute(
            "grant all privileges on %s.* to `%s`@`%s`" % (dbname, username, a))

    pdb.execute("flush privileges")
    psdb.where('username=?', (username,)).save('accept', (access,))
    return slemp.returnJson(True, 'Successfully set!')


def getMasterDbList(version=''):
    args = getArgs()
    page = 1
    page_size = 10
    search = ''
    data = {}
    if 'page' in args:
        page = int(args['page'])

    if 'page_size' in args:
        page_size = int(args['page_size'])

    if 'search' in args:
        search = args['search']

    conn = pSqliteDb('databases')
    limit = str((page - 1) * page_size) + ',' + str(page_size)
    condition = ''
    dodb = findBinlogDoDb()
    data['dodb'] = dodb

    slave_dodb = findBinlogSlaveDoDb()

    if not search == '':
        condition = "name like '%" + search + "%'"
    field = 'id,pid,name,username,password,accept,ps,addtime'
    clist = conn.where(condition, ()).field(
        field).limit(limit).order('id desc').select()
    count = conn.where(condition, ()).count()

    for x in range(0, len(clist)):
        if clist[x]['name'] in dodb:
            clist[x]['master'] = 1
        else:
            clist[x]['master'] = 0

        if clist[x]['name'] in slave_dodb:
            clist[x]['slave'] = 1
        else:
            clist[x]['slave'] = 0

    _page = {}
    _page['count'] = count
    _page['p'] = page
    _page['row'] = page_size
    _page['tojs'] = 'dbList'
    data['page'] = slemp.getPage(_page)
    data['data'] = clist

    return slemp.getJson(data)


def setDbMaster(version):
    args = getArgs()
    data = checkArgs(args, ['name'])
    if not data[0]:
        return data[1]

    conf = getConf()
    con = slemp.readFile(conf)
    rep = r"(binlog-do-db\s*?=\s*?(.*))"
    dodb = re.findall(rep, con, re.M)

    isHas = False
    for x in range(0, len(dodb)):

        if dodb[x][1] == args['name']:
            isHas = True

            con = con.replace(dodb[x][0] + "\n", '')
            slemp.writeFile(conf, con)

    if not isHas:
        prefix = '#binlog-do-db'
        con = con.replace(
            prefix, prefix + "\nbinlog-do-db=" + args['name'])
        slemp.writeFile(conf, con)

    restart(version)
    time.sleep(4)
    return slemp.returnJson(True, 'Successfully set', [args, dodb])


def setDbSlave(version):
    args = getArgs()
    data = checkArgs(args, ['name'])
    if not data[0]:
        return data[1]

    conf = getConf()
    con = slemp.readFile(conf)
    rep = r"(replicate-do-db\s*?=\s*?(.*))"
    dodb = re.findall(rep, con, re.M)

    isHas = False
    for x in range(0, len(dodb)):
        if dodb[x][1] == args['name']:
            isHas = True

            con = con.replace(dodb[x][0] + "\n", '')
            slemp.writeFile(conf, con)

    if not isHas:
        prefix = '#replicate-do-db'
        con = con.replace(
            prefix, prefix + "\nreplicate-do-db=" + args['name'])
        slemp.writeFile(conf, con)

    restart(version)
    time.sleep(4)
    return slemp.returnJson(True, 'Successfully set', [args, dodb])


def getMasterStatus(version=''):
    try:
        if status(version) == 'stop':
            return slemp.returnJson(False, 'MySQL is not started, or is starting...!', [])

        conf = getConf()
        content = slemp.readFile(conf)
        master_status = False
        if content.find('#log-bin') == -1 and content.find('log-bin') > 1:
            dodb = findBinlogDoDb()
            if len(dodb) > 0:
                master_status = True

        data = {}
        data['mode'] = recognizeDbMode()
        data['status'] = master_status

        db = pMysqlDb()
        dlist = db.query('show slave status')

        # print(dlist[0])
        if len(dlist) > 0 and (dlist[0]["Slave_IO_Running"] == 'Yes' or dlist[0]["Slave_SQL_Running"] == 'Yes'):
            data['slave_status'] = True

        return slemp.returnJson(master_status, 'Successfully set', data)
    except Exception as e:
        return slemp.returnJson(False, "The database password is wrong, in the management list - click [Repair]!", 'pwd')


def setMasterStatus(version=''):

    conf = getConf()
    con = slemp.readFile(conf)

    if con.find('#log-bin') != -1:
        return slemp.returnJson(False, 'Binary logging must be enabled')

    sign = 'slemp_ms_open'

    dodb = findBinlogDoDb()
    if not sign in dodb:
        prefix = '#binlog-do-db'
        con = con.replace(prefix, prefix + "\nbinlog-do-db=" + sign)
        slemp.writeFile(conf, con)
    else:
        con = con.replace("binlog-do-db=" + sign + "\n", '')
        rep = r"(binlog-do-db\s*?=\s*?(.*))"
        dodb = re.findall(rep, con, re.M)
        for x in range(0, len(dodb)):
            con = con.replace(dodb[x][0] + "\n", '')
        slemp.writeFile(conf, con)

    restart(version)
    return slemp.returnJson(True, 'Successfully set')


def getMasterRepSlaveList(version=''):
    args = getArgs()
    page = 1
    page_size = 10
    search = ''
    data = {}
    if 'page' in args:
        page = int(args['page'])

    if 'page_size' in args:
        page_size = int(args['page_size'])

    if 'search' in args:
        search = args['search']

    conn = pSqliteDb('master_replication_user')
    limit = str((page - 1) * page_size) + ',' + str(page_size)
    condition = ''

    if not search == '':
        condition = "name like '%" + search + "%'"
    field = 'id,username,password,accept,ps,addtime'
    clist = conn.where(condition, ()).field(
        field).limit(limit).order('id desc').select()
    count = conn.where(condition, ()).count()

    _page = {}
    _page['count'] = count
    _page['p'] = page
    _page['row'] = page_size
    _page['tojs'] = 'getMasterRepSlaveList'
    data['page'] = slemp.getPage(_page)
    data['data'] = clist

    return slemp.getJson(data)


def addMasterRepSlaveUser(version=''):
    args = getArgs()
    data = checkArgs(args, ['username', 'password'])
    if not data[0]:
        return data[1]

    if not 'address' in args:
        address = ''
    else:
        address = args['address'].strip()

    username = args['username'].strip()
    password = args['password'].strip()
    # ps = args['ps'].strip()
    # address = args['address'].strip()
    # dataAccess = args['dataAccess'].strip()

    reg = "^[\w-]+$"
    if not re.match(reg, username):
        return slemp.returnJson(False, 'Username cannot contain special symbols!')
    checks = ['root', 'mysql', 'test', 'sys', 'panel_logs']
    if username in checks or len(username) < 1:
        return slemp.returnJson(False, 'Username is invalid!')
    if password in checks or len(password) < 1:
        return slemp.returnJson(False, 'Password is invalid!')

    if len(password) < 1:
        password = slemp.md5(time.time())[0:8]

    pdb = pMysqlDb()
    psdb = pSqliteDb('master_replication_user')

    if psdb.where("username=?", (username)).count() > 0:
        return slemp.returnJson(False, 'User already exists!')

    sql = "GRANT REPLICATION SLAVE ON *.* TO  '" + username + \
        "'@'%' identified by '" + password + "';"
    result = pdb.execute(sql)

    isError = isSqlError(result)
    if isError != None:
        return isError

    sql_select = "grant select,lock tables,PROCESS on *.* to " + username + "@'%';"
    pdb.execute(sql_select)
    pdb.execute('FLUSH PRIVILEGES;')

    addTime = time.strftime('%Y-%m-%d %X', time.localtime())
    psdb.add('username,password,accept,ps,addtime',
             (username, password, '%', '', addTime))
    return slemp.returnJson(True, 'Added successfully!')


def getMasterRepSlaveUserCmd(version):

    args = getArgs()
    data = checkArgs(args, ['username', 'db'])
    if not data[0]:
        return data[1]

    psdb = pSqliteDb('master_replication_user')
    f = 'username,password'
    username = args['username']
    if username == '':
        count = psdb.count()
        if count == 0:
            return slemp.returnJson(False, 'Please add sync account!')

        clist = psdb.field(f).limit('1').order('id desc').select()
    else:
        clist = psdb.field(f).where("username=?", (username,)).limit(
            '1').order('id desc').select()

    ip = slemp.getLocalIp()
    port = getMyPort()
    db = pMysqlDb()

    mstatus = db.query('show master status')
    if len(mstatus) == 0:
        return slemp.returnJson(False, 'Unopened!')

    mode = recognizeDbMode()

    # SELECT BINLOG_GTID_POS('master1-bin.000002', 561866201);

    if mode == "gtid":
        sql = "CHANGE MASTER TO MASTER_HOST='" + ip + "', MASTER_PORT=" + port + ", MASTER_USER='" + \
            clist[0]['username'] + "', MASTER_PASSWORD='" + \
            clist[0]['password'] + "', " + "MASTER_LOG_FILE='" + mstatus[0]["File"] + \
            "',MASTER_LOG_POS=" + \
            str(mstatus[0]["Position"]) + \
            ",MASTER_USE_GTID=slave_pos,MASTER_CONNECT_RETRY=10;"
    else:
        sql = "CHANGE MASTER TO MASTER_HOST='" + ip + "', MASTER_PORT=" + port + ", MASTER_USER='" + \
            clist[0]['username']  + "', MASTER_PASSWORD='" + \
            clist[0]['password'] + \
            "', MASTER_LOG_FILE='" + mstatus[0]["File"] + \
            "',MASTER_LOG_POS=" + str(mstatus[0]["Position"])

    data = {}
    data['cmd'] = sql
    data["info"] = clist[0]
    data['mode'] = mode

    return slemp.returnJson(True, 'ok!', data)


def delMasterRepSlaveUser(version=''):
    args = getArgs()
    data = checkArgs(args, ['username'])
    if not data[0]:
        return data[1]

    name = args['username']

    pdb = pMysqlDb()
    psdb = pSqliteDb('master_replication_user')
    pdb.execute("drop user '" + name + "'@'%'")
    pdb.execute("drop user '" + name + "'@'localhost'")

    users = pdb.query("select Host from user where User='" +
                      name + "' AND Host!='localhost'")
    for us in users:
        pdb.execute("drop user '" + name + "'@'" + us["Host"] + "'")

    psdb.where("username=?", (args['username'],)).delete()

    return slemp.returnJson(True, 'Successfully deleted!')


def updateMasterRepSlaveUser(version=''):
    args = getArgs()
    data = checkArgs(args, ['username', 'password'])
    if not data[0]:
        return data[1]

    pdb = pMysqlDb()
    psdb = pSqliteDb('master_replication_user')
    pdb.execute("drop user '" + args['username'] + "'@'%'")

    pdb.execute("GRANT REPLICATION SLAVE ON *.* TO  '" +
                args['username'] + "'@'%' identified by '" + args['password'] + "'")

    psdb.where("username=?", (args['username'],)).save(
        'password', args['password'])

    return slemp.returnJson(True, 'Update completed!')


def getSlaveSSHList(version=''):
    args = getArgs()
    data = checkArgs(args, ['page', 'page_size'])
    if not data[0]:
        return data[1]

    page = int(args['page'])
    page_size = int(args['page_size'])

    conn = pSqliteDb('slave_id_rsa')
    limit = str((page - 1) * page_size) + ',' + str(page_size)

    field = 'id,ip,port,db_user,id_rsa,ps,addtime'
    clist = conn.field(field).limit(limit).order('id desc').select()
    count = conn.count()

    data = {}
    _page = {}
    _page['count'] = count
    _page['p'] = page
    _page['row'] = page_size
    _page['tojs'] = args['tojs']
    data['page'] = slemp.getPage(_page)
    data['data'] = clist

    return slemp.getJson(data)


def getSlaveSyncUserByIp(version=''):
    args = getArgs()
    data = checkArgs(args, ['ip'])
    if not data[0]:
        return data[1]

    ip = args['ip']

    conn = pSqliteDb('slave_sync_user')
    data = conn.field('ip,port,user,pass,mode,cmd').where(
        "ip=?", (ip,)).select()
    return slemp.returnJson(True, 'ok', data)


def addSlaveSyncUser(version=''):
    import base64

    args = getArgs()
    data = checkArgs(args, ['ip'])
    if not data[0]:
        return data[1]

    ip = args['ip']
    if ip == "":
        return slemp.returnJson(True, 'ok')

    data = checkArgs(args, ['port', 'user', 'pass', 'mode'])
    if not data[0]:
        return data[1]

    cmd = args['cmd']
    port = args['port']
    user = args['user']
    apass = args['pass']
    mode = args['mode']
    addTime = time.strftime('%Y-%m-%d %X', time.localtime())

    conn = pSqliteDb('slave_sync_user')
    data = conn.field('ip').where("ip=?", (ip,)).select()
    if len(data) > 0:
        res = conn.where("ip=?", (ip,)).save(
            'port,user,pass,mode,cmd', (port, user, apass, mode, cmd))
    else:
        conn.add('ip,port,user,cmd,user,pass,mode,addtime',
                 (ip, port, user, cmd, user, apass, mode, addTime))

    return slemp.returnJson(True, 'Successfully set!')


def delSlaveSyncUser(version=''):
    args = getArgs()
    data = checkArgs(args, ['ip'])
    if not data[0]:
        return data[1]

    ip = args['ip']

    conn = pSqliteDb('slave_sync_user')
    conn.where("ip=?", (ip,)).delete()
    return slemp.returnJson(True, 'Successfully deleted!')


def getSlaveSyncUserList(version=''):
    args = getArgs()
    data = checkArgs(args, ['page', 'page_size'])
    if not data[0]:
        return data[1]

    page = int(args['page'])
    page_size = int(args['page_size'])

    conn = pSqliteDb('slave_sync_user')
    limit = str((page - 1) * page_size) + ',' + str(page_size)

    field = 'id,ip,port,user,pass,cmd,addtime'
    clist = conn.field(field).limit(limit).order('id desc').select()
    count = conn.count()

    data = {}
    _page = {}
    _page['count'] = count
    _page['p'] = page
    _page['row'] = page_size
    _page['tojs'] = args['tojs']
    data['page'] = slemp.getPage(_page)
    data['data'] = clist

    return slemp.getJson(data)


def getSyncModeFile():
    return getServerDir() + "/sync.mode"


def getSlaveSyncMode(version):
    sync_mode = getSyncModeFile()
    if os.path.exists(sync_mode):
        mode = slemp.readFile(sync_mode).strip()
        return slemp.returnJson(True, 'ok', mode)
    return slemp.returnJson(False, 'fail')


def setSlaveSyncMode(version):
    args = getArgs()
    data = checkArgs(args, ['mode'])
    if not data[0]:
        return data[1]
    mode = args['mode']
    sync_mode = getSyncModeFile()

    if mode == 'none':
        os.remove(sync_mode)
    else:
        slemp.writeFile(sync_mode, mode)
    return slemp.returnJson(True, 'Successfully set', mode)


def getSlaveSSHByIp(version=''):
    args = getArgs()
    data = checkArgs(args, ['ip'])
    if not data[0]:
        return data[1]

    ip = args['ip']

    conn = pSqliteDb('slave_id_rsa')
    data = conn.field('ip,port,db_user,id_rsa').where("ip=?", (ip,)).select()
    return slemp.returnJson(True, 'ok', data)


def addSlaveSSH(version=''):
    import base64

    args = getArgs()
    data = checkArgs(args, ['ip'])
    if not data[0]:
        return data[1]

    ip = args['ip']
    if ip == "":
        return slemp.returnJson(True, 'ok')

    data = checkArgs(args, ['port', 'id_rsa', 'db_user'])
    if not data[0]:
        return data[1]

    id_rsa = args['id_rsa']
    port = args['port']
    db_user = args['db_user']
    user = 'root'
    addTime = time.strftime('%Y-%m-%d %X', time.localtime())

    conn = pSqliteDb('slave_id_rsa')
    data = conn.field('ip,id_rsa').where("ip=?", (ip,)).select()
    if len(data) > 0:
        res = conn.where("ip=?", (ip,)).save(
            'port,id_rsa,db_user', (port, id_rsa, db_user))
    else:
        conn.add('ip,port,user,id_rsa,db_user,ps,addtime',
                 (ip, port, user, id_rsa, db_user, '', addTime))

    return slemp.returnJson(True, 'Successfully set!')


def delSlaveSSH(version=''):
    args = getArgs()
    data = checkArgs(args, ['ip'])
    if not data[0]:
        return data[1]

    ip = args['ip']

    conn = pSqliteDb('slave_id_rsa')
    conn.where("ip=?", (ip,)).delete()
    return slemp.returnJson(True, 'ok')


def updateSlaveSSH(version=''):
    args = getArgs()
    data = checkArgs(args, ['ip', 'id_rsa'])
    if not data[0]:
        return data[1]

    ip = args['ip']
    id_rsa = args['id_rsa']
    conn = pSqliteDb('slave_id_rsa')
    conn.where("ip=?", (ip,)).save('id_rsa', (id_rsa,))
    return slemp.returnJson(True, 'ok')


def getSlaveList(version=''):

    db = pMysqlDb()
    dlist = db.query('show slave status')
    ret = []
    for x in range(0, len(dlist)):
        tmp = {}
        tmp['Master_User'] = dlist[x]["Master_User"]
        tmp['Master_Host'] = dlist[x]["Master_Host"]
        tmp['Master_Port'] = dlist[x]["Master_Port"]
        tmp['Master_Log_File'] = dlist[x]["Master_Log_File"]
        tmp['Slave_IO_Running'] = dlist[x]["Slave_IO_Running"]
        tmp['Slave_SQL_Running'] = dlist[x]["Slave_SQL_Running"]
        tmp['Last_Error'] = dlist[x]["Last_Error"]
        tmp['Last_IO_Error'] = dlist[x]["Last_IO_Error"]
        tmp['Last_SQL_Error'] = dlist[x]["Last_SQL_Error"]
        tmp['Slave_SQL_Running_State'] = dlist[x]["Slave_SQL_Running_State"]

        tmp['Error'] = ''
        if tmp['Last_Error'] != '':
            tmp['Error'] = tmp['Last_Error']

        if tmp['Last_IO_Error'] != '':
            tmp['Error'] = tmp['Last_IO_Error']

        if tmp['Last_SQL_Error'] != '':
            tmp['Error'] = tmp['Last_SQL_Error']

        if tmp['Error'] == '':
            tmp['Error'] = tmp['Slave_SQL_Running_State']

        ret.append(tmp)
    data = {}
    data['data'] = ret

    return slemp.getJson(data)


def getSlaveSyncCmd(version=''):

    root = slemp.getRunDir()
    cmd = 'cd ' + root + ' && python3 ' + root + \
        '/plugins/mysql/index.py do_full_sync {"db":"all"}'
    return slemp.returnJson(True, 'ok', cmd)


def initSlaveStatus(version=''):
    mode_file = getSyncModeFile()
    if not os.path.exists(mode_file):
        return slemp.returnJson(False, 'Synchronization configuration needs to be set first')

    mode = slemp.readFile(mode_file)
    if mode == 'ssh':
        return initSlaveStatusSSH(version)
    if mode == 'sync-user':
        return initSlaveStatusSyncUser(version)


def initSlaveStatusSyncUser(version=''):
    conn = pSqliteDb('slave_sync_user')
    data = conn.field('ip,port,user,pass,mode,cmd').find()
    if len(data) < 1:
        return slemp.returnJson(False, 'Need to add sync user configuration first!')

    # print(data)
    db = pMysqlDb()
    dlist = db.query('show slave status')
    if len(dlist) > 0:
        return slemp.returnJson(False, 'Already initialized zz...')

    u = data

    mode_name = 'classic'
    if u['mode'] == '1':
        mode_name = 'gtid'

    local_mode = recognizeDbMode()
    if local_mode != mode_name:
        return slemp.returnJson(False, 'Inconsistent sync mode!')

    # print(u['cmd'])
    t = db.query(u['cmd'])
    # print(t)
    db.query("start slave")
    return slemp.returnJson(True, 'Initialization successful!')


def initSlaveStatusSSH(version=''):
    db = pMysqlDb()
    dlist = db.query('show slave status')
    if len(dlist) > 0:
        return slemp.returnJson(False, 'Already initialized zz...')

    conn = pSqliteDb('slave_id_rsa')
    data = conn.field('ip,port,id_rsa,db_user').find()

    if len(data) < 1:
        return slemp.returnJson(False, 'You need to configure [[main] SSH configuration] first!')

    SSH_PRIVATE_KEY = "/tmp/t_ssh.txt"
    ip = data['ip']
    master_port = data['port']
    slemp.writeFile(SSH_PRIVATE_KEY, data['id_rsa'].replace('\\n', '\n'))

    import paramiko
    paramiko.util.log_to_file('paramiko.log')
    ssh = paramiko.SSHClient()

    try:

        slemp.execShell("chmod 600 " + SSH_PRIVATE_KEY)
        key = paramiko.RSAKey.from_private_key_file(SSH_PRIVATE_KEY)
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=ip, port=int(master_port),
                    username='root', pkey=key)

        db_user = data['db_user']
        cmd = 'cd /home/slemp/server/panel && python3 plugins/mariadb/index.py get_master_rep_slave_user_cmd {"username":"' + db_user + '","db":""}'
        stdin, stdout, stderr = ssh.exec_command(cmd)
        result = stdout.read()
        result = result.decode('utf-8')
        cmd_data = json.loads(result)
        time.sleep(1)
        ssh.close()
        if not cmd_data['status']:
            return slemp.returnJson(False, '[Host]:' + cmd_data['msg'])

        local_mode = recognizeDbMode()
        if local_mode != cmd_data['data']['mode']:
            return slemp.returnJson(False, 'The master [{}] slave [{}], the running mode is inconsistent!'.format(cmd_data['data']['mode'], local_mode))

        u = cmd_data['data']['info']
        ps = u['username'] + "|" + u['password']
        conn.where('ip=?', (ip,)).setField('ps', ps)
        db.query('stop slave')

        # Ensure that the synchronization IP is consistent
        cmd = cmd_data['data']['cmd']
        if cmd.find('SOURCE_HOST') > -1:
            cmd = re.sub(r"SOURCE_HOST='(.*?)'",
                         "SOURCE_HOST='" + ip + "'", cmd, 1)

        if cmd.find('MASTER_HOST') > -1:
            cmd = re.sub(r"MASTER_HOST='(.*?)'",
                         "MASTER_HOST='" + ip + "'", cmd, 1)

        # print(cmd)
        db.query(cmd)
        db.query("start slave")

    except Exception as e:
        return slemp.returnJson(False, 'SSH authentication configuration connection failed!' + str(e))

    os.system("rm -rf " + SSH_PRIVATE_KEY)
    return slemp.returnJson(True, 'Initialization successful!')


def setSlaveStatus(version=''):
    mode_file = getSyncModeFile()
    if not os.path.exists(mode_file):
        return slemp.returnJson(False, 'Synchronization configuration needs to be set first')

    mode = slemp.readFile(mode_file)
    if mode == 'ssh':
        return setSlaveStatusSSH(version)
    if mode == 'sync-user':
        return setSlaveStatusSyncUser(version)


def setSlaveStatusSyncUser(version=''):
    db = pMysqlDb()
    dlist = db.query('show slave status')
    if len(dlist) == 0:
        return slemp.returnJson(False, 'You need to manually add a synchronization account or perform initialization!')

    if len(dlist) > 0 and (dlist[0]["Slave_IO_Running"] == 'Yes' or dlist[0]["Slave_SQL_Running"] == 'Yes'):
        db.query('stop slave')
    else:
        ip = dlist[0]['Master_Host']
        conn = pSqliteDb('slave_sync_user')
        data = conn.field('ip,port,user,pass,mode,cmd').find()
        if len(data) == 0:
            return slemp.returnJson(False, 'Can not restart without data!')
        user = data['user']
        apass = data['pass']

        db.query("start slave")
        # db.query("start slave user='{}' password='{}';".format(user, apass))

    return slemp.returnJson(True, 'Successfully set!')


def setSlaveStatusSSH(version=''):

    db = pMysqlDb()
    dlist = db.query('show slave status')
    if len(dlist) == 0:
        return slemp.returnJson(False, 'You need to manually add the main service command or execute [initialization]!')

    # print(dlist)
    if len(dlist) > 0 and (dlist[0]["Slave_IO_Running"] == 'Yes' or dlist[0]["Slave_SQL_Running"] == 'Yes'):
        db.query('stop slave')
    else:
        ip = dlist[0]['Master_Host']
        conn = pSqliteDb('slave_id_rsa')
        data = conn.field('ip,ps').where("ip=?", (ip,)).find()
        if len(data) == 0:
            return slemp.returnJson(False, 'Can not restart without data!')
        db.query("start slave")

    return slemp.returnJson(True, 'Successfully set!')


def deleteSlave(version=''):
    db = pMysqlDb()
    dlist = db.query('stop slave')
    dlist = db.query('reset slave all')
    return slemp.returnJson(True, 'Successfully deleted!')


def dumpMysqlData(version=''):
    args = getArgs()
    data = checkArgs(args, ['db'])
    if not data[0]:
        return data[1]

    pwd = pSqliteDb('config').where('id=?', (1,)).getField('mysql_root')
    mysql_dir = getServerDir()
    myconf = mysql_dir + "/etc/my.cnf"

    option = ''
    mode = recognizeDbMode()
    if mode == 'gtid':
        option = ' --set-gtid-purged=off '

    if args['db'].lower() == 'all':
        dlist = findBinlogDoDb()
        cmd = mysql_dir + "/bin/mysqldump --defaults-file=" + myconf + " " + option + " -uroot -p" + \
            pwd + " --databases " + \
            ' '.join(dlist) + " | gzip > /tmp/dump.sql.gz"
    else:
        cmd = mysql_dir + "/bin/mysqldump --defaults-file=" + myconf + " " + option + " -uroot -p" + \
            pwd + " --databases " + args['db'] + " | gzip > /tmp/dump.sql.gz"

    ret = slemp.execShell(cmd)
    if ret[0] == '':
        return 'ok'
    return 'fail'


############### --- important synchronization---- ###########

def writeDbSyncStatus(data):
    path = '/tmp/db_async_status.txt'
    # status_data['code'] = 1
    # status_data['msg'] = 'master server backup completed...'
    # status_data['progress'] = 30
    slemp.writeFile(path, json.dumps(data))


def doFullSync(version=''):
    mode_file = getSyncModeFile()
    if not os.path.exists(mode_file):
        return slemp.returnJson(False, 'Synchronization configuration needs to be set first')

    mode = slemp.readFile(mode_file)
    if mode == 'ssh':
        return doFullSyncSSH(version)
    if mode == 'sync-user':
        return doFullSyncUser(version)


def doFullSyncUser(version=''):
    args = getArgs()
    data = checkArgs(args, ['db'])
    if not data[0]:
        return data[1]

    sync_db = args['db']

    db = pMysqlDb()

    conn = pSqliteDb('slave_sync_user')
    data = conn.field('ip,port,user,pass,mode,cmd').find()
    user = data['user']
    apass = data['pass']
    port = data['port']
    ip = data['ip']

    bak_file = '/tmp/tmp.sql'

    writeDbSyncStatus({'code': 0, 'msg': 'Start sync...', 'progress': 0})

    writeDbSyncStatus({'code': 1, 'msg': 'Export data remotely...', 'progress': 20})

    if not os.path.exists(bak_file):
        dump_sql_data = getServerDir() + "/bin/mysqldump --force --opt --default-character-set=utf8 --single-transaction -h" + ip + " -P" + \
            port + " -u" + user + " -p" + apass + " " + sync_db + " > " + bak_file
        slemp.execShell(dump_sql_data)

    writeDbSyncStatus({'code': 2, 'msg': 'Import data locally...', 'progress': 40})
    if os.path.exists(bak_file):
        pwd = pSqliteDb('config').where('id=?', (1,)).getField('mysql_root')
        sock = getSocketFile()
        my_import_cmd = getServerDir() + '/bin/mysql -S ' + sock + ' -uroot -p' + pwd + \
            ' ' + sync_db + ' < ' + bak_file
        slemp.execShell(my_import_cmd)

    db.query("start slave")

    writeDbSyncStatus({'code': 6, 'msg': 'Restart complete from library...', 'progress': 100})
    os.system("rm -rf " + bak_file)
    return True


def doFullSyncSSH(version=''):

    args = getArgs()
    data = checkArgs(args, ['db'])
    if not data[0]:
        return data[1]

    db = pMysqlDb()

    id_rsa_conn = pSqliteDb('slave_id_rsa')
    data = id_rsa_conn.field('ip,port,db_user,id_rsa').find()

    SSH_PRIVATE_KEY = "/tmp/mysql_sync_id_rsa.txt"
    id_rsa = data['id_rsa'].replace('\\n', '\n')
    slemp.writeFile(SSH_PRIVATE_KEY, id_rsa)

    ip = data["ip"]
    master_port = data['port']
    db_user = data['db_user']
    print("master ip:", ip)

    writeDbSyncStatus({'code': 0, 'msg': 'Start sync...', 'progress': 0})

    import paramiko
    paramiko.util.log_to_file('paramiko.log')
    ssh = paramiko.SSHClient()

    print(SSH_PRIVATE_KEY)
    if not os.path.exists(SSH_PRIVATE_KEY):
        writeDbSyncStatus({'code': 0, 'msg': 'Need to configure SSH......', 'progress': 0})
        return 'fail'

    try:
        # ssh.load_system_host_keys()
        slemp.execShell("chmod 600 " + SSH_PRIVATE_KEY)
        key = paramiko.RSAKey.from_private_key_file(SSH_PRIVATE_KEY)
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(ip, master_port)

        # pkey=key
        # key_filename=SSH_PRIVATE_KEY
        ssh.connect(hostname=ip, port=int(master_port),
                    username='root', pkey=key)
    except Exception as e:
        print(str(e))
        writeDbSyncStatus(
            {'code': 0, 'msg': 'SSH misconfiguration:' + str(e), 'progress': 0})
        return 'fail'

    writeDbSyncStatus({'code': 0, 'msg': 'Log in to Master successfully...', 'progress': 5})
    dbname = args['db']
    cmd = "cd /home/slemp/server/panel && python3 plugins/mariadb/index.py dump_mysql_data {\"db\":'" + dbname + "'}"
    print(cmd)
    stdin, stdout, stderr = ssh.exec_command(cmd)
    result = stdout.read()
    result = result.decode('utf-8')
    if result.strip() == 'ok':
        writeDbSyncStatus({'code': 1, 'msg': 'Master server backup completed...', 'progress': 30})
    else:
        writeDbSyncStatus(
            {'code': 1, 'msg': 'Master server backup failed...:' + str(result), 'progress': 100})
        return 'fail'

    print("sync files", "start")
    # cmd = 'scp -P' + str(master_port) + ' -i ' + SSH_PRIVATE_KEY + \
    #     ' root@' + ip + ':/tmp/dump.sql.gz /tmp'
    t = ssh.get_transport()
    sftp = paramiko.SFTPClient.from_transport(t)
    copy_status = sftp.get("/tmp/dump.sql.gz", "/tmp/dump.sql.gz")
    print("Synchronization information:", copy_status)
    print("Sync files", "end")
    if copy_status == None:
        writeDbSyncStatus({'code': 2, 'msg': 'Data synchronization is completed locally...', 'progress': 40})

    cmd = 'cd /home/slemp/server/panel && python3 plugins/mariadb/index.py get_master_rep_slave_user_cmd {"username":"' + db_user + '","db":""}'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    result = stdout.read()
    result = result.decode('utf-8')
    cmd_data = json.loads(result)

    db.query('stop slave')
    writeDbSyncStatus({'code': 3, 'msg': 'Stop slave completion...', 'progress': 45})

    cmd = cmd_data['data']['cmd']
    # Ensure that the synchronization IP is consistent
    if cmd.find('SOURCE_HOST') > -1:
        cmd = re.sub(r"SOURCE_HOST='(.*)'", "SOURCE_HOST='" + ip + "'", cmd, 1)

    if cmd.find('MASTER_HOST') > -1:
        cmd = re.sub(r"MASTER_HOST='(.*)'", "SOURCE_HOST='" + ip + "'", cmd, 1)

    db.query(cmd)
    uinfo = cmd_data['data']['info']
    ps = uinfo['username'] + "|" + uinfo['password']
    id_rsa_conn.where('ip=?', (ip,)).setField('ps', ps)
    writeDbSyncStatus({'code': 4, 'msg': 'Refresh slave library synchronization information completed...', 'progress': 50})

    pwd = pSqliteDb('config').where('id=?', (1,)).getField('mysql_root')
    root_dir = getServerDir()
    msock = root_dir + "/mysql.sock"
    slemp.execShell("cd /tmp && gzip -d dump.sql.gz")
    cmd = root_dir + "/bin/mysql -S " + msock + \
        " -uroot -p" + pwd + " < /tmp/dump.sql"
    import_data = slemp.execShell(cmd)
    if import_data[0] == '':
        print(import_data[1])
        writeDbSyncStatus({'code': 5, 'msg': 'Import data complete...', 'progress': 90})
    else:
        print(import_data[0])
        writeDbSyncStatus({'code': 5, 'msg': 'Failed to import data...', 'progress': 100})
        return 'fail'

    db.query("start slave")
    writeDbSyncStatus({'code': 6, 'msg': 'Restart complete from library...', 'progress': 100})

    os.system("rm -rf " + SSH_PRIVATE_KEY)
    os.system("rm -rf /tmp/dump.sql")
    return True


def fullSync(version=''):
    args = getArgs()
    data = checkArgs(args, ['db', 'begin'])
    if not data[0]:
        return data[1]

    status_file = '/tmp/db_async_status.txt'
    if args['begin'] == '1':
        cmd = 'cd ' + slemp.getRunDir() + ' && python3 ' + \
            getPluginDir() + \
            '/index.py do_full_sync {"db":"' + args['db'] + '"} &'
        print(cmd)
        slemp.execShell(cmd)
        return json.dumps({'code': 0, 'msg': 'Synchronizing data!', 'progress': 0})

    if os.path.exists(status_file):
        c = slemp.readFile(status_file)
        tmp = json.loads(c)
        if tmp['code'] == 1:
            sys_dump_sql = "/tmp/dump.sql"
            if os.path.exists(sys_dump_sql):
                dump_size = os.path.getsize(sys_dump_sql)
                tmp['msg'] = tmp['msg'] + ":" + " sync files:" + slemp.toSize(dump_size)
            c = json.dumps(tmp)

        # if tmp['code'] == 6:
        #     os.remove(status_file)
        return c

    return json.dumps({'code': 0, 'msg': 'Click start to start syncing!', 'progress': 0})


def installPreInspection(version):
    swap_path = slemp.getServerDir() + "/swap"
    if not os.path.exists(swap_path):
        return "In order to install MariaDB stably, first install the swap plugin!"
    return 'ok'


def uninstallPreInspection(version):
    stop(version)
    if slemp.isDebugMode():
        return 'ok'

    return "Please remove MariaDB manually[{}]<br/> rm -rf {}".format(version, getServerDir())

if __name__ == "__main__":
    func = sys.argv[1]

    version = "10.6"
    version_pl = getServerDir() + "/version.pl"
    if os.path.exists(version_pl):
        version = slemp.readFile(version_pl).strip()

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
    elif func == 'initd_status':
        print(initdStatus())
    elif func == 'initd_install':
        print(initdInstall())
    elif func == 'initd_uninstall':
        print(initdUinstall())
    elif func == 'install_pre_inspection':
        print(installPreInspection(version))
    elif func == 'uninstall_pre_inspection':
        print(uninstallPreInspection(version))
    elif func == 'run_info':
        print(runInfo(version))
    elif func == 'db_status':
        print(myDbStatus())
    elif func == 'set_db_status':
        print(setDbStatus())
    elif func == 'conf':
        print(getConf())
    elif func == 'bin_log':
        print(binLog())
    elif func == 'clean_bin_log':
        print(cleanBinLog())
    elif func == 'error_log':
        print(getErrorLog())
    elif func == 'show_log':
        print(getShowLogFile())
    elif func == 'my_db_pos':
        print(getMyDbPos())
    elif func == 'set_db_pos':
        print(setMyDbPos())
    elif func == 'my_port':
        print(getMyPort())
    elif func == 'set_my_port':
        print(setMyPort())
    elif func == 'init_pwd':
        print(initMysqlPwd())
    elif func == 'get_db_list':
        print(getDbList())
    elif func == 'set_db_backup':
        print(setDbBackup())
    elif func == 'import_db_backup':
        print(importDbBackup())
    elif func == 'import_db_external':
        print(importDbExternal())
    elif func == 'delete_db_backup':
        print(deleteDbBackup())
    elif func == 'get_db_backup_list':
        print(getDbBackupList())
    elif func == 'get_db_backup_import_list':
        print(getDbBackupImportList())
    elif func == 'add_db':
        print(addDb())
    elif func == 'del_db':
        print(delDb())
    elif func == 'sync_get_databases':
        print(syncGetDatabases())
    elif func == 'sync_to_databases':
        print(syncToDatabases())
    elif func == 'set_root_pwd':
        print(setRootPwd(version))
    elif func == 'set_user_pwd':
        print(setUserPwd(version))
    elif func == 'get_db_access':
        print(getDbAccess())
    elif func == 'set_db_access':
        print(setDbAccess())
    elif func == 'fix_db_access':
        print(fixDbAccess(version))
    elif func == 'get_db_rw':
        print(setDbRw(version))
    elif func == 'set_db_ps':
        print(setDbPs())
    elif func == 'get_db_info':
        print(getDbInfo())
    elif func == 'repair_table':
        print(repairTable())
    elif func == 'opt_table':
        print(optTable())
    elif func == 'alter_table':
        print(alterTable())
    elif func == 'get_total_statistics':
        print(getTotalStatistics())
    elif func == 'get_dbrun_mode':
        print(getDbrunMode(version))
    elif func == 'set_dbrun_mode':
        print(setDbrunMode(version))
    elif func == 'get_masterdb_list':
        print(getMasterDbList(version))
    elif func == 'get_master_status':
        print(getMasterStatus(version))
    elif func == 'set_master_status':
        print(setMasterStatus(version))
    elif func == 'set_db_master':
        print(setDbMaster(version))
    elif func == 'set_db_slave':
        print(setDbSlave(version))
    elif func == 'set_dbmaster_access':
        print(setDbMasterAccess())
    elif func == 'get_master_rep_slave_list':
        print(getMasterRepSlaveList(version))
    elif func == 'add_master_rep_slave_user':
        print(addMasterRepSlaveUser(version))
    elif func == 'del_master_rep_slave_user':
        print(delMasterRepSlaveUser(version))
    elif func == 'update_master_rep_slave_user':
        print(updateMasterRepSlaveUser(version))
    elif func == 'get_master_rep_slave_user_cmd':
        print(getMasterRepSlaveUserCmd(version))
    elif func == 'get_slave_list':
        print(getSlaveList(version))
    elif func == 'get_slave_sync_cmd':
        print(getSlaveSyncCmd(version))
    elif func == 'get_slave_ssh_list':
        print(getSlaveSSHList(version))
    elif func == 'get_slave_ssh_by_ip':
        print(getSlaveSSHByIp(version))
    elif func == 'add_slave_ssh':
        print(addSlaveSSH(version))
    elif func == 'del_slave_ssh':
        print(delSlaveSSH(version))
    elif func == 'update_slave_ssh':
        print(updateSlaveSSH(version))
    elif func == 'get_slave_sync_user_list':
        print(getSlaveSyncUserList(version))
    elif func == 'get_slave_sync_user_by_ip':
        print(getSlaveSyncUserByIp(version))
    elif func == 'add_slave_sync_user':
        print(addSlaveSyncUser(version))
    elif func == 'del_slave_sync_user':
        print(delSlaveSyncUser(version))
    elif func == 'get_slave_sync_mode':
        print(getSlaveSyncMode(version))
    elif func == 'set_slave_sync_mode':
        print(setSlaveSyncMode(version))
    elif func == 'init_slave_status':
        print(initSlaveStatus(version))
    elif func == 'set_slave_status':
        print(setSlaveStatus(version))
    elif func == 'delete_slave':
        print(deleteSlave(version))
    elif func == 'full_sync':
        print(fullSync(version))
    elif func == 'do_full_sync':
        print(doFullSync(version))
    elif func == 'dump_mysql_data':
        print(dumpMysqlData(version))
    else:
        print('error')
