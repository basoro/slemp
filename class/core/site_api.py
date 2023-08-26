# coding: utf-8

import time
import os
import sys
from urllib.parse import urlparse
import slemp
import re
import json
import shutil


from flask import request


class site_api:
    siteName = None
    sitePath = None
    sitePort = None
    phpVersion = None

    setupPath = None
    vhostPath = None
    logsPath = None
    passPath = None
    rewritePath = None
    redirectPath = None
    sslDir = None
    sslLetsDir = None

    def __init__(self):
        self.setupPath = slemp.getServerDir() + '/web_conf'

        self.vhostPath = vhost = self.setupPath + '/nginx/vhost'
        if not os.path.exists(vhost):
            slemp.execShell("mkdir -p " + vhost + " && chmod -R 755 " + vhost)
        self.rewritePath = rewrite = self.setupPath + '/nginx/rewrite'
        if not os.path.exists(rewrite):
            slemp.execShell("mkdir -p " + rewrite + " && chmod -R 755 " + rewrite)

        self.passPath = passwd = self.setupPath + '/nginx/pass'
        if not os.path.exists(passwd):
            slemp.execShell("mkdir -p " + passwd + " && chmod -R 755 " + passwd)

        self.redirectPath = redirect = self.setupPath + '/nginx/redirect'
        if not os.path.exists(redirect):
            slemp.execShell("mkdir -p " + redirect +
                         " && chmod -R 755 " + redirect)

        self.proxyPath = proxy = self.setupPath + '/nginx/proxy'
        if not os.path.exists(proxy):
            slemp.execShell("mkdir -p " + proxy + " && chmod -R 755 " + proxy)

        self.logsPath = slemp.getRootDir() + '/wwwlogs'
        # ssl conf
        self.sslDir = self.setupPath + '/ssl'
        self.sslLetsDir = self.setupPath + '/letsencrypt'
        if not os.path.exists(self.sslLetsDir):
            slemp.execShell("mkdir -p " + self.sslLetsDir +
                         " && chmod -R 755 " + self.sslLetsDir)

    def runHook(self, hook_name, func_name):
        hook_file = 'data/hook_site_cb.json'
        hook_cfg = []
        if os.path.exists(hook_file):
            t = slemp.readFile(hook_file)
            hook_cfg = json.loads(t)

        hook_num = len(hook_cfg)
        if hook_num == 0:
            return

        import plugins_api
        pa = plugins_api.plugins_api()

        for x in range(hook_num):
            hook_data = hook_cfg[x]
            if func_name in hook_data:
                app_name = hook_data["name"]
                run_func = hook_data[func_name]['func']
                # print(app_name, run_func)
                pa.run(app_name, run_func)
        return True

    ##### ----- start ----- ###
    def listApi(self):
        limit = request.form.get('limit', '10')
        p = request.form.get('p', '1')
        type_id = request.form.get('type_id', '0').strip()
        search = request.form.get('search', '').strip()

        start = (int(p) - 1) * (int(limit))

        siteM = slemp.M('sites').field('id,name,path,status,ps,addtime,edate')

        sql_where = ''
        if search != '':
            sql_where = " name like '%" + search + "%' or ps like '%" + search + "%' "

        if type_id != '' and int(type_id) >= 0 and search != '':
            sql_where = sql_where + " and type_id=" + type_id + ""
        elif type_id != '' and int(type_id) >= 0:
            sql_where = " type_id=" + type_id

        if sql_where != '':
            siteM.where(sql_where)

        _list = siteM.limit((str(start)) + ',' +
                            limit).order('id desc').select()

        if _list != None:
            for i in range(len(_list)):
                _list[i]['backup_count'] = slemp.M('backup').where(
                    "pid=? AND type=?", (_list[i]['id'], 0)).count()

        _ret = {}
        _ret['data'] = _list

        count = siteM.count()
        _page = {}
        _page['count'] = count
        _page['tojs'] = 'getWeb'
        _page['p'] = p
        _page['row'] = limit

        _ret['page'] = slemp.getPage(_page)
        return slemp.getJson(_ret)

    def setDefaultSiteApi(self):
        name = request.form.get('name', '')
        import time
        default_site = slemp.readFile('data/default_site.pl')
        if default_site:
            path = self.getHostConf(default_site)
            if os.path.exists(path):
                conf = slemp.readFile(path)
                rep = "listen\s+80.+;"
                conf = re.sub(rep, 'listen 80;', conf, 1)
                rep = "listen\s+443.+;"
                conf = re.sub(rep, 'listen 443 ssl;', conf, 1)
                slemp.writeFile(path, conf)

        path = self.getHostConf(name)
        if os.path.exists(path):
            conf = slemp.readFile(path)
            rep = "listen\s+80\s*;"
            conf = re.sub(rep, 'listen 80 default_server;', conf, 1)
            rep = "listen\s+443\s*ssl\s*\w*\s*;"
            conf = re.sub(rep, 'listen 443 ssl default_server;', conf, 1)
            slemp.writeFile(path, conf)

        slemp.writeFile('data/default_site.pl', name)
        slemp.restartWeb()
        return slemp.returnJson(True, 'Successfully set!')

    def getDefaultSiteApi(self):
        data = {}
        data['sites'] = slemp.M('sites').field(
            'name').order('id desc').select()
        data['default_site'] = slemp.readFile('data/default_site.pl')
        return slemp.getJson(data)

    def getCliPhpVersionApi(self):
        php_dir = slemp.getServerDir() + '/php'
        if not os.path.exists(php_dir):
            return slemp.returnJson(False, 'PHP is not installed and cannot be set')

        php_bin = '/usr/bin/php'
        php_versions = self.getPhpVersion()
        php_versions = php_versions[1:]

        if len(php_versions) < 1:
            return slemp.returnJson(False, 'PHP is not installed and cannot be set')

        if os.path.exists(php_bin) and os.path.islink(php_bin):
            link_re = os.readlink(php_bin)
            for v in php_versions:
                if link_re.find(v['version']) != -1:
                    return slemp.getJson({"select": v, "versions": php_versions})

        return slemp.getJson({
            "select": php_versions[0],
            "versions": php_versions})

    def setCliPhpVersionApi(self):
        if slemp.isAppleSystem():
            return slemp.returnJson(False, "The development machine cannot be set!")

        version = request.form.get('version', '')

        php_bin = '/usr/bin/php'
        php_bin_src = "/home/slemp/server/php/%s/bin/php" % version
        php_ize = '/usr/bin/phpize'
        php_ize_src = "/home/slemp/server/php/%s/bin/phpize" % version
        php_fpm = '/usr/bin/php-fpm'
        php_fpm_src = "/home/slemp/server/php/%s/sbin/php-fpm" % version
        php_pecl = '/usr/bin/pecl'
        php_pecl_src = "/home/slemp/server/php/%s/bin/pecl" % version
        php_pear = '/usr/bin/pear'
        php_pear_src = "/home/slemp/server/php/%s/bin/pear" % version
        if not os.path.exists(php_bin_src):
            return slemp.returnJson(False, 'The specified PHP version is not installed!')

        is_chattr = slemp.execShell('lsattr /usr|grep /usr/bin')[0].find('-i-')
        if is_chattr != -1:
            slemp.execShell('chattr -i /usr/bin')
        slemp.execShell("rm -f " + php_bin + ' ' + php_ize + ' ' +
                     php_fpm + ' ' + php_pecl + ' ' + php_pear)
        slemp.execShell("ln -sf %s %s" % (php_bin_src, php_bin))
        slemp.execShell("ln -sf %s %s" % (php_ize_src, php_ize))
        slemp.execShell("ln -sf %s %s" % (php_fpm_src, php_fpm))
        slemp.execShell("ln -sf %s %s" % (php_pecl_src, php_pecl))
        slemp.execShell("ln -sf %s %s" % (php_pear_src, php_pear))
        if is_chattr != -1:
            slemp.execShell('chattr +i /usr/bin')
        slemp.writeLog('Panel settings', 'Set the PHP-CLI version to: %s' % version)
        return slemp.returnJson(True, 'Successfully set!')

    def setPsApi(self):
        mid = request.form.get('id', '')
        ps = request.form.get('ps', '')
        if slemp.M('sites').where("id=?", (mid,)).setField('ps', ps):
            return slemp.returnJson(True, 'Successfully modified!')
        return slemp.returnJson(False, 'Fail to edit!')

    def stopApi(self):
        mid = request.form.get('id', '')
        name = request.form.get('name', '')

        return self.stop(mid, name)

    def stop(self, mid, name):
        path = self.setupPath + '/stop'
        if not os.path.exists(path):
            os.makedirs(path)
            default_text = 'The website has been closed!!!'
            slemp.writeFile(path + '/index.html', default_text)

        binding = slemp.M('binding').where('pid=?', (mid,)).field(
            'id,pid,domain,path,port,addtime').select()
        for b in binding:
            bpath = path + '/' + b['path']
            if not os.path.exists(bpath):
                slemp.execShell('mkdir -p ' + bpath)
                slemp.execShell('ln -sf ' + path +
                             '/index.html ' + bpath + '/index.html')

        sitePath = slemp.M('sites').where("id=?", (mid,)).getField('path')

        file = self.getHostConf(name)
        conf = slemp.readFile(file)
        if conf:
            conf = conf.replace(sitePath, path)
            slemp.writeFile(file, conf)

        slemp.M('sites').where("id=?", (mid,)).setField('status', '0')
        slemp.restartWeb()
        msg = slemp.getInfo('Site [{1}] has been disabled!', (name,))
        slemp.writeLog('Website management', msg)
        return slemp.returnJson(True, 'Site disabled!')

    def startApi(self):
        mid = request.form.get('id', '')
        name = request.form.get('name', '')
        path = self.setupPath + '/stop'
        sitePath = slemp.M('sites').where("id=?", (mid,)).getField('path')

        file = self.getHostConf(name)
        conf = slemp.readFile(file)
        if conf:
            conf = conf.replace(path, sitePath)
            slemp.writeFile(file, conf)

        slemp.M('sites').where("id=?", (mid,)).setField('status', '1')
        slemp.restartWeb()
        msg = slemp.getInfo('Site [{1}] has been enabled!', (name,))
        slemp.writeLog('Website management', msg)
        return slemp.returnJson(True, 'Site enabled!')

    def getBackupApi(self):
        limit = request.form.get('limit', '')
        p = request.form.get('p', '')
        mid = request.form.get('search', '')

        find = slemp.M('sites').where("id=?", (mid,)).field(
            "id,name,path,status,ps,addtime,edate").find()

        start = (int(p) - 1) * (int(limit))
        _list = slemp.M('backup').where('pid=?', (mid,)).field('id,type,name,pid,filename,size,addtime').limit(
            (str(start)) + ',' + limit).order('id desc').select()
        _ret = {}
        _ret['data'] = _list

        count = slemp.M('backup').where("id=?", (mid,)).count()
        info = {}
        info['count'] = count
        info['tojs'] = 'getBackup'
        info['p'] = p
        info['row'] = limit
        _ret['page'] = slemp.getPage(info)
        _ret['site'] = find
        return slemp.getJson(_ret)

    def toBackupApi(self):
        mid = request.form.get('id', '')
        find = slemp.M('sites').where(
            "id=?", (mid,)).field('name,path,id').find()
        fileName = find['name'] + '_' + \
            time.strftime('%Y%m%d_%H%M%S', time.localtime()) + '.zip'
        backupPath = slemp.getBackupDir() + '/site'
        zipName = backupPath + '/' + fileName
        if not (os.path.exists(backupPath)):
            os.makedirs(backupPath)
        tmps = slemp.getRunDir() + '/tmp/panelExec.log'
        execStr = "cd '" + find['path'] + "' && zip '" + \
            zipName + "' -r ./* > " + tmps + " 2>&1"
        # print execStr
        slemp.execShell(execStr)

        if os.path.exists(zipName):
            fsize = os.path.getsize(zipName)
        else:
            fsize = 0
        sql = slemp.M('backup').add('type,name,pid,filename,size,addtime',
                                 (0, fileName, find['id'], zipName, fsize, slemp.getDate()))

        msg = slemp.getInfo('Backup site [{1}] succeeded!', (find['name'],))
        slemp.writeLog('Website management', msg)
        return slemp.returnJson(True, 'Backup successful!')

    def delBackupApi(self):
        mid = request.form.get('id', '')
        filename = slemp.M('backup').where(
            "id=?", (mid,)).getField('filename')
        if os.path.exists(filename):
            os.remove(filename)
        name = slemp.M('backup').where("id=?", (mid,)).getField('name')
        msg = slemp.getInfo('Backup [{2}] of site [{1}] deleted successfully!', (name, filename))
        slemp.writeLog('Website management', msg)
        slemp.M('backup').where("id=?", (mid,)).delete()
        return slemp.returnJson(True, 'Site deleted successfully!')

    def getPhpVersionApi(self):
        data = self.getPhpVersion()
        return slemp.getJson(data)

    def setPhpVersionApi(self):
        siteName = request.form.get('siteName', '')
        version = request.form.get('version', '')

        file = self.getHostConf(siteName)
        conf = slemp.readFile(file)
        if conf:
            rep = "enable-php-(.*)\.conf"
            tmp = re.search(rep, conf).group()
            conf = conf.replace(tmp, 'enable-php-' + version + '.conf')
            slemp.writeFile(file, conf)

        msg = slemp.getInfo('Successfully switched the PHP version of website [{1}] to PHP-{2}', (siteName, version))
        slemp.writeLog("Website management", msg)
        slemp.restartWeb()
        return slemp.returnJson(True, msg)

    def getDomainApi(self):
        pid = request.form.get('pid', '')
        return self.getDomain(pid)

    def getSiteDomainsApi(self):
        pid = request.form.get('id', '')

        data = {}
        domains = slemp.M('domain').where(
            'pid=?', (pid,)).field('name,id').select()
        binding = slemp.M('binding').where(
            'pid=?', (pid,)).field('domain,id').select()
        if type(binding) == str:
            return binding
        for b in binding:
            tmp = {}
            tmp['name'] = b['domain']
            tmp['id'] = b['id']
            domains.append(tmp)
        data['domains'] = domains
        data['email'] = slemp.M('users').getField('email')
        if data['email'] == 'dentix.id@gmail.com':
            data['email'] = ''
        return slemp.returnJson(True, 'OK', data)

    def getDirBindingApi(self):
        mid = request.form.get('id', '')

        path = slemp.M('sites').where('id=?', (mid,)).getField('path')
        if not os.path.exists(path):
            checks = ['/', '/usr', '/etc']
            if path in checks:
                data = {}
                data['dirs'] = []
                data['binding'] = []
                return slemp.returnJson(True, 'OK', data)
            os.system('mkdir -p ' + path)
            os.system('chmod 755 ' + path)
            os.system('chown www:www ' + path)
            siteName = slemp.M('sites').where(
                'id=?', (get.id,)).getField('name')
            slemp.writeLog(
                'Website management', 'Site [' + siteName + '], root directory [' + path + '] does not exist, has been recreated!')

        dirnames = []
        for filename in os.listdir(path):
            try:
                filePath = path + '/' + filename
                if os.path.islink(filePath):
                    continue
                if os.path.isdir(filePath):
                    dirnames.append(filename)
            except:
                pass

        data = {}
        data['dirs'] = dirnames
        data['binding'] = slemp.M('binding').where('pid=?', (mid,)).field(
            'id,pid,domain,path,port,addtime').select()
        return slemp.returnJson(True, 'OK', data)

    def getDirUserIniApi(self):
        mid = request.form.get('id', '')

        path = slemp.M('sites').where('id=?', (mid,)).getField('path')
        name = slemp.M('sites').where("id=?", (mid,)).getField('name')
        data = {}
        data['logs'] = self.getLogsStatus(name)
        data['runPath'] = self.getSiteRunPath(mid)

        data['userini'] = False
        if os.path.exists(path + '/.user.ini'):
            data['userini'] = True

        if data['runPath']['runPath'] != '/':
            if os.path.exists(path + data['runPath']['runPath'] + '/.user.ini'):
                data['userini'] = True

        data['pass'] = self.getHasPwd(name)
        data['path'] = path
        data['name'] = name
        return slemp.returnJson(True, 'OK', data)

    def setDirUserIniApi(self):
        path = request.form.get('path', '')
        runPath = request.form.get('runPath', '')
        filename = path + '/.user.ini'

        if os.path.exists(filename):
            self.delUserInI(path)
            slemp.execShell("which chattr && chattr -i " + filename)
            os.remove(filename)
            return slemp.returnJson(True, 'Anti-cross-site setting has been cleared!')

        self.setDirUserINI(path, runPath)
        slemp.execShell("which chattr && chattr +i " + filename)

        return slemp.returnJson(True, 'The anti-cross-site setting is turned on!')

    def setRewriteApi(self):
        data = request.form.get('data', '')
        path = request.form.get('path', '')
        encoding = request.form.get('encoding', '')
        if not os.path.exists(path):
            slemp.writeFile(path, '')

        slemp.backFile(path)
        slemp.writeFile(path, data)
        isError = slemp.checkWebConfig()
        if(type(isError) == str):
            slemp.restoreFile(path)
            return slemp.returnJson(False, 'ERROR: <br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')
        slemp.restartWeb()
        return slemp.returnJson(True, 'Successfully set!')

    def setRewriteTplApi(self):
        data = request.form.get('data', '')
        name = request.form.get('name', '')
        path = slemp.getRunDir() + "/rewrite/nginx/" + name + ".conf"
        if os.path.exists(path):
            return slemp.returnJson(False, 'Template already exists!')

        if data == "":
            return slemp.returnJson(False, 'Template content cannot be empty!')
        ok = slemp.writeFile(path, data)
        if not ok:
            return slemp.returnJson(False, 'Template keeps failing!')

        return slemp.returnJson(True, 'Set template successfully!')

    def logsOpenApi(self):
        mid = request.form.get('id', '')
        name = slemp.M('sites').where("id=?", (mid,)).getField('name')

        filename = self.getHostConf(name)
        if os.path.exists(filename):
            conf = slemp.readFile(filename)
            rep = self.logsPath + "/" + name + ".log"
            if conf.find(rep) != -1:
                conf = conf.replace(rep + " main", "off")
            else:
                conf = conf.replace('access_log  off',
                                    'access_log  ' + rep + " main")
            slemp.writeFile(filename, conf)

        slemp.restartWeb()
        return slemp.returnJson(True, 'Successful operation!')

    def getCertListApi(self):
        try:
            vpath = self.sslDir
            if not os.path.exists(vpath):
                os.system('mkdir -p ' + vpath)
            data = []
            for d in os.listdir(vpath):

                # keyPath = self.sslDir + siteName + '/privkey.pem'
                # certPath = self.sslDir + siteName + '/fullchain.pem'

                keyPath = vpath + '/' + d + '/privkey.pem'
                certPath = vpath + '/' + d + '/fullchain.pem'
                if os.path.exists(keyPath) and os.path.exists(certPath):
                    self.saveCert(keyPath, certPath)

                mpath = vpath + '/' + d + '/info.json'
                if not os.path.exists(mpath):
                    continue

                tmp = slemp.readFile(mpath)
                if not tmp:
                    continue
                tmp1 = json.loads(tmp)
                data.append(tmp1)
            return slemp.returnJson(True, 'OK', data)
        except:
            return slemp.returnJson(True, 'OK', [])

    def deleteSslApi(self):
        site_name = request.form.get('site_name', '')
        ssl_type = request.form.get('ssl_type', '')

        path = self.sslDir + '/' + site_name
        csr_path = path + '/fullchain.pem'

        file = self.getHostConf(site_name)
        content = slemp.readFile(file)
        key_text = 'ssl_certificate'
        status = True
        if content.find(key_text) == -1:
            status = False

        if ssl_type == 'now':
            if status:
                return slemp.returnJson(False, 'In use, first close and then delete')
            if os.path.exists(path):
                slemp.execShell('rm -rf ' + path)
            else:
                return slemp.returnJson(False, 'Not yet applied!')
        elif ssl_type == 'lets':
            ssl_lets_dir = self.sslLetsDir + '/' + site_name
            csr_lets_path = ssl_lets_dir + '/fullchain.pem'
            if slemp.md5(slemp.readFile(csr_lets_path)) == slemp.md5(slemp.readFile(csr_path)):
                return slemp.returnJson(False, 'In use, first close and then delete')
            slemp.execShell('rm -rf ' + ssl_lets_dir)
        elif ssl_type == 'acme':
            ssl_acme_dir = slemp.getAcmeDomainDir(site_name)
            csr_acme_path = ssl_acme_dir + '/fullchain.cer'
            if slemp.md5(slemp.readFile(csr_acme_path)) == slemp.md5(slemp.readFile(csr_path)):
                return slemp.returnJson(False, 'In use, first close and then delete')
            slemp.execShell('rm -rf ' + ssl_acme_dir)

        # slemp.restartWeb()
        return slemp.returnJson(True, 'Successfully deleted')

    def getSslApi(self):
        site_name = request.form.get('site_name', '')
        ssl_type = request.form.get('ssl_type', '')

        path = self.sslDir + '/' + site_name

        file = self.getHostConf(site_name)
        content = slemp.readFile(file)

        key_text = 'ssl_certificate'
        status = True
        stype = 0
        if content.find(key_text) == -1:
            status = False
            stype = -1

        to_https = self.isToHttps(site_name)
        sid = slemp.M('sites').where("name=?", (site_name,)).getField('id')
        domains = slemp.M('domain').where("pid=?", (sid,)).field('name').select()

        csr_path = path + '/fullchain.pem'
        key_path = path + '/privkey.pem'

        cert_data = None
        if ssl_type == 'lets':
            csr_path = self.sslLetsDir + '/' + site_name + '/fullchain.pem'
            key_path = self.sslLetsDir + '/' + site_name + '/privkey.pem'
        elif ssl_type == 'acme':
            acme_dir = slemp.getAcmeDomainDir(site_name)
            csr_path = acme_dir + '/fullchain.cer'
            key_path = acme_dir + '/' + site_name + '.key'

        key = slemp.readFile(key_path)
        csr = slemp.readFile(csr_path)
        cert_data = slemp.getCertName(csr_path)
        data = {
            'status': status,
            'domain': domains,
            'key': key,
            'csr': csr,
            'type': stype,
            'httpTohttps': to_https,
            'cert_data': cert_data,
        }
        return slemp.returnJson(True, 'OK', data)

    def setSslApi(self):
        siteName = request.form.get('siteName', '')

        key = request.form.get('key', '')
        csr = request.form.get('csr', '')

        path = self.sslDir + '/' + siteName
        if not os.path.exists(path):
            slemp.execShell('mkdir -p ' + path)

        csrpath = path + "/fullchain.pem"
        keypath = path + "/privkey.pem"

        if(key.find('KEY') == -1):
            return slemp.returnJson(False, 'The key is wrong, please check!')
        if(csr.find('CERTIFICATE') == -1):
            return slemp.returnJson(False, 'Certificate error, please check!')

        slemp.writeFile('/tmp/cert.pl', csr)
        if not slemp.checkCert('/tmp/cert.pl'):
            return slemp.returnJson(False, 'Certificate error, please paste the correct certificate in PEM format!')

        slemp.backFile(keypath)
        slemp.backFile(csrpath)

        slemp.writeFile(keypath, key)
        slemp.writeFile(csrpath, csr)

        result = self.setSslConf(siteName)
        if not result['status']:
            return slemp.getJson(result)

        isError = slemp.checkWebConfig()
        if(type(isError) == str):
            slemp.restoreFile(keypath)
            slemp.restoreFile(csrpath)
            return slemp.returnJson(False, 'ERROR: <br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')

        slemp.writeLog('Website management', 'Certificate saved!')
        slemp.restartWeb()
        return slemp.returnJson(True, 'Certificate saved!')

    def setCertToSiteApi(self):
        certName = request.form.get('certName', '')
        siteName = request.form.get('siteName', '')
        try:
            path = self.sslDir + '/' + siteName.strip()
            if not os.path.exists(path):
                return slemp.returnJson(False, 'Certificate does not exist!')

            result = self.setSslConf(siteName)
            if not result['status']:
                return slemp.getJson(result)

            slemp.restartWeb()
            slemp.writeLog('Website management', 'The certificate is deployed!')
            return slemp.returnJson(True, 'The certificate is deployed!')
        except Exception as ex:
            return slemp.returnJson(False, 'Setting error: ' + str(ex))

    def removeCertApi(self):
        certName = request.form.get('certName', '')
        try:
            path = self.sslDir + '/' + certName
            if not os.path.exists(path):
                return slemp.returnJson(False, 'Certificate no longer exists!')
            os.system("rm -rf " + path)
            return slemp.returnJson(True, 'Certificate deleted!')
        except:
            return slemp.returnJson(False, 'Failed to delete!')

    def closeSslConfApi(self):
        siteName = request.form.get('siteName', '')

        file = self.getHostConf(siteName)
        conf = slemp.readFile(file)

        if conf:
            rep = "\n\s*#HTTP_TO_HTTPS_START(.|\n){1,300}#HTTP_TO_HTTPS_END"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_certificate\s+.+;\s+ssl_certificate_key\s+.+;"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_protocols\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_ciphers\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_prefer_server_ciphers\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_session_cache\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_session_timeout\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_ecdh_curve\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_session_tickets\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_stapling\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_stapling_verify\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+add_header\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+add_header\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl\s+on;"
            conf = re.sub(rep, '', conf)
            rep = "\s+error_page\s497.+;"
            conf = re.sub(rep, '', conf)
            rep = "\s+if.+server_port.+\n.+\n\s+\s*}"
            conf = re.sub(rep, '', conf)
            rep = "\s+listen\s+443.*;"
            conf = re.sub(rep, '', conf)
            rep = "\s+listen\s+\[\:\:\]\:443.*;"
            conf = re.sub(rep, '', conf)
            slemp.writeFile(file, conf)

        msg = slemp.getInfo('Website [{1}] closed SSL successfully!', (siteName,))
        slemp.writeLog('Website management', msg)
        slemp.restartWeb()
        return slemp.returnJson(True, 'SSL is turned off!')

    def deploySslApi(self):
        site_name = request.form.get('site_name', '')
        ssl_type = request.form.get('ssl_type', '')

        path = self.sslDir + '/' + site_name
        csr_path = path + '/fullchain.pem'
        key_path = path + '/privkey.pem'

        if not os.path.exists(path):
            os.makedirs(path)

        if ssl_type == 'lets':
            ssl_lets_dir = self.sslLetsDir + '/' + site_name
            lets_csrpath = ssl_lets_dir + '/fullchain.pem'
            lets_keypath = ssl_lets_dir + '/privkey.pem'
            if slemp.md5(slemp.readFile(lets_csrpath)) == slemp.md5(slemp.readFile(csr_path)):
                return slemp.returnJson(False, 'Deployed Lets')
            else:

                slemp.buildSoftLink(lets_csrpath, csr_path, True)
                slemp.buildSoftLink(lets_keypath, key_path, True)
                slemp.execShell('echo "lets" > "' + path + '/README"')
        elif ssl_type == 'acme':
            ssl_acme_dir = slemp.getAcmeDir() + '/' + site_name
            if not os.path.exists(ssl_acme_dir):
                ssl_acme_dir = slemp.getAcmeDir() + '/' + site_name + '_ecc'
            acme_csrpath = ssl_acme_dir + '/fullchain.cer'
            acme_keypath = ssl_acme_dir + '/' + site_name + '.key'
            if slemp.md5(slemp.readFile(acme_csrpath)) == slemp.md5(slemp.readFile(csr_path)):
                return slemp.returnJson(False, 'ACME deployed')
            else:
                slemp.buildSoftLink(acme_csrpath, csr_path, True)
                slemp.buildSoftLink(acme_keypath, key_path, True)
                slemp.execShell('echo "acme" > "' + path + '/README"')

        result = self.setSslConf(site_name)
        if not result['status']:
            return slemp.getJson(result)
        return slemp.returnJson(True, 'Successful deployment')

    def getLetsIndex(self, site_name):
        cfg = slemp.getRunDir() + '/data/letsencrypt.json'
        if not os.path.exists(cfg):
            return False

        data = slemp.readFile(cfg)
        lets_data = json.loads(data)
        order_list = lets_data['orders']

        for x in order_list:
            if order_list[x]['status'] == 'valid':
                for d in order_list[x]['domains']:
                    if d == site_name:
                        return x
        return False

    def renewSslApi(self):
        site_name = request.form.get('site_name', '')
        ssl_type = request.form.get('ssl_type', '')
        if ssl_type == 'lets':
            index = self.getLetsIndex(site_name)
            if index:
                import cert_api
                data = cert_api.cert_api().renewCert(index)
                return data
            else:
                return slemp.returnJson(False, 'Invalid operation')

        return slemp.returnJson(True, 'Renewed successfully')

    def getLetLogsApi(self):
        log_file = slemp.getRunDir() + '/logs/letsencrypt.log'
        if not os.path.exists(log_file):
            slemp.execShell('touch ' + log_file)
        return slemp.returnJson(True, 'OK', log_file)

    def createLetApi(self):
        siteName = request.form.get('siteName', '')
        domains = request.form.get('domains', '')
        force = request.form.get('force', '')
        renew = request.form.get('renew', '')
        email_args = request.form.get('email', '')

        domains = json.loads(domains)
        email = slemp.M('users').getField('email')
        if email_args.strip() != '':
            slemp.M('users').setField('email', email_args)
            email = email_args

        if not len(domains):
            return slemp.returnJson(False, 'Please select a domain name')

        host_conf_file = self.getHostConf(siteName)
        if os.path.exists(host_conf_file):
            siteConf = slemp.readFile(host_conf_file)
            if siteConf.find('301-END') != -1:
                return slemp.returnJson(False, 'It is detected that your site has made a 301 redirection setting, please close the redirection first!')

            data_path = self.getProxyDataPath(siteName)
            data_content = slemp.readFile(data_path)
            if data_content != False:
                try:
                    data = json.loads(data_content)
                except:
                    pass
                for proxy in data:
                    proxy_dir = "{}/{}".format(self.proxyPath, siteName)
                    proxy_dir_file = proxy_dir + '/' + proxy['id'] + '.conf'
                    if os.path.exists(proxy_dir_file):
                        return slemp.returnJson(False, 'It is detected that your site has a reverse proxy setting, please close the reverse proxy first!')

            # fix binddir domain ssl apply question
            slemp.backFile(host_conf_file)
            auth_to = self.getSitePath(siteName)
            rep = "\s*root\s*(.+);"
            replace_root = "\n\troot " + auth_to + ";"
            siteConf = re.sub(rep, replace_root, siteConf)
            slemp.writeFile(host_conf_file, siteConf)
            slemp.restartWeb()

        to_args = {
            'domains': domains,
            'auth_type': 'http',
            'auth_to': auth_to,
        }

        src_letpath = slemp.getServerDir() + '/web_conf/letsencrypt/' + siteName
        src_csrpath = src_letpath + "/fullchain.pem"
        src_keypath = src_letpath + "/privkey.pem"

        dst_letpath = self.sslDir + '/' + siteName
        dst_csrpath = dst_letpath + '/fullchain.pem'
        dst_keypath = dst_letpath + '/privkey.pem'

        if not os.path.exists(src_letpath):
            import cert_api
            data = cert_api.cert_api().applyCertApi(to_args)
            slemp.restoreFile(host_conf_file)
            if not data['status']:
                msg = data['msg']
                if type(data['msg']) != str:
                    msg = data['msg'][0]
                    emsg = data['msg'][1]['challenges'][0]['error']
                    msg = msg + '<p><span>Response status: </span>' + str(emsg['status']) + '</p><p><span>Error type :</span>' + emsg[
                        'type'] + '</p><p><span>Error code :</span>' + emsg['detail'] + '</p>'
                return slemp.returnJson(data['status'], msg, data['msg'])

        slemp.execShell('mkdir -p ' + dst_letpath)
        slemp.buildSoftLink(src_csrpath, dst_csrpath, True)
        slemp.buildSoftLink(src_keypath, dst_keypath, True)
        slemp.execShell('echo "lets" > "' + dst_letpath + '/README"')

        result = self.setSslConf(siteName)
        if not result['status']:
            return slemp.getJson(result)

        result['csr'] = slemp.readFile(src_csrpath)
        result['key'] = slemp.readFile(src_keypath)

        slemp.restartWeb()
        return slemp.returnJson(data['status'], data['msg'], result)

    def getAcmeLogsApi(self):
        log_file = slemp.getRunDir() + '/logs/acme.log'
        if not os.path.exists(log_file):
            slemp.execShell('touch ' + log_file)
        return slemp.returnJson(True, 'OK', log_file)

    def createAcmeApi(self):
        siteName = request.form.get('siteName', '')
        domains = request.form.get('domains', '')
        force = request.form.get('force', '')
        renew = request.form.get('renew', '')
        email_args = request.form.get('email', '')

        domains = json.loads(domains)
        email = slemp.M('users').getField('email')
        if email_args.strip() != '':
            slemp.M('users').setField('email', email_args)
            email = email_args

        if not len(domains):
            return slemp.returnJson(False, 'Please select a domain name')

        file = self.getHostConf(siteName)
        if os.path.exists(file):
            siteConf = slemp.readFile(file)
            if siteConf.find('301-END') != -1:
                return slemp.returnJson(False, 'It is detected that your site has made a 301 redirection setting, please close the redirection first!')

            data_path = self.getProxyDataPath(siteName)
            data_content = slemp.readFile(data_path)
            if data_content != False:
                try:
                    data = json.loads(data_content)
                except:
                    pass
                for proxy in data:
                    proxy_dir = "{}/{}".format(self.proxyPath, siteName)
                    proxy_dir_file = proxy_dir + '/' + proxy['id'] + '.conf'
                    if os.path.exists(proxy_dir_file):
                        return slemp.returnJson(False, 'It is detected that your site has a reverse proxy setting, please close the reverse proxy first!')

        siteInfo = slemp.M('sites').where(
            'name=?', (siteName,)).field('id,name,path').find()
        path = self.getSitePath(siteName)
        srcPath = siteInfo['path']

        acme_dir = slemp.getAcmeDir()
        if not os.path.exists(acme_dir):
            try:
                slemp.execShell("curl -sS curl https://get.acme.sh | sh")
            except:
                pass
        if not os.path.exists(acme_dir):
            return slemp.returnJson(False, 'Attempt to install ACME automatically failed, please try to install manually with the following command<p>installation command: curl https://get.acme.sh | sh</p>')

        checkAcmeRun = slemp.execShell('ps -ef | grep acme.sh | grep -v grep')
        if checkAcmeRun[0] != '':
            return slemp.returnJson(False, 'Applying for or renewing SSL...')

        if force == 'true':
            force_bool = True

        if renew == 'true':
            execStr = acme_dir + "/acme.sh --renew --yes-I-know-dns-manual-mode-enough-go-ahead-please"
        else:
            execStr = acme_dir + "/acme.sh --issue --force"

        domainsTmp = []
        if siteName in domains:
            domainsTmp.append(siteName)
        for domainTmp in domains:
            if domainTmp == siteName:
                continue
            domainsTmp.append(domainTmp)
        domains = domainsTmp

        domainCount = 0
        for domain in domains:
            if slemp.checkIp(domain):
                continue
            if domain.find('*.') != -1:
                return slemp.returnJson(False, 'Generic domain names cannot apply for a certificate using [File Verification]!')
            execStr += ' -w ' + path
            execStr += ' -d ' + domain
            domainCount += 1
        if domainCount == 0:
            return slemp.returnJson(False, 'Please select a domain name (excluding IP address and generic domain name)!')

        log_file = slemp.getRunDir() + '/logs/acme.log'
        slemp.writeFile(log_file, "Start ACME Application...\n", "wb+")
        cmd = 'export ACCOUNT_EMAIL=' + email + ' && ' + \
            execStr + ' >> ' + log_file
        # print(domains)
        # print(cmd)
        result = slemp.execShell(cmd)

        src_path = slemp.getAcmeDomainDir(domains[0])
        src_cert = src_path + '/fullchain.cer'
        src_key = src_path + '/' + domains[0] + '.key'
        src_cert.replace("\*", "*")

        msg = 'Issuance failed, and the number of failed attempts to apply for a certificate has reached the upper limit! <p>1. Check whether the domain name is bound to the corresponding site</p>\
            <p>2. Check whether the domain name is correctly resolved to this server, or the resolution has not fully taken effect</p>\
            <p>3. If your site has a reverse proxy or CDN, please close it first</p>\
            <p>4. If your site has 301 redirection, please close it first</p>\
            <p>5. If the above checks confirm that there is no problem, please try to change the DNS service provider</p>'
        if not os.path.exists(src_cert):
            data = {}
            data['err'] = result
            data['out'] = result[0]
            data['msg'] = msg
            data['result'] = {}
            if result[1].find('new-authz error:') != -1:
                data['result'] = json.loads(
                    re.search("{.+}", result[1]).group())
                if data['result']['status'] == 429:
                    data['msg'] = msg
            data['status'] = False
            return slemp.getJson(data)

        dst_path = self.sslDir + '/' + siteName
        dst_cert = dst_path + "/fullchain.pem"
        dst_key = dst_path + "/privkey.pem"

        if not os.path.exists(dst_path):
            slemp.execShell("mkdir -p " + dst_path)

        slemp.buildSoftLink(src_cert, dst_cert, True)
        slemp.buildSoftLink(src_key, dst_key, True)
        slemp.execShell('echo "acme" > "' + dst_path + '/README"')

        result = self.setSslConf(siteName)
        if not result['status']:
            return slemp.getJson(result)
        result['csr'] = slemp.readFile(src_cert)
        result['key'] = slemp.readFile(src_key)

        slemp.restartWeb()
        return slemp.returnJson(True, 'Certificate updated!', result)

    def httpToHttpsApi(self):
        siteName = request.form.get('siteName', '')
        return self.httpToHttps(siteName)

    def httpToHttps(self, site_name):
        file = self.getHostConf(site_name)
        conf = slemp.readFile(file)
        if conf:
            if conf.find('ssl_certificate') == -1:
                return slemp.returnJson(False, 'SSL is not currently enabled')
            to = "#error_page 404/404.html;\n\
    #HTTP_TO_HTTPS_START\n\
    if ($server_port !~ 443){\n\
        rewrite ^(/.*)$ https://$host$1 permanent;\n\
    }\n\
    #HTTP_TO_HTTPS_END"
            conf = conf.replace('#error_page 404/404.html;', to)
            slemp.writeFile(file, conf)

        slemp.restartWeb()
        return slemp.returnJson(True, 'Successfully set!')

    def closeToHttpsApi(self):
        siteName = request.form.get('siteName', '')
        return self.closeToHttps(siteName)

    def closeToHttps(self, site_name):
        file = self.getHostConf(site_name)
        conf = slemp.readFile(file)
        if conf:
            rep = "\n\s*#HTTP_TO_HTTPS_START(.|\n){1,300}#HTTP_TO_HTTPS_END"
            conf = re.sub(rep, '', conf)
            rep = "\s+if.+server_port.+\n.+\n\s+\s*}"
            conf = re.sub(rep, '', conf)
            slemp.writeFile(file, conf)

        slemp.restartWeb()
        return slemp.returnJson(True, 'Turn off HTTPS and jump successfully!')

    def getIndexApi(self):
        sid = request.form.get('id', '')
        data = {}
        index = self.getIndex(sid)
        data['index'] = index
        return slemp.getJson(data)

    def setIndexApi(self):
        sid = request.form.get('id', '')
        index = request.form.get('index', '')
        return self.setIndex(sid, index)

    def getLimitNetApi(self):
        sid = request.form.get('id', '')
        return self.getLimitNet(sid)

    def saveLimitNetApi(self):
        sid = request.form.get('id', '')
        perserver = request.form.get('perserver', '')
        perip = request.form.get('perip', '')
        limit_rate = request.form.get('limit_rate', '')
        return self.saveLimitNet(sid, perserver, perip, limit_rate)

    def closeLimitNetApi(self):
        sid = request.form.get('id', '')
        return self.closeLimitNet(sid)

    def getSecurityApi(self):
        sid = request.form.get('id', '')
        name = request.form.get('name', '')
        return self.getSecurity(sid, name)

    def setSecurityApi(self):
        fix = request.form.get('fix', '')
        domains = request.form.get('domains', '')
        status = request.form.get('status', '')
        name = request.form.get('name', '')
        sid = request.form.get('id', '')
        return self.setSecurity(sid, name, fix, domains, status)

    def getLogsApi(self):
        siteName = request.form.get('siteName', '')
        return self.getLogs(siteName)

    def getErrorLogsApi(self):
        siteName = request.form.get('siteName', '')
        return self.getErrorLogs(siteName)

    def getSitePhpVersionApi(self):
        siteName = request.form.get('siteName', '')
        return self.getSitePhpVersion(siteName)

    def getHostConfApi(self):
        siteName = request.form.get('siteName', '')
        host = self.getHostConf(siteName)
        return slemp.getJson({'host': host})

    def saveHostConfApi(self):
        path = request.form.get('path', '')
        data = request.form.get('data', '')
        encoding = request.form.get('encoding', '')

        import files_api

        slemp.backFile(path)
        save_ret_data = files_api.files_api().saveBody(path, data, encoding)
        rdata = json.loads(save_ret_data)

        if rdata['status']:
            isError = slemp.checkWebConfig()
            if isError != True:
                slemp.restoreFile(path)
                return slemp.returnJson(False, 'ERROR: An error has been detected in the configuration file, please troubleshoot before proceeding<br><br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')
            slemp.restartWeb()
            slemp.removeBackFile(path)
        return save_ret_data

    def getRewriteConfApi(self):
        siteName = request.form.get('siteName', '')
        rewrite = self.getRewriteConf(siteName)
        return slemp.getJson({'rewrite': rewrite})

    def getRewriteTplApi(self):
        tplname = request.form.get('tplname', '')
        file = slemp.getRunDir() + '/rewrite/nginx/' + tplname + '.conf'
        if not os.path.exists(file):
            return slemp.returnJson(False, 'Template does not exist!')
        return slemp.returnJson(True, 'OK', file)

    def getRewriteListApi(self):
        rlist = self.getRewriteList()
        return slemp.getJson(rlist)

    def getRootDirApi(self):
        data = {}
        data['dir'] = slemp.getWwwDir()
        return slemp.getJson(data)

    def setEndDateApi(self):
        sid = request.form.get('id', '')
        edate = request.form.get('edate', '')
        return self.setEndDate(sid, edate)

    def addApi(self):
        webname = request.form.get('webinfo', '')
        ps = request.form.get('ps', '')
        path = request.form.get('path', '')
        version = request.form.get('version', '')
        port = request.form.get('port', '')
        return self.add(webname, port, ps, path, version)

    def checkWebStatusApi(self):
        '''
        create site check web service
        '''
        if not slemp.isInstalledWeb():
            return slemp.returnJson(False, 'Please install and start the OpenResty service!')

        pid = slemp.getServerDir() + '/openresty/nginx/logs/nginx.pid'
        if not os.path.exists(pid):
            return slemp.returnJson(False, 'Please start the OpenResty service!')

        # path = slemp.getServerDir() + '/openresty/init.d/openresty'
        # data = slemp.execShell(path + " status")
        # if data[0].strip().find('stopped') != -1:
        #     return slemp.returnJson(False, 'Please start the OpenResty service!')

        # import plugins_api
        # data = plugins_api.plugins_api().run('openresty', 'status')
        # if data[0].strip() == 'stop':
        #     return slemp.returnJson(False, 'Please start the OpenResty service!')

        return slemp.returnJson(True, 'OK')

    def addDomainApi(self):
        isError = slemp.checkWebConfig()
        if isError != True:
            return slemp.returnJson(False, 'ERROR: An error has been detected in the configuration file, please troubleshoot before proceeding<br><br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')

        domain = request.form.get('domain', '')
        webname = request.form.get('webname', '')
        pid = request.form.get('id', '')
        return self.addDomain(domain, webname, pid)

    def addDomain(self, domain, webname, pid):
        if len(domain) < 3:
            return slemp.returnJson(False, 'Domain name cannot be empty!')
        domains = domain.split(',')
        for domain in domains:
            if domain == "":
                continue
            domain = domain.split(':')
            # print domain
            domain_name = self.toPunycode(domain[0])
            domain_port = '80'

            reg = "^([\w\-\*]{1,100}\.){1,4}([\w\-]{1,24}|[\w\-]{1,24}\.[\w\-]{1,24})$"
            if not re.match(reg, domain_name):
                return slemp.returnJson(False, 'The domain name format is incorrect!')

            if len(domain) == 2:
                domain_port = domain[1]
            if domain_port == "":
                domain_port = "80"

            if not slemp.checkPort(domain_port):
                return slemp.returnJson(False, 'Invalid port range!')

            opid = slemp.M('domain').where(
                "name=? AND (port=? OR pid=?)", (domain_name, domain_port, pid,)).getField('pid')
            # print(opid)
            is_bind = False
            if type(opid) == list and len(opid) > 0:
                is_bind = True

            if type(opid) == int and opid > 0:
                is_bind = True

            if type(opid) == str and int(opid) > 0:
                is_bind = True

            if is_bind:
                return slemp.returnJson(False, 'The domain name [{}] you added has been bound!'.format(domain_name))
                # if slemp.M('sites').where('id=?', (opid,)).count():
                #     return slemp.returnJson(False, 'The specified domain name has been bound!')
                # slemp.M('domain').where('pid=?', (opid,)).delete()

            if slemp.M('binding').where('domain=?', (domain,)).count():
                return slemp.returnJson(False, 'The domain name you added, the subdirectory has been bound!')

            self.nginxAddDomain(webname, domain_name, domain_port)

            slemp.restartWeb()
            msg = slemp.getInfo('Website [{1}] successfully added domain name [{2}]!', (webname, domain_name))
            slemp.writeLog('Website management', msg)
            slemp.M('domain').add('pid,name,port,addtime',
                               (pid, domain_name, domain_port, slemp.getDate()))

        self.runHook('site_cb', 'add')
        return slemp.returnJson(True, 'Domain name added successfully!')

    def addDirBindApi(self):
        pid = request.form.get('id', '')
        domain = request.form.get('domain', '')
        dirName = request.form.get('dirName', '')
        tmp = domain.split(':')
        domain = tmp[0]
        port = '80'
        if len(tmp) > 1:
            port = tmp[1]
        if dirName == '':
            slemp.returnJson(False, 'Directory cannot be empty!')

        reg = "^([\w\-\*]{1,100}\.){1,4}(\w{1,10}|\w{1,10}\.\w{1,10})$"
        if not re.match(reg, domain):
            return slemp.returnJson(False, 'Primary domain name format is incorrect!')

        siteInfo = slemp.M('sites').where(
            "id=?", (pid,)).field('id,path,name').find()
        webdir = siteInfo['path'] + '/' + dirName

        if slemp.M('binding').where("domain=?", (domain,)).count() > 0:
            return slemp.returnJson(False, 'The domain you added already exists!')
        if slemp.M('domain').where("name=?", (domain,)).count() > 0:
            return slemp.returnJson(False, 'The domain you added already exists!')

        filename = self.getHostConf(siteInfo['name'])
        conf = slemp.readFile(filename)
        if conf:
            rep = "enable-php-([0-9]{2,3})\.conf"
            tmp = re.search(rep, conf).groups()
            version = tmp[0]

            source_dirbind_tpl = slemp.getRunDir() + '/data/tpl/nginx_dirbind.conf'
            content = slemp.readFile(source_dirbind_tpl)
            content = content.replace('{$PORT}', port)
            content = content.replace('{$PHPVER}', version)
            content = content.replace('{$DIRBIND}', domain)
            content = content.replace('{$ROOT_DIR}', webdir)
            content = content.replace('{$SERVER_MAIN}', siteInfo['name'])
            content = content.replace('{$OR_REWRITE}', self.rewritePath)
            content = content.replace('{$PHP_DIR}', self.setupPath + '/php')
            content = content.replace('{$LOGPATH}', slemp.getLogsDir())

            conf += "\r\n" + content
            slemp.backFile(filename)
            slemp.writeFile(filename, conf)
        conf = slemp.readFile(filename)

        isError = slemp.checkWebConfig()
        if isError != True:
            slemp.restoreFile(filename)
            return slemp.returnJson(False, 'ERROR: <br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')

        slemp.M('binding').add('pid,domain,port,path,addtime',
                            (pid, domain, port, dirName, slemp.getDate()))

        msg = slemp.getInfo('Website [{1}] subdirectory [{2}] is bound to [{3}]',
                         (siteInfo['name'], dirName, domain))
        slemp.writeLog('Website management', msg)
        slemp.restartWeb()
        slemp.removeBackFile(filename)
        return slemp.returnJson(True, 'Added successfully!')

    def delDirBindApi(self):
        mid = request.form.get('id', '')
        binding = slemp.M('binding').where(
            "id=?", (mid,)).field('id,pid,domain,path').find()
        siteName = slemp.M('sites').where(
            "id=?", (binding['pid'],)).getField('name')

        filename = self.getHostConf(siteName)
        conf = slemp.readFile(filename)
        if conf:
            rep = "\s*.+BINDING-" + \
                binding['domain'] + \
                "-START(.|\n)+BINDING-" + binding['domain'] + "-END"
            conf = re.sub(rep, '', conf)
            slemp.writeFile(filename, conf)

        slemp.M('binding').where("id=?", (mid,)).delete()

        filename = self.getDirBindRewrite(siteName,  binding['path'])
        if os.path.exists(filename):
            os.remove(filename)
        slemp.restartWeb()
        msg = slemp.getInfo('Delete website [{1}] subdirectory [{2}] binding',
                         (siteName, binding['path']))
        slemp.writeLog('Website management', msg)
        return slemp.returnJson(True, 'Successfully deleted!')

    def getDirBindRewriteApi(self):
        mid = request.form.get('id', '')
        add = request.form.get('add', '0')
        find = slemp.M('binding').where(
            "id=?", (mid,)).field('id,pid,domain,path').find()
        site = slemp.M('sites').where(
            "id=?", (find['pid'],)).field('id,name,path').find()

        filename = self.getDirBindRewrite(site['name'], find['path'])
        if add == '1':
            slemp.writeFile(filename, '')
            file = self.getHostConf(site['name'])
            conf = slemp.readFile(file)
            domain = find['domain']
            rep = "\n#BINDING-" + domain + \
                "-START(.|\n)+BINDING-" + domain + "-END"
            tmp = re.search(rep, conf).group()
            dirConf = tmp.replace('rewrite/' + site['name'] + '.conf;', 'rewrite/' + site[
                'name'] + '_' + find['path'] + '.conf;')
            conf = conf.replace(tmp, dirConf)
            slemp.writeFile(file, conf)
        data = {}
        data['rewrite_dir'] = self.rewritePath
        data['status'] = False
        if os.path.exists(filename):
            data['status'] = True
            data['data'] = slemp.readFile(filename)
            data['rlist'] = []
            for ds in os.listdir(self.rewritePath):
                if ds[0:1] == '.':
                    continue
                if ds == 'list.txt':
                    continue
                data['rlist'].append(ds[0:len(ds) - 5])
            data['filename'] = filename
        return slemp.getJson(data)

    def setPathApi(self):
        mid = request.form.get('id', '')
        path = request.form.get('path', '')

        path = self.getPath(path)
        if path == "" or mid == '0':
            return slemp.returnJson(False,  "Directory cannot be empty!")

        import files_api
        if not files_api.files_api().checkDir(path):
            return slemp.returnJson(False,  "The system key directory cannot be used as the site directory")

        siteFind = slemp.M("sites").where(
            "id=?", (mid,)).field('path,name').find()
        if siteFind["path"] == path:
            return slemp.returnJson(False,  "Consistent with the original path, without modification!")
        file = self.getHostConf(siteFind['name'])
        conf = slemp.readFile(file)
        if conf:
            conf = conf.replace(siteFind['path'], path)
            slemp.writeFile(file, conf)

        # userIni = path + '/.user.ini'
        # if os.path.exists(userIni):
            # slemp.execShell("chattr -i " + userIni)
        # slemp.writeFile(userIni, 'open_basedir=' + path + '/:/tmp/:/proc/')
        # slemp.execShell('chmod 644 ' + userIni)
        # slemp.execShell('chown root:root ' + userIni)
        # slemp.execShell('chattr +i ' + userIni)

        slemp.restartWeb()
        slemp.M("sites").where("id=?", (mid,)).setField('path', path)
        msg = slemp.getInfo('Modify the physical path of website [{1}] successfully!', (siteFind['name'],))
        slemp.writeLog('Website management', msg)
        return slemp.returnJson(True,  "Successfully set!")

    def setSiteRunPathApi(self):
        mid = request.form.get('id', '')
        runPath = request.form.get('runPath', '')
        siteName = slemp.M('sites').where('id=?', (mid,)).getField('name')
        sitePath = slemp.M('sites').where('id=?', (mid,)).getField('path')

        newPath = sitePath + runPath

        filename = self.getHostConf(siteName)
        if os.path.exists(filename):
            conf = slemp.readFile(filename)
            rep = '\s*root\s*(.+);'
            path = re.search(rep, conf).groups()[0]
            conf = conf.replace(path, newPath)
            slemp.writeFile(filename, conf)

        self.setDirUserINI(sitePath, runPath)

        slemp.restartWeb()
        return slemp.returnJson(True, 'Successfully set!')

    def setHasPwdApi(self):
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        siteName = request.form.get('siteName', '')
        mid = request.form.get('id', '')

        if len(username.strip()) == 0 or len(password.strip()) == 0:
            return slemp.returnJson(False, 'Username or password cannot be empty!')

        if siteName == '':
            siteName = slemp.M('sites').where('id=?', (mid,)).getField('name')

        # self.closeHasPwd(get)
        filename = self.passPath + '/' + siteName + '.pass'
        # print(filename)
        passconf = username + ':' + slemp.hasPwd(password)

        if siteName == 'phpmyadmin':
            configFile = self.getHostConf('phpmyadmin')
        else:
            configFile = self.getHostConf(siteName)

        conf = slemp.readFile(configFile)
        if conf:
            rep = '#error_page   404   /404.html;'
            if conf.find(rep) == -1:
                rep = '#error_page 404/404.html;'
            data = '''
    #AUTH_START
    auth_basic "Authorization";
    auth_basic_user_file %s;
    #AUTH_END''' % (filename,)
            conf = conf.replace(rep, rep + data)
            slemp.writeFile(configFile, conf)

        passDir = self.passPath
        if not os.path.exists(passDir):
            slemp.execShell('mkdir -p ' + passDir)
        slemp.writeFile(filename, passconf)

        slemp.restartWeb()
        msg = slemp.getInfo('Set website [{1}] to require password authentication!', (siteName,))
        slemp.writeLog("Website management", msg)
        return slemp.returnJson(True, 'Successfully set!')

    def closeHasPwdApi(self):
        siteName = request.form.get('siteName', '')
        mid = request.form.get('id', '')
        if siteName == '':
            siteName = slemp.M('sites').where('id=?', (mid,)).getField('name')

        if siteName == 'phpmyadmin':
            configFile = self.getHostConf('phpmyadmin')
        else:
            configFile = self.getHostConf(siteName)

        if os.path.exists(configFile):
            conf = slemp.readFile(configFile)
            rep = "\n\s*#AUTH_START(.|\n){1,200}#AUTH_END"
            conf = re.sub(rep, '', conf)
            slemp.writeFile(configFile, conf)

        slemp.restartWeb()
        msg = slemp.getInfo('Clear password authentication for site [{1}]!', (siteName,))
        slemp.writeLog("Website management", msg)
        return slemp.returnJson(True, 'Successfully set!')

    def delDomainApi(self):
        domain = request.form.get('domain', '')
        webname = request.form.get('webname', '')
        port = request.form.get('port', '')
        pid = request.form.get('id', '')

        find = slemp.M('domain').where("pid=? AND name=?",
                                    (pid, domain)).field('id,name').find()

        domain_count = slemp.M('domain').where("pid=?", (pid,)).count()
        if domain_count == 1:
            return slemp.returnJson(False, 'The last domain name cannot be deleted!')

        file = self.getHostConf(webname)
        conf = slemp.readFile(file)
        if conf:
            rep = "server_name\s+(.+);"
            tmp = re.search(rep, conf).group()
            newServerName = tmp.replace(' ' + domain + ';', ';')
            newServerName = newServerName.replace(' ' + domain + ' ', ' ')
            conf = conf.replace(tmp, newServerName)

            rep = "listen\s+([0-9]+);"
            tmp = re.findall(rep, conf)
            port_count = slemp.M('domain').where(
                'pid=? AND port=?', (pid, port)).count()
            if slemp.inArray(tmp, port) == True and port_count < 2:
                rep = "\n*\s+listen\s+" + port + ";"
                conf = re.sub(rep, '', conf)
            slemp.writeFile(file, conf)

        slemp.M('domain').where("id=?", (find['id'],)).delete()
        msg = slemp.getInfo('Website [{1}] deleted domain name [{2}] successfully!', (webname, domain))
        slemp.writeLog('Website management', msg)
        slemp.restartWeb()
        return slemp.returnJson(True, 'Site deleted successfully!')

    def deleteApi(self):
        sid = request.form.get('id', '')
        webname = request.form.get('webname', '')
        path = request.form.get('path', '0')
        return self.delete(sid, webname, path)

    def operateRedirectConf(self, siteName, method='start'):
        vhost_file = self.vhostPath + '/' + siteName + '.conf'
        content = slemp.readFile(vhost_file)

        cnf_301 = '''#301-START
    include %s/*.conf;
    #301-END''' % (self.getRedirectPath( siteName))

        cnf_301_source = '#301-START'
        # print('operateRedirectConf', content.find('#301-END'))
        if content.find('#301-END') != -1:
            if method == 'stop':
                rep = '#301-START(\n|.){1,500}#301-END'
                content = re.sub(rep, '#301-START', content)
        else:
            if method == 'start':
                content = re.sub(cnf_301_source, cnf_301, content)

        slemp.writeFile(vhost_file, content)

    # get_redirect_status
    def getRedirectApi(self):
        _siteName = request.form.get("siteName", '')

        # read data base
        data_path = self.getRedirectDataPath(_siteName)
        data_content = slemp.readFile(data_path)
        if data_content == False:
            slemp.execShell("mkdir {}/{}".format(self.redirectPath, _siteName))
            return slemp.returnJson(True, "", {"result": [], "count": 0})
        # get
        # conf_path = "{}/{}/*.conf".format(self.redirectPath, siteName)
        # conf_list = glob.glob(conf_path)
        # if conf_list == []:
        #     return slemp.returnJson(True, "", {"result": [], "count": 0})
        try:
            data = json.loads(data_content)
        except:
            slemp.execShell("rm -rf {}/{}".format(self.redirectPath, _siteName))
            return slemp.returnJson(True, "", {"result": [], "count": 0})

        return slemp.returnJson(True, "ok", {"result": data, "count": len(data)})

    def getRedirectConfApi(self):
        _siteName = request.form.get("siteName", '')
        _id = request.form.get("id", '')
        if _id == '' or _siteName == '':
            return slemp.returnJson(False, "Required fields cannot be empty!")

        data = slemp.readFile(
            "{}/{}/{}.conf".format(self.redirectPath, _siteName, _id))
        if data == False:
            return slemp.returnJson(False, "Fetch failed!")
        return slemp.returnJson(True, "ok", {"result": data})

    def saveRedirectConfApi(self):
        _siteName = request.form.get("siteName", '')
        _id = request.form.get("id", '')
        _config = request.form.get("config", "")
        if _id == '' or _siteName == '':
            return slemp.returnJson(False, "Required fields cannot be empty!")

        proxy_file = "{}/{}/{}.conf".format(self.proxyPath, _siteName, _id)
        slemp.backFile(proxy_file)
        slemp.writeFile(proxy_file, _config)
        rule_test = slemp.checkWebConfig()
        if rule_test != True:
            slemp.restoreFile(proxy_file)
            slemp.removeBackFile(proxy_file)
            return slemp.returnJson(False, "OpenResty configuration test failed, please try again: {}".format(rule_test))

        slemp.removeBackFile(proxy_file)
        self.operateRedirectConf(_siteName, 'start')
        slemp.restartWeb()
        return slemp.returnJson(True, "ok")

    # get redirect status
    def setRedirectApi(self):
        _siteName = request.form.get("siteName", '')
        # from (example.com / /test/)
        _from = request.form.get("from", '')
        _to = request.form.get("to", '')              # redirect to
        _type = request.form.get("type", '')          # path / domain
        _rType = request.form.get("r_type", '')       # redirect type
        _keepPath = request.form.get("keep_path", '')  # keep path

        if _siteName == '' or _from == '' or _to == '' or _type == '' or _rType == '':
            return slemp.returnJson(False, "Required fields cannot be empty!")

        data_path = self.getRedirectDataPath(_siteName)
        data_content = slemp.readFile(
            data_path) if os.path.exists(data_path) else ""
        data = json.loads(data_content) if data_content != "" else []

        _rTypeCode = 0 if _rType == "301" else 1
        _typeCode = 0 if _type == "path" else 1
        _keepPath = 1 if _keepPath == "1" else 0

        # check if domain exists in site
        if _typeCode == 1:
            pid = slemp.M('domain').where("name=?", (_siteName,)).field(
                'id,pid,name,port,addtime').select()
            site_domain_lists = slemp.M('domain').where("pid=?", (pid[0]['pid'],)).field(
                'name').select()
            found = False
            for item in site_domain_lists:
                if item['name'] == _from:
                    found = True
                    break
            if found == False:
                return slemp.returnJson(False, "Domain name does not exist!")

        file_content = ""
        # path
        if _typeCode == 0:
            redirect_type = "permanent" if _rTypeCode == 0 else "redirect"
            if not _from.startswith("/"):
                _from = "/{}".format(_from)
            if _keepPath == 1:
                _to = "{}$1".format(_to)
                _from = "{}(.*)".format(_from)
            file_content = "rewrite ^{} {} {};".format(
                _from, _to, redirect_type)
        # domain
        else:
            if _keepPath == 1:
                _to = "{}$request_uri".format(_to)

            redirect_type = "301" if _rTypeCode == 0 else "302"
            _if = "if ($host ~ '^{}')".format(_from)
            _return = "return {} {}; ".format(redirect_type, _to)
            file_content = _if + "{\r\n    " + _return + "\r\n}"

        _id = slemp.md5("{}+{}".format(file_content, _siteName))

        for item in data:
            if item["r_from"] == _from:
                return slemp.returnJson(False, "Repeating rules!")

        rep = "http(s)?\:\/\/([a-zA-Z0-9][-a-zA-Z0-9]{0,62}\.)+([a-zA-Z0-9][a-zA-Z0-9]{0,62})+.?"
        if not re.match(rep, _to):
            return slemp.returnJson(False, "wrong target address")

        # write data json file
        data.append({"r_from": _from, "type": _typeCode, "r_type": _rTypeCode,
                     "r_to": _to, 'keep_path': _keepPath, 'id': _id})
        slemp.writeFile(data_path, json.dumps(data))
        slemp.writeFile(
            "{}/{}.conf".format(self.getRedirectPath(_siteName), _id), file_content)

        self.operateRedirectConf(_siteName, 'start')
        slemp.restartWeb()
        return slemp.returnJson(True, "ok")

    def delRedirectApi(self):
        _siteName = request.form.get("siteName", '')
        _id = request.form.get("id", '')
        if _id == '' or _siteName == '':
            return slemp.returnJson(False, "Required fields cannot be empty!")

        try:
            data_path = self.getRedirectDataPath(_siteName)
            data_content = slemp.readFile(
                data_path) if os.path.exists(data_path) else ""
            data = json.loads(data_content) if data_content != "" else []
            for item in data:
                if item["id"] == _id:
                    data.remove(item)
                    break
            # write database
            slemp.writeFile(data_path, json.dumps(data))
            # data is empty ,should stop
            if len(data) == 0:
                self.operateRedirectConf(_siteName, 'stop')
            # remove conf file
            slemp.execShell(
                "rm -rf {}/{}.conf".format(self.getRedirectPath(_siteName), _id))
        except:
            return slemp.returnJson(False, "Failed to delete!")
        return slemp.returnJson(True, "Successfully deleted!")

    def operateProxyConf(self, siteName, method='start'):
        vhost_file = self.vhostPath + '/' + siteName + '.conf'
        content = slemp.readFile(vhost_file)

        proxy_cnf = '''#PROXY-START
    include %s/*.conf;
    #PROXY-END''' % (self.getProxyPath(siteName))

        proxy_cnf_source = '#PROXY-START'

        if content.find('#PROXY-END') != -1:
            if method == 'stop':
                rep = '#PROXY-START(\n|.){1,500}#PROXY-END'
                content = re.sub(rep, '#PROXY-START', content)
        else:
            if method == 'start':
                content = re.sub(proxy_cnf_source, proxy_cnf, content)

        slemp.writeFile(vhost_file, content)

    def getProxyConfApi(self):
        _siteName = request.form.get("siteName", '')
        _id = request.form.get("id", '')
        if _id == '' or _siteName == '':
            return slemp.returnJson(False, "Required fields cannot be empty!")

        conf_file = "{}/{}/{}.conf".format(self.proxyPath, _siteName, _id)
        if not os.path.exists(conf_file):
            conf_file = "{}/{}/{}.conf.txt".format(
                self.proxyPath, _siteName, _id)

        data = slemp.readFile(conf_file)
        if data == False:
            return slemp.returnJson(False, "Fetch failed!")
        return slemp.returnJson(True, "ok", {"result": data})

    def setProxyStatusApi(self):
        _siteName = request.form.get("siteName", '')
        _status = request.form.get("status", '')
        _id = request.form.get("id", '')
        if _status == '' or _siteName == '' or _id == '':
            return slemp.returnJson(False, "Required fields cannot be empty!")

        conf_file = "{}/{}/{}.conf".format(self.proxyPath, _siteName, _id)
        conf_txt = "{}/{}/{}.conf.txt".format(self.proxyPath, _siteName, _id)

        if _status == '1':
            slemp.execShell('mv ' + conf_txt + ' ' + conf_file)
        else:
            slemp.execShell('mv ' + conf_file + ' ' + conf_txt)

        slemp.restartWeb()
        return slemp.returnJson(True, "OK")

    def saveProxyConfApi(self):
        _siteName = request.form.get("siteName", '')
        _id = request.form.get("id", '')
        _config = request.form.get("config", "")
        if _id == '' or _siteName == '':
            return slemp.returnJson(False, "Required fields cannot be empty!")

        _old_config = slemp.readFile(
            "{}/{}/{}.conf".format(self.proxyPath, _siteName, _id))
        if _old_config == False:
            return slemp.returnJson(False, "Illegal operation")

        slemp.writeFile("{}/{}/{}.conf".format(self.proxyPath,
                                            _siteName, _id), _config)
        rule_test = slemp.checkWebConfig()
        if rule_test != True:
            slemp.writeFile("{}/{}/{}.conf".format(self.proxyPath,
                                                _siteName, _id), _old_config)
            return slemp.returnJson(False, "OpenResty configuration test failed, please try again: {}".format(rule_test))

        self.operateRedirectConf(_siteName, 'start')
        slemp.restartWeb()
        return slemp.returnJson(True, "ok")

    def getProxyListApi(self):
        _siteName = request.form.get('siteName', '')

        data_path = self.getProxyDataPath(_siteName)
        data_content = slemp.readFile(data_path)

        # not exists
        if data_content == False:
            slemp.execShell("mkdir {}/{}".format(self.proxyPath, _siteName))
            return slemp.returnJson(True, "", {"result": [], "count": 0})

        try:
            data = json.loads(data_content)
        except:
            slemp.execShell("rm -rf {}/{}".format(self.proxyPath, _siteName))
            return slemp.returnJson(True, "", {"result": [], "count": 0})

        tmp = []
        for proxy in data:
            proxy_dir = "{}/{}".format(self.proxyPath, _siteName)
            proxy_dir_file = proxy_dir + '/' + proxy['id'] + '.conf'
            if os.path.exists(proxy_dir_file):
                proxy['status'] = True
            else:
                proxy['status'] = False
            tmp.append(proxy)

        return slemp.returnJson(True, "ok", {"result": data, "count": len(data)})

    def setProxyApi(self):
        _siteName = request.form.get('siteName', '')
        _from = request.form.get('from', '')
        _to = request.form.get('to', '')
        _host = request.form.get('host', '')
        _name = request.form.get('name', '')
        _open_proxy = request.form.get('open_proxy', '')
        _open_cache = request.form.get('open_cache', '')
        _cache_time = request.form.get('cache_time', '')
        _id = request.form.get('id', '')

        if _name == "" or _siteName == "" or _from == "" or _to == "" or _host == "":
            return slemp.returnJson(False, "Required fields cannot be empty")

        rep = "http(s)?\:\/\/([a-zA-Z0-9][-a-zA-Z0-9]{0,62}\.)+([a-zA-Z0-9][a-zA-Z0-9]{0,62})+.?"
        if not re.match(rep, _to):
            return slemp.returnJson(False, "Wrong target address!")

        # _to = _to.strip("/")
        # get host from url
        try:
            if _host == "$host":
                host_tmp = urlparse(_to)
                _host = host_tmp.netloc
        except:
            return slemp.returnJson(False, "Wrong target address")

        # location ~* ^{from}(.*)$ {
        proxy_site_path = self.getProxyDataPath(_siteName)
        data_content = slemp.readFile(
            proxy_site_path) if os.path.exists(proxy_site_path) else ""
        data = json.loads(data_content) if data_content != "" else []

        tpl = "#PROXY-START\n\
location ^~ {from} {\n\
    proxy_pass {to};\n\
    proxy_set_header Host {host};\n\
    proxy_set_header X-Real-IP $remote_addr;\n\
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n\
    proxy_set_header REMOTE-HOST $remote_addr;\n\
    proxy_set_header Upgrade $http_upgrade;\n\
    proxy_set_header Connection $connection_upgrade;\n\
    proxy_http_version 1.1;\n\
    \n\
    add_header X-Cache $upstream_cache_status;\n\
     {proxy_cache}\n\
}\n\
# PROXY-END"

        tpl_proxy_cache = "\n\
    if ( $uri ~* \"\.(gif|png|jpg|css|js|woff|woff2)$\" )\n\
    {\n\
        expires {cache_time}m;\n\
    }\n\
    proxy_ignore_headers Set-Cookie Cache-Control expires;\n\
    proxy_cache slemp_cache;\n\
    proxy_cache_key \"$host$uri$is_args$args\";\n\
    proxy_cache_valid 200 304 301 302 {cache_time}m;\n\
"

        tpl_proxy_nocache = "\n\
    set $static_files_app 0; \n\
    if ( $uri ~* \"\.(gif|png|jpg|css|js|woff|woff2)$\" )\n\
    {\n\
        set $static_files_app 1;\n\
        expires 12h;\n\
    }\n\
    if ( $static_files_app = 0 )\n\
    {\n\
        add_header Cache-Control no-cache;\n\
    }\n\

        # replace
        if _from[0] != '/':
            _from = '/' + _from
        tpl = tpl.replace("{from}", _from, 999)
        tpl = tpl.replace("{to}", _to)
        tpl = tpl.replace("{host}", _host, 999)
        tpl = tpl.replace("{cache_time}", _cache_time, 999)

        if _open_cache == 'on':
            tpl_proxy_cache = tpl_proxy_cache.replace(
                "{cache_time}", _cache_time, 999)
            tpl = tpl.replace("{proxy_cache}", tpl_proxy_cache, 999)
        else:
            tpl = tpl.replace("{proxy_cache}", tpl_proxy_nocache, 999)

        proxy_action = 'add'
        if _id == "":
            _id = slemp.md5("{}".format(_name))
        else:
            proxy_action = 'edit'

        conf_proxy = "{}/{}.conf".format(self.getProxyPath(_siteName), _id)
        conf_bk = "{}/{}.conf.txt".format(self.getProxyPath(_siteName), _id)

        slemp.writeFile(conf_proxy, tpl)

        rule_test = slemp.checkWebConfig()
        if rule_test != True:
            os.remove(conf_proxy)
            return slemp.returnJson(False, "OpenResty configuration test failed, please try again: {}".format(rule_test))

        if proxy_action == "add":
            _id = slemp.md5("{}".format(_name))
            for item in data:
                if item["name"] == _name:
                    return slemp.returnJson(False, "Duplicate name!")
                if item["from"] == _from:
                    return slemp.returnJson(False, "Proxy directory already exists!")
            data.append({
                "name": _name,
                "from": _from,
                "to": _to,
                "host": _host,
                "open_cache": _open_cache,
                "open_proxy": _open_proxy,
                "cache_time": _cache_time,
                "id": _id,
            })
        else:
            dindex = -1
            for x in range(len(data)):
                if data[x]["id"] == _id:
                    dindex = x
                    break
            if dindex < 0:
                return slemp.returnJson(False, "Bad request")
            data[dindex]['from'] = _from
            data[dindex]['to'] = _to
            data[dindex]['host'] = _host
            data[dindex]['open_cache'] = _open_cache
            data[dindex]['open_proxy'] = _open_proxy
            data[dindex]['cache_time'] = _cache_time

        if _open_proxy != 'on':
            os.rename(conf_proxy, conf_bk)

        slemp.writeFile(proxy_site_path, json.dumps(data))

        self.operateProxyConf(_siteName, 'start')
        slemp.restartWeb()
        return slemp.returnJson(True, "ok", {"hash": _id})

    def delProxyApi(self):
        _siteName = request.form.get("siteName", '')
        _id = request.form.get("id", '')
        if _id == '' or _siteName == '':
            return slemp.returnJson(False, "Required fields cannot be empty!")

        try:
            data_path = self.getProxyDataPath(_siteName)
            data_content = slemp.readFile(
                data_path) if os.path.exists(data_path) else ""
            data = json.loads(data_content) if data_content != "" else []
            for item in data:
                if item["id"] == _id:
                    data.remove(item)
                    break
            # write database
            slemp.writeFile(data_path, json.dumps(data))

            # data is empty,should stop
            if len(data) == 0:
                self.operateProxyConf(_siteName, 'stop')
            # remove conf file
            cmd = "rm -rf {}/{}.conf*".format(
                self.getProxyPath(_siteName), _id)
            slemp.execShell(cmd)
        except:
            return slemp.returnJson(False, "Failed to delete!")

        slemp.restartWeb()
        return slemp.returnJson(True, "Successfully deleted!")

    def getSiteTypesApi(self):
        data = slemp.M("site_types").field("id,name").order("id asc").select()
        data.insert(0, {"id": 0, "name": "Default category"})
        return slemp.getJson(data)

    def getSiteDocApi(self):
        stype = request.form.get('type', '0').strip()
        vlist = []
        vlist.append('')
        vlist.append(slemp.getServerDir() +
                     '/openresty/nginx/html/index.html')
        vlist.append(slemp.getServerDir() + '/openresty/nginx/html/404.html')
        vlist.append(slemp.getServerDir() +
                     '/openresty/nginx/html/index.html')
        vlist.append(slemp.getServerDir() + '/web_conf/stop/index.html')
        data = {}
        data['path'] = vlist[int(stype)]
        return slemp.returnJson(True, 'ok', data)

    def addSiteTypeApi(self):
        name = request.form.get('name', '').strip()
        if not name:
            return slemp.returnJson(False, "Category name cannot be empty")
        if len(name) > 18:
            return slemp.returnJson(False, "The length of the category name cannot exceed 6 Chinese characters or 18 letters")
        if slemp.M('site_types').count() >= 10:
            return slemp.returnJson(False, 'Add up to 10 categories!')
        if slemp.M('site_types').where('name=?', (name,)).count() > 0:
            return slemp.returnJson(False, "The specified category name already exists!")
        slemp.M('site_types').add("name", (name,))
        return slemp.returnJson(True, 'Added successfully!')

    def removeSiteTypeApi(self):
        mid = request.form.get('id', '')
        if slemp.M('site_types').where('id=?', (mid,)).count() == 0:
            return slemp.returnJson(False, "The specified category does not exist!")
        slemp.M('site_types').where('id=?', (mid,)).delete()
        slemp.M("sites").where("type_id=?", (mid,)).save("type_id", (0,))
        return slemp.returnJson(True, "Category deleted!")

    def modifySiteTypeNameApi(self):
        name = request.form.get('name', '').strip()
        mid = request.form.get('id', '')
        if not name:
            return slemp.returnJson(False, "Category name cannot be empty")
        if len(name) > 18:
            return slemp.returnJson(False, "The length of the category name cannot exceed 6 Chinese characters or 18 letters")
        if slemp.M('site_types').where('id=?', (mid,)).count() == 0:
            return slemp.returnJson(False, "The specified category does not exist!")
        slemp.M('site_types').where('id=?', (mid,)).setField('name', name)
        return slemp.returnJson(True, "Successfully modified!")

    def setSiteTypeApi(self):
        site_ids = request.form.get('site_ids', '')
        mid = request.form.get('id', '')
        site_ids = json.loads(site_ids)
        for sid in site_ids:
            print(slemp.M('sites').where('id=?', (sid,)).setField('type_id', mid))
        return slemp.returnJson(True, "Successfully set!")

    ##### ----- end   ----- ###

    def toPunycode(self, domain):
        import re
        if sys.version_info[0] == 2:
            domain = domain.encode('utf8')
        tmp = domain.split('.')
        newdomain = ''
        for dkey in tmp:
            match = re.search(u"[\x80-\xff]+", dkey)
            if not match:
                newdomain += dkey + '.'
            else:
                newdomain += 'xn--' + \
                    dkey.decode('utf-8').encode('punycode') + '.'
        return newdomain[0:-1]

    def toPunycodePath(self, path):
        if sys.version_info[0] == 2:
            path = path.encode('utf-8')
        if os.path.exists(path):
            return path
        import re
        match = re.search(u"[\x80-\xff]+", path)
        if not match:
            return path
        npath = ''
        for ph in path.split('/'):
            npath += '/' + self.toPunycode(ph)
        return npath.replace('//', '/')

    def getPath(self, path):
        if path[-1] == '/':
            return path[0:-1]
        return path

    def getSitePath(self, siteName):
        file = self.getHostConf(siteName)
        if os.path.exists(file):
            conf = slemp.readFile(file)
            rep = '\s*root\s*(.+);'
            path = re.search(rep, conf).groups()[0]
            return path
        return ''

    def getSiteRunPath(self, mid):
        siteName = slemp.M('sites').where('id=?', (mid,)).getField('name')
        sitePath = slemp.M('sites').where('id=?', (mid,)).getField('path')
        path = sitePath

        filename = self.getHostConf(siteName)
        if os.path.exists(filename):
            conf = slemp.readFile(filename)
            rep = '\s*root\s*(.+);'
            path = re.search(rep, conf).groups()[0]

        data = {}
        if sitePath == path:
            data['runPath'] = '/'
        else:
            data['runPath'] = path.replace(sitePath, '')

        dirnames = []
        dirnames.append('/')
        for filename in os.listdir(sitePath):
            try:
                filePath = sitePath + '/' + filename
                if os.path.islink(filePath):
                    continue
                if os.path.isdir(filePath):
                    dirnames.append('/' + filename)
            except:
                pass

        data['dirs'] = dirnames
        return data

    def getHostConf(self, siteName):
        return self.vhostPath + '/' + siteName + '.conf'

    def getRewriteConf(self, siteName):
        return self.rewritePath + '/' + siteName + '.conf'

    def getRedirectDataPath(self, siteName):
        return "{}/{}/data.json".format(self.redirectPath, siteName)

    def getRedirectPath(self, siteName):
        return "{}/{}".format(self.redirectPath, siteName)

    def getProxyDataPath(self, siteName):
        return "{}/{}/data.json".format(self.proxyPath, siteName)

    def getProxyPath(self, siteName):
        return "{}/{}".format(self.proxyPath, siteName)

    def getDirBindRewrite(self, siteName, dirname):
        return self.rewritePath + '/' + siteName + '_' + dirname + '.conf'

    def getIndexConf(self):
        return slemp.getServerDir() + '/openresty/nginx/conf/nginx.conf'

    def getDomain(self, pid):
        _list = slemp.M('domain').where("pid=?", (pid,)).field(
            'id,pid,name,port,addtime').select()
        return slemp.getJson(_list)

    def getLogs(self, siteName):
        logPath = slemp.getLogsDir() + '/' + siteName + '.log'
        if not os.path.exists(logPath):
            return slemp.returnJson(False, 'Log is empty')
        return slemp.returnJson(True, slemp.getLastLine(logPath, 100))

    def getErrorLogs(self, siteName):
        logPath = slemp.getLogsDir() + '/' + siteName + '.error.log'
        if not os.path.exists(logPath):
            return slemp.returnJson(False, 'Log is empty')
        return slemp.returnJson(True, slemp.getLastLine(logPath, 100))

    def getLogsStatus(self, siteName):
        filename = self.getHostConf(siteName)
        conf = slemp.readFile(filename)
        if conf.find('#ErrorLog') != -1:
            return False
        if conf.find("access_log  off") != -1:
            return False
        return True

    def getHasPwd(self, siteName):
        filename = self.getHostConf(siteName)
        conf = slemp.readFile(filename)
        if conf.find('#AUTH_START') != -1:
            return True
        return False

    def getSitePhpVersion(self, siteName):
        conf = slemp.readFile(self.getHostConf(siteName))
        rep = "enable-php-(.*)\.conf"
        tmp = re.search(rep, conf).groups()
        data = {}
        data['phpversion'] = tmp[0]
        return slemp.getJson(data)

    def getIndex(self, sid):
        siteName = slemp.M('sites').where("id=?", (sid,)).getField('name')
        file = self.getHostConf(siteName)
        conf = slemp.readFile(file)
        rep = "\s+index\s+(.+);"
        tmp = re.search(rep, conf).groups()
        return tmp[0].replace(' ', ',')

    def setIndex(self, sid, index):
        if index.find('.') == -1:
            return slemp.returnJson(False,  'The default document format is incorrect, e.g.：index.html')

        index = index.replace(' ', '')
        index = index.replace(',,', ',')

        if len(index) < 3:
            return slemp.returnJson(False,  'Default document cannot be empty!')

        siteName = slemp.M('sites').where("id=?", (sid,)).getField('name')
        index_l = index.replace(",", " ")
        file = self.getHostConf(siteName)
        conf = slemp.readFile(file)
        if conf:
            rep = "\s+index\s+.+;"
            conf = re.sub(rep, "\n\tindex " + index_l + ";", conf)
            slemp.writeFile(file, conf)

        slemp.writeLog('TYPE_SITE', 'SITE_INDEX_SUCCESS', (siteName, index_l))
        return slemp.returnJson(True,  'Successfully set!')

    def getLimitNet(self, sid):
        siteName = slemp.M('sites').where("id=?", (sid,)).getField('name')
        filename = self.getHostConf(siteName)
        data = {}
        conf = slemp.readFile(filename)
        try:
            rep = "\s+limit_conn\s+perserver\s+([0-9]+);"
            tmp = re.search(rep, conf).groups()
            data['perserver'] = int(tmp[0])

            rep = "\s+limit_conn\s+perip\s+([0-9]+);"
            tmp = re.search(rep, conf).groups()
            data['perip'] = int(tmp[0])

            rep = "\s+limit_rate\s+([0-9]+)\w+;"
            tmp = re.search(rep, conf).groups()
            data['limit_rate'] = int(tmp[0])
        except:
            data['perserver'] = 0
            data['perip'] = 0
            data['limit_rate'] = 0

        return slemp.getJson(data)

    def checkIndexConf(self):
        limit = self.getIndexConf()
        nginxConf = slemp.readFile(limit)
        limitConf = "limit_conn_zone $binary_remote_addr zone=perip:10m;\n\t\tlimit_conn_zone $server_name zone=perserver:10m;"
        nginxConf = nginxConf.replace(
            "#limit_conn_zone $binary_remote_addr zone=perip:10m;", limitConf)
        slemp.writeFile(limit, nginxConf)

    def saveLimitNet(self, sid, perserver, perip, limit_rate):

        str_perserver = 'limit_conn perserver ' + perserver + ';'
        str_perip = 'limit_conn perip ' + perip + ';'
        str_limit_rate = 'limit_rate ' + limit_rate + 'k;'

        siteName = slemp.M('sites').where("id=?", (sid,)).getField('name')
        filename = self.getHostConf(siteName)

        conf = slemp.readFile(filename)
        if(conf.find('limit_conn perserver') != -1):
            rep = "limit_conn\s+perserver\s+([0-9]+);"
            conf = re.sub(rep, str_perserver, conf)

            rep = "limit_conn\s+perip\s+([0-9]+);"
            conf = re.sub(rep, str_perip, conf)

            rep = "limit_rate\s+([0-9]+)\w+;"
            conf = re.sub(rep, str_limit_rate, conf)
        else:
            conf = conf.replace('#error_page 404/404.html;', "#error_page 404/404.html;\n    " +
                                str_perserver + "\n    " + str_perip + "\n    " + str_limit_rate)

        slemp.writeFile(filename, conf)
        slemp.restartWeb()
        slemp.writeLog('TYPE_SITE', 'SITE_NETLIMIT_OPEN_SUCCESS', (siteName,))
        return slemp.returnJson(True, 'Successfully set!')

    def closeLimitNet(self, sid):
        siteName = slemp.M('sites').where("id=?", (sid,)).getField('name')
        filename = self.getHostConf(siteName)
        conf = slemp.readFile(filename)
        rep = "\s+limit_conn\s+perserver\s+([0-9]+);"
        conf = re.sub(rep, '', conf)

        rep = "\s+limit_conn\s+perip\s+([0-9]+);"
        conf = re.sub(rep, '', conf)

        rep = "\s+limit_rate\s+([0-9]+)\w+;"
        conf = re.sub(rep, '', conf)
        slemp.writeFile(filename, conf)
        slemp.restartWeb()
        slemp.writeLog(
            'TYPE_SITE', 'SITE_NETLIMIT_CLOSE_SUCCESS', (siteName,))
        return slemp.returnJson(True, 'Data limit turned off!')

    def getSecurity(self, sid, name):
        filename = self.getHostConf(name)
        conf = slemp.readFile(filename)
        data = {}
        if conf.find('SECURITY-START') != -1:
            rep = "#SECURITY-START(\n|.){1,500}#SECURITY-END"
            tmp = re.search(rep, conf).group()
            data['fix'] = re.search(
                "\(.+\)\$", tmp).group().replace('(', '').replace(')$', '').replace('|', ',')
            data['domains'] = ','.join(re.search(
                "valid_referers\s+none\s+blocked\s+(.+);\n", tmp).groups()[0].split())
            data['status'] = True
        else:
            data['fix'] = 'jpg,jpeg,gif,png,js,css'
            domains = slemp.M('domain').where(
                'pid=?', (sid,)).field('name').select()
            tmp = []
            for domain in domains:
                tmp.append(domain['name'])
            data['domains'] = ','.join(tmp)
            data['status'] = False
        return slemp.getJson(data)

    def setSecurity(self, sid, name, fix, domains, status):
        if len(fix) < 2:
            return slemp.returnJson(False, 'URL suffix cannot be empty!')
        file = self.getHostConf(name)
        if os.path.exists(file):
            conf = slemp.readFile(file)
            if conf.find('SECURITY-START') != -1:
                rep = "\s{0,4}#SECURITY-START(\n|.){1,500}#SECURITY-END\n?"
                conf = re.sub(rep, '', conf)
                slemp.writeLog('Website management', 'Site [' + name + '] has disabled anti-leech settings!')
            else:
                pre_path = self.setupPath + "/php/conf"
                re_path = "include\s+" + pre_path + "/enable-php-"
                rconf = '''#SECURITY-START Anti-leech configuration
    location ~ .*\.(%s)$
    {
        expires      30d;
        access_log /dev/null;
        valid_referers none blocked %s;
        if ($invalid_referer){
           return 404;
        }
    }
    #SECURITY-END
    include %s/enable-php-''' % (fix.strip().replace(',', '|'), domains.strip().replace(',', ' '), pre_path)
                conf = re.sub(re_path, rconf, conf)
                slemp.writeLog('Website management', 'Site [' + name + '] has enabled anti-leech!')
            slemp.writeFile(file, conf)
        slemp.restartWeb()
        return slemp.returnJson(True, 'Successfully set!')

    def getPhpVersion(self):
        phpVersions = ('00', '52', '53', '54', '55',
                       '56', '70', '71', '72', '73', '74', '80', '81', '82')
        data = []
        for val in phpVersions:
            tmp = {}
            if val == '00':
                tmp['version'] = '00'
                tmp['name'] = 'Pure static'
                data.append(tmp)

            checkPath = slemp.getServerDir() + '/php/' + val + '/bin/php'
            if os.path.exists(checkPath):
                tmp['version'] = val
                tmp['name'] = 'PHP-' + val
                data.append(tmp)

        conf_dir = slemp.getServerDir() + "/web_conf/php/conf"
        conf_list = os.listdir(conf_dir)
        l = len(conf_list)
        rep = "enable-php-(.*?)\.conf"
        for name in conf_list:
            tmp = {}
            try:
                matchVer = re.search(rep, name).groups()[0]
            except Exception as e:
                continue

            if matchVer in phpVersions:
                continue

            tmp['version'] = matchVer
            tmp['name'] = 'PHP-' + matchVer
            data.append(tmp)

        return data

    def isToHttps(self, siteName):
        file = self.getHostConf(siteName)
        conf = slemp.readFile(file)
        if conf:
            # if conf.find('HTTP_TO_HTTPS_START') != -1:
            #     return True
            if conf.find('$server_port !~ 443') != -1:
                return True
        return False

    def getRewriteList(self):
        rewriteList = {}
        rewriteList['rewrite'] = []
        rewriteList['rewrite'].append('0.Current')
        for ds in os.listdir('rewrite/nginx'):
            rewriteList['rewrite'].append(ds[0:len(ds) - 5])
        rewriteList['rewrite'] = sorted(rewriteList['rewrite'])
        return rewriteList

    def createRootDir(self, path):
        autoInit = False
        if not os.path.exists(path):
            autoInit = True
            os.makedirs(path)
        if not slemp.isAppleSystem():
            slemp.execShell('chown -R www:www ' + path)

        if autoInit:
            slemp.writeFile(path + '/index.html', 'Work has started!!!')
            slemp.execShell('chmod -R 755 ' + path)

    def nginxAddDomain(self, webname, domain, port):
        file = self.getHostConf(webname)
        conf = slemp.readFile(file)
        if not conf:
            return

        rep = "server_name\s*(.*);"
        tmp = re.search(rep, conf).group()
        domains = tmp.split(' ')
        if not slemp.inArray(domains, domain):
            newServerName = tmp.replace(';', ' ' + domain + ';')
            conf = conf.replace(tmp, newServerName)

        rep = "listen\s+([0-9]+)\s*[default_server]*\s*;"
        tmp = re.findall(rep, conf)
        if not slemp.inArray(tmp, port):
            listen = re.search(rep, conf).group()
            conf = conf.replace(
                listen, listen + "\n\tlisten " + port + ';')
        slemp.writeFile(file, conf)
        return True

    def nginxAddConf(self):
        source_tpl = slemp.getRunDir() + '/data/tpl/nginx.conf'
        vhost_file = self.vhostPath + '/' + self.siteName + '.conf'
        content = slemp.readFile(source_tpl)

        content = content.replace('{$PORT}', self.sitePort)
        content = content.replace('{$SERVER_NAME}', self.siteName)
        content = content.replace('{$ROOT_DIR}', self.sitePath)
        content = content.replace('{$PHP_DIR}', self.setupPath + '/php')
        content = content.replace('{$PHPVER}', self.phpVersion)
        content = content.replace('{$OR_REWRITE}', self.rewritePath)
        # content = content.replace('{$OR_REDIRECT}', self.redirectPath)
        # content = content.replace('{$OR_PROXY}', self.proxyPath)

        logsPath = slemp.getLogsDir()
        content = content.replace('{$LOGPATH}', logsPath)
        slemp.writeFile(vhost_file, content)

#         rewrite_content = '''
# location /{
#     if ($PHP_ENV != "1"){
#         break;
#     }

#     if (!-e $request_filename) {
#        rewrite  ^(.*)$  /index.php/$1  last;
#        break;
#     }
# }
# '''
        rewrite_file = self.rewritePath + '/' + self.siteName + '.conf'
        slemp.writeFile(rewrite_file, '')

    def add(self, webname, port, ps, path, version):
        siteMenu = json.loads(webname)
        self.siteName = self.toPunycode(
            siteMenu['domain'].strip().split(':')[0]).strip()
        self.sitePath = self.toPunycodePath(
            self.getPath(path.replace(' ', '')))
        self.sitePort = port.strip().replace(' ', '')
        self.phpVersion = version

        if slemp.M('sites').where("name=?", (self.siteName,)).count():
            return slemp.returnJson(False, 'The site you added already exists!')

        pid = slemp.M('sites').add('name,path,status,ps,edate,addtime,type_id',
                                (self.siteName, self.sitePath, '1', ps, '0000-00-00', slemp.getDate(), 0,))
        opid = slemp.M('domain').where("name=?", (self.siteName,)).getField('pid')
        if opid:
            if slemp.M('sites').where('id=?', (opid,)).count():
                return slemp.returnJson(False, 'The domain you added already exists!')
            slemp.M('domain').where('pid=?', (opid,)).delete()

        self.createRootDir(self.sitePath)
        self.nginxAddConf()

        slemp.M('domain').add('pid,name,port,addtime',
                           (pid, self.siteName, self.sitePort, slemp.getDate()))

        for domain in siteMenu['domainlist']:
            self.addDomain(domain, self.siteName, pid)

        data = {}
        data['siteStatus'] = False
        slemp.restartWeb()
        self.runHook('site_cb', 'add')
        return slemp.returnJson(True, 'Added successfully')

    def deleteWSLogs(self, webname):
        assLogPath = slemp.getLogsDir() + '/' + webname + '.log'
        errLogPath = slemp.getLogsDir() + '/' + webname + '.error.log'
        confFile = self.setupPath + '/nginx/vhost/' + webname + '.conf'
        rewriteFile = self.setupPath + '/nginx/rewrite/' + webname + '.conf'
        passFile = self.setupPath + '/nginx/pass/' + webname + '.conf'
        keyPath = self.sslDir + webname + '/privkey.pem'
        certPath = self.sslDir + webname + '/fullchain.pem'
        logs = [assLogPath,
                errLogPath,
                confFile,
                rewriteFile,
                passFile,
                keyPath,
                certPath]
        for i in logs:
            slemp.deleteFile(i)

        redirectDir = self.setupPath + '/nginx/redirect/' + webname
        if os.path.exists(redirectDir):
            slemp.execShell('rm -rf ' + redirectDir)
        proxyDir = self.setupPath + '/nginx/proxy/' + webname
        if os.path.exists(proxyDir):
            slemp.execShell('rm -rf ' + proxyDir)

    def delete(self, sid, webname, path):
        self.deleteWSLogs(webname)
        if path == '1':
            rootPath = slemp.getWwwDir() + '/' + webname
            slemp.execShell('rm -rf ' + rootPath)

        # ssl
        ssl_dir = self.sslDir + '/' + webname
        if os.path.exists(ssl_dir):
            slemp.execShell('rm -rf ' + ssl_dir)

        ssl_lets_dir = self.sslLetsDir + '/' + webname
        if os.path.exists(ssl_lets_dir):
            slemp.execShell('rm -rf ' + ssl_lets_dir)

        ssl_acme_dir = slemp.getAcmeDir() + '/' + webname
        if os.path.exists(ssl_acme_dir):
            slemp.execShell('rm -rf ' + ssl_acme_dir)

        slemp.M('sites').where("id=?", (sid,)).delete()
        slemp.M('domain').where("pid=?", (sid,)).delete()
        slemp.M('domain').where("name=?", (webname,)).delete()

        # binding domain delete
        binding_list = slemp.M('binding').field(
            'id,domain').where("pid=?", (sid,)).select()

        for x in binding_list:
            wlog = slemp.getLogsDir() + "/" + webname + "_" + x['domain'] + ".log"
            wlog_error = slemp.getLogsDir() + "/" + webname + "_" + \
                x['domain'] + ".error.log"

            if os.path.exists(wlog):
                slemp.execShell('rm -rf ' + wlog)
            if os.path.exists(wlog_error):
                slemp.execShell('rm -rf ' + wlog_error)

        slemp.M('binding').where("pid=?", (sid,)).delete()
        slemp.restartWeb()
        self.runHook('site_cb', 'delete')
        return slemp.returnJson(True, 'Site deleted successfully!')

    def setEndDate(self, sid, edate):
        result = slemp.M('sites').where(
            'id=?', (sid,)).setField('edate', edate)
        siteName = slemp.M('sites').where('id=?', (sid,)).getField('name')
        slemp.writeLog('TYPE_SITE', 'The setting is successful, and the site will automatically stop when it expires!', (siteName, edate))
        return slemp.returnJson(True, 'The setting is successful, and the site will automatically stop when it expires!')

    def setSslConf(self, siteName):
        file = self.getHostConf(siteName)
        conf = slemp.readFile(file)

        keyPath = self.sslDir + '/' + siteName + '/privkey.pem'
        certPath = self.sslDir + '/' + siteName + '/fullchain.pem'
        if conf:
            if conf.find('ssl_certificate') == -1:
                sslStr = """#error_page 404/404.html;
    ssl_certificate    %s;
    ssl_certificate_key  %s;
    ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:HIGH:!aNULL:!MD5:!RC4:!DHE;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    error_page 497  https://$host$request_uri;""" % (certPath, keyPath)
            if(conf.find('ssl_certificate') != -1):
                return slemp.returnData(True, 'SSL opened successfully!')

            conf = conf.replace('#error_page 404/404.html;', sslStr)

            rep = "listen\s+([0-9]+)\s*[default_server]*;"
            tmp = re.findall(rep, conf)
            if not slemp.inArray(tmp, '443'):
                listen = re.search(rep, conf).group()
                http_ssl = "\n\tlisten 443 ssl http2;"
                http_ssl = http_ssl + "\n\tlisten [::]:443 ssl http2;"
                conf = conf.replace(listen, listen + http_ssl)

            slemp.backFile(file)
            slemp.writeFile(file, conf)
            isError = slemp.checkWebConfig()
            if(isError != True):
                slemp.restoreFile(file)
                return slemp.returnData(False, 'Certificate error: <br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')

        self.saveCert(keyPath, certPath)

        msg = slemp.getInfo('Website [{}] successfully enabled SSL!', siteName)
        slemp.writeLog('Website management', msg)

        slemp.restartWeb()
        return slemp.returnData(True, 'SSL opened successfully!')

    def saveCert(self, keyPath, certPath):
        try:
            certInfo = slemp.getCertName(certPath)
            if not certInfo:
                return slemp.returnData(False, 'Certificate parsing failed!')
            vpath = self.sslDir + '/' + certInfo['subject'].strip()
            if not os.path.exists(vpath):
                os.system('mkdir -p ' + vpath)
            slemp.writeFile(vpath + '/privkey.pem', slemp.readFile(keyPath))
            slemp.writeFile(vpath + '/fullchain.pem', slemp.readFile(certPath))
            slemp.writeFile(vpath + '/info.json', json.dumps(certInfo))
            return slemp.returnData(True, 'Certificate saved successfully!')
        except Exception as e:
            return slemp.returnData(False, 'Certificate save failed!')

    def delUserInI(self, path, up=0):
        for p1 in os.listdir(path):
            try:
                npath = path + '/' + p1
                if os.path.isdir(npath):
                    if up < 100:
                        self.delUserInI(npath, up + 1)
                else:
                    continue
                useriniPath = npath + '/.user.ini'
                if not os.path.exists(useriniPath):
                    continue
                slemp.execShell('which chattr && chattr -i ' + useriniPath)
                slemp.execShell('rm -f ' + useriniPath)
            except:
                continue
        return True

    def setDirUserINI(self, sitePath, runPath):
        newPath = sitePath + runPath

        filename = newPath + '/.user.ini'
        if os.path.exists(filename):
            slemp.execShell("chattr -i " + filename)
            os.remove(filename)
            return slemp.returnJson(True, 'Anti-cross-site setting has been cleared!')

        self.delUserInI(newPath)
        openPath = 'open_basedir={}/:{}/'.format(newPath, sitePath)
        if runPath == '/':
            openPath = 'open_basedir={}/'.format(sitePath)

        slemp.writeFile(filename, openPath + ':/home/slemp/server/php:/tmp/:/proc/')
        slemp.execShell("chattr +i " + filename)

        return slemp.returnJson(True, 'The anti-cross-site setting is turned on!')
