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

    def __init__(self):
        self.setupPath = slemp.getServerDir() + '/web_conf'
        self.vhostPath = vh = self.setupPath + '/nginx/vhost'
        if not os.path.exists(vh):
            slemp.execShell("mkdir -p " + vh + " && chmod -R 755 " + vh)
        self.rewritePath = rw = self.setupPath + '/nginx/rewrite'
        if not os.path.exists(rw):
            slemp.execShell("mkdir -p " + rw + " && chmod -R 755 " + rw)
        self.passPath = self.setupPath + '/nginx/pass'

        self.redirectPath = self.setupPath + '/nginx/redirect'
        if not os.path.exists(self.redirectPath):
            slemp.execShell("mkdir -p " + self.redirectPath +
                         " && chmod -R 755 " + self.redirectPath)

        self.proxyPath = self.setupPath + '/nginx/proxy'
        if not os.path.exists(self.proxyPath):
            slemp.execShell("mkdir -p " + self.proxyPath +
                         " && chmod -R 755 " + self.proxyPath)

        self.logsPath = slemp.getRootDir() + '/wwwlogs'
        if slemp.isAppleSystem():
            self.sslDir = self.setupPath + '/letsencrypt/'
        else:
            self.sslDir = '/etc/letsencrypt/live/'

    def listApi(self):
        limit = request.form.get('limit', '10')
        p = request.form.get('p', '1')
        type_id = request.form.get('type_id', '')

        start = (int(p) - 1) * (int(limit))

        siteM = slemp.M('sites')
        if type_id != '' and type_id == '-1' and type_id == '0':
            siteM.where('type_id=?', (type_id))

        _list = siteM.field('id,name,path,status,ps,addtime,edate').limit(
            (str(start)) + ',' + limit).order('id desc').select()

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
        return slemp.returnJson(True, 'Pengaturan berhasil!')

    def getDefaultSiteApi(self):
        data = {}
        data['sites'] = slemp.M('sites').field(
            'name').order('id desc').select()
        data['default_site'] = slemp.readFile('data/default_site.pl')
        return slemp.getJson(data)

    def setPsApi(self):
        mid = request.form.get('id', '')
        ps = request.form.get('ps', '')
        if slemp.M('sites').where("id=?", (mid,)).setField('ps', ps):
            return slemp.returnJson(True, 'Berhasil diubah!')
        return slemp.returnJson(False, 'Gagal mengedit!')

    def stopApi(self):
        mid = request.form.get('id', '')
        name = request.form.get('name', '')

        return self.stop(mid, name)

    def stop(self, mid, name):
        path = self.setupPath + '/stop'
        if not os.path.exists(path):
            os.makedirs(path)
            slemp.writeFile(path + '/index.html',
                         'The website has been closed!!!')

        binding = slemp.M('binding').where('pid=?', (mid,)).field(
            'id,pid,domain,path,port,addtime').select()
        for b in binding:
            bpath = path + '/' + b['path']
            if not os.path.exists(bpath):
                slemp.execShell('mkdir -p ' + bpath)
                slemp.execShell('ln -sf ' + path +
                             '/index.html ' + bpath + '/index.html')

        sitePath = slemp.M('sites').where("id=?", (mid,)).getField('path')

        # nginx
        file = self.getHostConf(name)
        conf = slemp.readFile(file)
        if conf:
            conf = conf.replace(sitePath, path)
            slemp.writeFile(file, conf)

        slemp.M('sites').where("id=?", (mid,)).setField('status', '0')
        slemp.restartWeb()
        msg = slemp.getInfo('Situs [{1}] telah dinonaktifkan!', (name,))
        slemp.writeLog('Manajemen situs web', msg)
        return slemp.returnJson(True, 'Situs dinonaktifkan!')

    def startApi(self):
        mid = request.form.get('id', '')
        name = request.form.get('name', '')
        path = self.setupPath + '/stop'
        sitePath = slemp.M('sites').where("id=?", (mid,)).getField('path')

        # nginx
        file = self.getHostConf(name)
        conf = slemp.readFile(file)
        if conf:
            conf = conf.replace(path, sitePath)
            slemp.writeFile(file, conf)

        slemp.M('sites').where("id=?", (mid,)).setField('status', '1')
        slemp.restartWeb()
        msg = slemp.getInfo('Situs [{1}] telah diaktifkan!', (name,))
        slemp.writeLog('Manajemen situs web', msg)
        return slemp.returnJson(True, 'Situs diaktifkan!')

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

        msg = slemp.getInfo('Situs [{1}] berhasil dicadangkan!', (find['name'],))
        slemp.writeLog('Manajemen situs web', msg)
        return slemp.returnJson(True, 'Pencadangan berhasil!')

    def delBackupApi(self):
        mid = request.form.get('id', '')
        filename = slemp.M('backup').where(
            "id=?", (mid,)).getField('filename')
        if os.path.exists(filename):
            os.remove(filename)
        name = slemp.M('backup').where("id=?", (mid,)).getField('name')
        msg = slemp.getInfo('Menghapus cadangan [{2}] situs web [{1}] berhasil!', (name, filename))
        slemp.writeLog('Manajemen situs web', msg)
        slemp.M('backup').where("id=?", (mid,)).delete()
        return slemp.returnJson(True, 'Situs berhasil dihapus!')

    def getPhpVersionApi(self):
        return self.getPhpVersion()

    def setPhpVersionApi(self):
        siteName = request.form.get('siteName', '')
        version = request.form.get('version', '')

        # nginx
        file = self.getHostConf(siteName)
        conf = slemp.readFile(file)
        if conf:
            rep = "enable-php-(.*)\.conf"
            tmp = re.search(rep, conf).group()
            conf = conf.replace(tmp, 'enable-php-' + version + '.conf')
            slemp.writeFile(file, conf)

        msg = slemp.getInfo('Versi PHP situs web [{1}] berhasil dialihkan ke PHP-{2}', (siteName, version))
        slemp.writeLog("Manajemen situs web", msg)
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
                'Manajemen situs web', 'Situs [' + siteName + '], direktori root [' + path + '] tidak ada, dibuat ulang!')

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
        data['userini'] = False
        if os.path.exists(path + '/.user.ini'):
            data['userini'] = True
        data['runPath'] = self.getSiteRunPath(mid)
        data['pass'] = self.getHasPwd(name)
        data['path'] = path
        data['name'] = name
        return slemp.returnJson(True, 'OK', data)

    def setDirUserIniApi(self):
        path = request.form.get('path', '')
        filename = path + '/.user.ini'
        self.delUserInI(path)
        if os.path.exists(filename):
            slemp.execShell("which chattr && chattr -i " + filename)
            os.remove(filename)
            return slemp.returnJson(True, 'Pengaturan anti-cross-site dihapus!')
        slemp.writeFile(filename, 'open_basedir=' + path +
                     '/:/home/slemp/server/php:/tmp/:/proc/')
        slemp.execShell("which chattr && chattr +i " + filename)
        return slemp.returnJson(True, 'Pengaturan anti-cross-site diaktifkan!')

    def logsOpenApi(self):
        mid = request.form.get('id', '')
        name = slemp.M('sites').where("id=?", (mid,)).getField('name')

        # NGINX
        filename = self.getHostConf(name)
        if os.path.exists(filename):
            conf = slemp.readFile(filename)
            rep = self.logsPath + "/" + name + ".log"
            if conf.find(rep) != -1:
                conf = conf.replace(rep, "off")
            else:
                conf = conf.replace('access_log  off', 'access_log  ' + rep)
            slemp.writeFile(filename, conf)

        slemp.restartWeb()
        return slemp.returnJson(True, 'Sukses!')

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

    def getSslApi(self):
        siteName = request.form.get('siteName', '')

        path = self.sslDir + siteName
        csrpath = path + "/fullchain.pem"
        keypath = path + "/privkey.pem"
        key = slemp.readFile(keypath)
        csr = slemp.readFile(csrpath)

        file = self.getHostConf(siteName)
        conf = slemp.readFile(file)

        keyText = 'ssl_certificate'
        status = True
        stype = 0
        if(conf.find(keyText) == -1):
            status = False
            stype = -1

        toHttps = self.isToHttps(siteName)
        id = slemp.M('sites').where("name=?", (siteName,)).getField('id')
        domains = slemp.M('domain').where(
            "pid=?", (id,)).field('name').select()
        data = {'status': status, 'domain': domains, 'key': key,
                'csr': csr, 'type': stype, 'httpTohttps': toHttps}
        return slemp.returnJson(True, 'OK', data)

    def setSslApi(self):
        siteName = request.form.get('siteName', '')
        key = request.form.get('key', '')
        csr = request.form.get('csr', '')

        path = self.sslDir + siteName
        if not os.path.exists(path):
            slemp.execShell('mkdir -p ' + path)

        csrpath = path + "/fullchain.pem"
        keypath = path + "/privkey.pem"

        if(key.find('KEY') == -1):
            return slemp.returnJson(False, 'Key salah, silakan periksa!')
        if(csr.find('CERTIFICATE') == -1):
            return slemp.returnJson(False, 'Certificate salah, harap periksa!')

        slemp.writeFile('/tmp/cert.pl', csr)
        if not slemp.checkCert('/tmp/cert.pl'):
            return slemp.returnJson(False, 'Certificate salah, harap tempel sertifikat format PEM yang benar!')

        slemp.execShell('\\cp -a ' + keypath + ' /tmp/backup1.conf')
        slemp.execShell('\\cp -a ' + csrpath + ' /tmp/backup2.conf')

        if os.path.exists(path + '/README'):
            slemp.execShell('rm -rf ' + path)
            slemp.execShell('rm -rf ' + path + '-00*')
            slemp.execShell('rm -rf /etc/letsencrypt/archive/' + siteName)
            slemp.execShell(
                'rm -rf /etc/letsencrypt/archive/' + siteName + '-00*')
            slemp.execShell(
                'rm -f /etc/letsencrypt/renewal/' + siteName + '.conf')
            slemp.execShell('rm -rf /etc/letsencrypt/renewal/' +
                         siteName + '-00*.conf')
            slemp.execShell('rm -rf ' + path + '/README')
            slemp.execShell('mkdir -p ' + path)

        slemp.writeFile(keypath, key)
        slemp.writeFile(csrpath, csr)

        result = self.setSslConf(siteName)
        # print result['msg']
        if not result['status']:
            return slemp.getJson(result)

        isError = slemp.checkWebConfig()
        if(type(isError) == str):
            slemp.execShell('\\cp -a /tmp/backup1.conf ' + keypath)
            slemp.execShell('\\cp -a /tmp/backup2.conf ' + csrpath)
            return slemp.returnJson(False, 'ERROR: <br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')

        slemp.writeLog('Manajemen situs web', 'Sertifikat disimpan!')
        slemp.restartWeb()
        return slemp.returnJson(True, 'Sertifikat disimpan!')

    def setCertToSiteApi(self):
        certName = request.form.get('certName', '')
        siteName = request.form.get('siteName', '')
        try:
            path = self.sslDir + siteName
            if not os.path.exists(path):
                return slemp.returnJson(False, 'Sertifikat tidak ada!')

            result = self.setSslConf(siteName)
            if not result['status']:
                return slemp.getJson(result)

            slemp.restartWeb()
            slemp.writeLog('Manajemen situs web', 'Sertifikat dideploy!')
            return slemp.returnJson(True, 'Sertifikat dideploy!')
        except Exception as ex:
            return slemp.returnJson(False, 'Pengaturan salah,' + str(ex))

    def removeCertApi(self):
        certName = request.form.get('certName', '')
        try:
            path = self.sslDir + certName
            if not os.path.exists(path):
                return slemp.returnJson(False, 'Sertifikat tidak ada lagi!')
            os.system("rm -rf " + path)
            return slemp.returnJson(True, 'Sertifikat dihapus!')
        except:
            return slemp.returnJson(False, 'Gagal menghapus!')

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
            slemp.writeFile(file, conf)

        msg = slemp.getInfo('Situs web [{1}] berhasil mematikan SSL!', (siteName,))
        slemp.writeLog('Manajemen situs web', msg)
        slemp.restartWeb()
        return slemp.returnJson(True, 'SSL mati!')

    def createLetApi(self):
        siteName = request.form.get('siteName', '')
        updateOf = request.form.get('updateOf', '')
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
            return slemp.returnJson(False, 'Silakan pilih nama domain')

        file = self.getHostConf(siteName)
        if os.path.exists(file):
            siteConf = slemp.readFile(file)
            if siteConf.find('301-END') != -1:
                return slemp.returnJson(False, 'Terdeteksi bahwa situs Anda telah menyetel pengalihan 301, harap matikan pengalihan terlebih dahulu!')

            if siteConf.find('PROXY-END') != -1:
                return slemp.returnJson(False, 'Terdeteksi bahwa situs Anda memiliki pengaturan proxy reverse, harap tutup proxy reverse terlebih dahulu!')

        letpath = self.sslDir + siteName
        csrpath = letpath + "/fullchain.pem"
        keypath = letpath + "/privkey.pem"

        actionstr = updateOf
        siteInfo = slemp.M('sites').where(
            'name=?', (siteName,)).field('id,name,path').find()
        path = self.getSitePath(siteName)
        srcPath = siteInfo['path']

        if slemp.isAppleSystem():
            user = slemp.execShell(
                "who | sed -n '2, 1p' |awk '{print $1}'")[0].strip()
            acem = '/Users/' + user + '/.acme.sh/acme.sh'
        else:
            acem = '/root/.acme.sh/acme.sh'
        if not os.path.exists(acem):
            acem = '/.acme.sh/acme.sh'
        if not os.path.exists(acem):
            try:
                slemp.execShell("curl -sS curl https://get.acme.sh | sh")
            except:
                return slemp.returnJson(False, 'Gagal menginstal ACME secara otomatis, silahkan coba install secara manual dengan perintah berikut <p>Installation command: curl https://get.acme.sh | sh</p>' + acem)
        if not os.path.exists(acem):
            return slemp.returnJson(False, 'Gagal menginstal ACME secara otomatis, silahkan coba install secara manual dengan perintah berikut <p>Installation command: curl https://get.acme.sh | sh</p>' + acem)

        checkAcmeRun = slemp.execShell('ps -ef|grep acme.sh |grep -v grep')
        if checkAcmeRun[0] != '':
            return slemp.returnJson(False, 'Memperbarui SSL...')

        if force == 'true':
            force_bool = True

        if renew == 'true':
            execStr = acem + " --renew --yes-I-know-dns-manual-mode-enough-go-ahead-please"
        else:
            execStr = acem + " --issue --force"

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
                return slemp.returnJson(False, 'Nama domain PAN tidak dapat mengajukan permohonan sertifikat menggunakan metode [verifikasi dokumen]!')
            execStr += ' -w ' + path
            execStr += ' -d ' + domain
            domainCount += 1
        if domainCount == 0:
            return slemp.returnJson(False, 'Silakan pilih nama domain (tidak termasuk alamat IP dan nama domain generik)!')

        home_path = '/root/.acme.sh/' + domains[0]
        home_cert = home_path + '/fullchain.cer'
        home_key = home_path + '/' + domains[0] + '.key'

        if not os.path.exists(home_cert):
            home_path = '/.acme.sh/' + domains[0]
            home_cert = home_path + '/fullchain.cer'
            home_key = home_path + '/' + domains[0] + '.key'

        if slemp.isAppleSystem():
            user = slemp.execShell(
                "who | sed -n '2, 1p' |awk '{print $1}'")[0].strip()
            acem = '/Users/' + user + '/.acme.sh/'
            if not os.path.exists(home_cert):
                home_path = acem + domains[0]
                home_cert = home_path + '/fullchain.cer'
                home_key = home_path + '/' + domains[0] + '.key'

        # print home_cert
        cmd = 'export ACCOUNT_EMAIL=' + email + ' && ' + execStr
        # print(domains)
        # print(cmd)
        result = slemp.execShell(cmd)

        if not os.path.exists(home_cert.replace("\*", "*")):
            data = {}
            data['err'] = result
            data['out'] = result[0]
            data['msg'] = 'Penerbitan gagal, kami tidak dapat memverifikasi nama domain Anda: <p>1. Periksa apakah nama domain terikat ke situs yang sesuai</p>\
                <p>2. Periksa apakah nama domain diselesaikan dengan benar ke server ini, atau resolusi belum sepenuhnya diterapkan</p>\
                <p>3. Jika situs Anda diatur dengan proxy reverse atau menggunakan CDN, harap matikan terlebih dahulu</p>\
                <p>4. Jika situs Anda telah menyetel pengalihan 301, harap tutup terlebih dahulu</p>\
                <p>5. Jika pemeriksaan di atas mengkonfirmasi bahwa tidak ada masalah, coba ganti penyedia layanan DNS</p>'
            data['result'] = {}
            if result[1].find('new-authz error:') != -1:
                data['result'] = json.loads(
                    re.search("{.+}", result[1]).group())
                if data['result']['status'] == 429:
                    data['msg'] = 'Penerbitan gagal, jumlah upaya yang gagal untuk mengajukan sertifikat telah mencapai batas atas!<p>1. Periksa apakah nama domain terikat ke situs yang sesuai</p>\
                        <p>2. Periksa apakah nama domain telah diselesaikan dengan benar ke server ini, atau resolusi belum sepenuhnya diterapkan.</p>\
                        <p>3. Jika situs Anda diatur dengan proxy reverse atau menggunakan CDN, harap matikan terlebih dahulu</p>\
                        <p>4. Jika situs Anda telah menyetel pengalihan 301, harap tutup terlebih dahulu</p>\
                        <p>5. Jika pemeriksaan di atas mengkonfirmasi bahwa tidak ada masalah, coba ganti penyedia layanan DNS</p>'
            data['status'] = False
            return slemp.getJson(data)

        if not os.path.exists(letpath):
            slemp.execShell("mkdir -p " + letpath)
        slemp.execShell("ln -sf \"" + home_cert + "\" \"" + csrpath + '"')
        slemp.execShell("ln -sf \"" + home_key + "\" \"" + keypath + '"')
        slemp.execShell('echo "let" > "' + letpath + '/README"')
        if(actionstr == '2'):
            return slemp.returnJson(True, 'Sertifikat diperbarui!')

        result = self.setSslConf(siteName)
        if not result['status']:
            return slemp.getJson(result)
        result['csr'] = slemp.readFile(csrpath)
        result['key'] = slemp.readFile(keypath)
        slemp.restartWeb()

        return slemp.returnJson(True, 'OK', result)

    def httpToHttpsApi(self):
        siteName = request.form.get('siteName', '')
        file = self.getHostConf(siteName)
        conf = slemp.readFile(file)
        if conf:
            if conf.find('ssl_certificate') == -1:
                return slemp.returnJson(False, 'SSL saat ini tidak diaktifkan')
            to = """#error_page 404/404.html;
    #HTTP_TO_HTTPS_START
    if ($server_port !~ 443){
        rewrite ^(/.*)$ https://$host$1 permanent;
    }
    #HTTP_TO_HTTPS_END"""
            conf = conf.replace('#error_page 404/404.html;', to)
            slemp.writeFile(file, conf)

        slemp.restartWeb()
        return slemp.returnJson(True, 'Pengaturan berhasil! Sertifikat juga harus disetel!')

    def closeToHttpsApi(self):
        siteName = request.form.get('siteName', '')
        file = self.getHostConf(siteName)
        conf = slemp.readFile(file)
        if conf:
            rep = "\n\s*#HTTP_TO_HTTPS_START(.|\n){1,300}#HTTP_TO_HTTPS_END"
            conf = re.sub(rep, '', conf)
            rep = "\s+if.+server_port.+\n.+\n\s+\s*}"
            conf = re.sub(rep, '', conf)
            slemp.writeFile(file, conf)

        slemp.restartWeb()
        return slemp.returnJson(True, 'Matikan pengalihan HTTPS sukses!')

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

    def getRewriteConfApi(self):
        siteName = request.form.get('siteName', '')
        rewrite = self.getRewriteConf(siteName)
        return slemp.getJson({'rewrite': rewrite})

    def getRewriteTplApi(self):
        tplname = request.form.get('tplname', '')
        file = slemp.getRunDir() + '/rewrite/nginx/' + tplname + '.conf'
        if not os.path.exists(file):
            return slemp.returnJson(False, 'Templat tidak ada!')
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
        Create a site check web service
        '''
        if not slemp.isInstalledWeb():
            return slemp.returnJson(False, 'Silakan instal dan mulai layanan OpenResty!')

        pid = slemp.getServerDir() + '/openresty/nginx/logs/nginx.pid'
        if not os.path.exists(pid):
            return slemp.returnJson(False, 'Silakan mulai layanan OpenResty!')

        return slemp.returnJson(True, 'OK')

    def addDomainApi(self):
        isError = slemp.checkWebConfig()
        if isError != True:
            return slemp.returnJson(False, 'ERROR: Kesalahan terdeteksi dalam file konfigurasi, harap kecualikan sebelum melanjutkan<br><br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')

        domain = request.form.get('domain', '')
        webname = request.form.get('webname', '')
        pid = request.form.get('id', '')
        return self.addDomain(domain, webname, pid)

    def addDomain(self, domain, webname, pid):
        if len(domain) < 3:
            return slemp.returnJson(False, 'Nama domain tidak boleh kosong!')
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
                return slemp.returnJson(False, 'Format nama domain salah!')

            if len(domain) == 2:
                domain_port = domain[1]
            if domain_port == "":
                domain_port = "80"

            if not slemp.checkPort(domain_port):
                return slemp.returnJson(False, 'Rentang port tidak valid!')

            opid = slemp.M('domain').where(
                "name=? AND (port=? OR pid=?)", (domain, domain_port, pid)).getField('pid')
            if opid:
                if slemp.M('sites').where('id=?', (opid,)).count():
                    return slemp.returnJson(False, 'Nama domain yang ditentukan telah terpasang!')
                slemp.M('domain').where('pid=?', (opid,)).delete()

            if slemp.M('binding').where('domain=?', (domain,)).count():
                return slemp.returnJson(False, 'Nama domain yang anda tambahkan sudah ada!')

            self.nginxAddDomain(webname, domain_name, domain_port)

            slemp.restartWeb()
            msg = slemp.getInfo('Situs web [{1}] berhasil menambahkan nama domain [{2}]!', (webname, domain_name))
            slemp.writeLog('Manajemen situs web', msg)
            slemp.M('domain').add('pid,name,port,addtime',
                               (pid, domain_name, domain_port, slemp.getDate()))

        return slemp.returnJson(True, 'Nama domain berhasil ditambahkan!')

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
            slemp.returnJson(False, 'Direktori tidak boleh kosong!')

        reg = "^([\w\-\*]{1,100}\.){1,4}(\w{1,10}|\w{1,10}\.\w{1,10})$"
        if not re.match(reg, domain):
            return slemp.returnJson(False, 'Format nama domain utama salah!')

        siteInfo = slemp.M('sites').where(
            "id=?", (pid,)).field('id,path,name').find()
        webdir = siteInfo['path'] + '/' + dirName

        if slemp.M('binding').where("domain=?", (domain,)).count() > 0:
            return slemp.returnJson(False, 'Nama domain yang anda tambahkan sudah ada!')
        if slemp.M('domain').where("name=?", (domain,)).count() > 0:
            return slemp.returnJson(False, 'Nama domain yang anda tambahkan sudah ada!')

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
            content = content.replace('{$LOGPATH}', slemp.getLogsDir())

            conf += "\r\n" + content
            shutil.copyfile(filename, '/tmp/backup.conf')
            slemp.writeFile(filename, conf)
        conf = slemp.readFile(filename)

        isError = slemp.checkWebConfig()
        if isError != True:
            shutil.copyfile('/tmp/backup.conf', filename)
            return slemp.returnJson(False, 'ERROR: <br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')

        slemp.M('binding').add('pid,domain,port,path,addtime',
                            (pid, domain, port, dirName, slemp.getDate()))

        slemp.restartWeb()
        msg = slemp.getInfo('Situs [{1}] subdirektori [{2}] terikat dengan [{3}]',
                         (siteInfo['name'], dirName, domain))
        slemp.writeLog('Manajemen situs web', msg)
        return slemp.returnJson(True, 'Berhasil ditambahkan!')

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
        msg = slemp.getInfo('Hapus situs [{1}] subdirektori [{2}] binding',
                         (siteName, binding['path']))
        slemp.writeLog('Manajemen situs web', msg)
        return slemp.returnJson(True, 'Berhasil dihapus!')

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
            return slemp.returnJson(False,  "Direktori tidak boleh kosong!")

        import files_api
        if not files_api.files_api().checkDir(path):
            return slemp.returnJson(False,  "Tidak dapat menggunakan direktori kritis sistem sebagai direktori situs")

        siteFind = slemp.M("sites").where(
            "id=?", (mid,)).field('path,name').find()
        if siteFind["path"] == path:
            return slemp.returnJson(False,  "Konsisten dengan jalur aslinya, tidak perlu dimodifikasi!")
        file = self.getHostConf(siteFind['name'])
        conf = slemp.readFile(file)
        if conf:
            conf = conf.replace(siteFind['path'], path)
            slemp.writeFile(file, conf)

        slemp.restartWeb()
        slemp.M("sites").where("id=?", (mid,)).setField('path', path)
        msg = slemp.getInfo('Mengubah jalur fisik situs web [{1}] berhasil!', (siteFind['name'],))
        slemp.writeLog('Manajemen situs web', msg)
        return slemp.returnJson(True,  "Pengaturan berhasil!")

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

        self.delUserInI(sitePath)
        self.setDirUserINI(newPath)

        slemp.restartWeb()
        return slemp.returnJson(True, 'Pengaturan berhasil!')

    def setHasPwdApi(self):
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        siteName = request.form.get('siteName', '')
        mid = request.form.get('id', '')

        if len(username.strip()) == 0 or len(password.strip()) == 0:
            return slemp.returnJson(False, 'Nama pengguna atau kata sandi tidak boleh kosong!')

        if siteName == '':
            siteName = slemp.M('sites').where('id=?', (mid,)).getField('name')

        filename = self.passPath + '/' + siteName + '.pass'
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
        msg = slemp.getInfo('Setel situs [{1}] untuk meminta otentikasi kata sandi!', (siteName,))
        slemp.writeLog("Manajemen situs web", msg)
        return slemp.returnJson(True, 'Pengaturan berhasil!')

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
        msg = slemp.getInfo('Hapus autentikasi sandi untuk situs [{1}]!', (siteName,))
        slemp.writeLog("Manajemen situs web", msg)
        return slemp.returnJson(True, 'Pengaturan berhasil!')

    def delDomainApi(self):
        domain = request.form.get('domain', '')
        webname = request.form.get('webname', '')
        port = request.form.get('port', '')
        pid = request.form.get('id', '')

        find = slemp.M('domain').where("pid=? AND name=?",
                                    (pid, domain)).field('id,name').find()

        domain_count = slemp.M('domain').where("pid=?", (pid,)).count()
        if domain_count == 1:
            return slemp.returnJson(False, 'Nama domain terakhir tidak dapat dihapus!')

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
        msg = slemp.getInfo('Situs web [{1}] berhasil menghapus nama domain [{2}]!', (webname, domain))
        slemp.writeLog('Manajemen situs web', msg)
        slemp.restartWeb()
        return slemp.returnJson(True, 'Situs berhasil dihapus!')

    def deleteApi(self):
        sid = request.form.get('id', '')
        webname = request.form.get('webname', '')
        path = request.form.get('path', '0')
        return self.delete(sid, webname, path)

    def operateRedirectConf(self, siteName, method='start'):
        vhost_file = self.vhostPath + '/' + siteName + '.conf'
        content = slemp.readFile(vhost_file)

        cnf_301 = '''
    #301-START
    include %s/*.conf;
    #301-END
''' % (self.getRedirectPath( siteName))

        cnf_301_source = '''
    #301-START
'''
        if content.find('#301-END') != -1:
            if method == 'stop':
                rep = '#301-START(\n|.){1,500}#301-END'
                content = re.sub(rep, '#301-START', content)
        else:
            if method == 'start':
                content = re.sub(cnf_301_source, cnf_301, content)

        slemp.writeFile(vhost_file, content)

    def getRedirectApi(self):
        _siteName = request.form.get("siteName", '')

        data_path = self.getRedirectDataPath(_siteName)
        data_content = slemp.readFile(data_path)
        if data_content == False:
            slemp.execShell("mkdir {}/{}".format(self.redirectPath, _siteName))
            return slemp.returnJson(True, "", {"result": [], "count": 0})
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
            return slemp.returnJson(False, "Bidang yang wajib diisi tidak boleh kosong!")

        data = slemp.readFile(
            "{}/{}/{}.conf".format(self.redirectPath, _siteName, _id))
        if data == False:
            return slemp.returnJson(False, "Gagal!")
        return slemp.returnJson(True, "ok", {"result": data})

    def saveRedirectConfApi(self):
        _siteName = request.form.get("siteName", '')
        _id = request.form.get("id", '')
        _config = request.form.get("config", "")
        if _id == '' or _siteName == '':
            return slemp.returnJson(False, "Bidang yang wajib diisi tidak boleh kosong!")

        _old_config = slemp.readFile(
            "{}/{}/{}.conf".format(self.redirectPath, _siteName, _id))
        if _old_config == False:
            return slemp.returnJson(False, "Aksi tidak dibolehkan")

        slemp.writeFile("{}/{}/{}.conf".format(self.redirectPath,
                                            _siteName, _id), _config)
        rule_test = slemp.checkWebConfig()
        if rule_test != True:
            slemp.writeFile("{}/{}/{}.conf".format(self.redirectPath,
                                                _siteName, _id), _old_config)
            return slemp.returnJson(False, "Uji konfigurasi openResty gagal, silakan coba lagi: {}".format(rule_test))

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
            return slemp.returnJson(False, "Bidang yang wajib diisi tidak boleh kosong!")

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
                return slemp.returnJson(False, "Nama domain tidak ada!")

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
                return slemp.returnJson(False, "Pengaturan duplikat!")

        rep = "http(s)?\:\/\/([a-zA-Z0-9][-a-zA-Z0-9]{0,62}\.)+([a-zA-Z0-9][a-zA-Z0-9]{0,62})+.?"
        if not re.match(rep, _to):
            return slemp.returnJson(False, "Salah alamat tujuan")

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
            return slemp.returnJson(False, "Bidang yang wajib diisi tidak boleh kosong!")

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
            return slemp.returnJson(False, "Gagal menghapus!")
        return slemp.returnJson(True, "Berhasil dihapus!")

    def operateProxyConf(self, siteName, method='start'):
        vhost_file = self.vhostPath + '/' + siteName + '.conf'
        content = slemp.readFile(vhost_file)

        proxy_cnf = '''
    #PROXY-START
    include %s/*.conf;
    #PROXY-END
''' % (self.getProxyPath(siteName))

        proxy_cnf_source = '''
    #PROXY-START
'''

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
            return slemp.returnJson(False, "Bidang yang wajib diisi tidak boleh kosong!")

        conf_file = "{}/{}/{}.conf".format(self.proxyPath, _siteName, _id)
        if not os.path.exists(conf_file):
            conf_file = "{}/{}/{}.conf.txt".format(
                self.proxyPath, _siteName, _id)

        data = slemp.readFile(conf_file)
        if data == False:
            return slemp.returnJson(False, "Gagal!")
        return slemp.returnJson(True, "ok", {"result": data})

    def setProxyStatusApi(self):
        _siteName = request.form.get("siteName", '')
        _status = request.form.get("status", '')
        _id = request.form.get("id", '')
        if _status == '' or _siteName == '' or _id == '':
            return slemp.returnJson(False, "Bidang yang wajib diisi tidak boleh kosong!")

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
            return slemp.returnJson(False, "Bidang yang wajib diisi tidak boleh kosong!")

        _old_config = slemp.readFile(
            "{}/{}/{}.conf".format(self.proxyPath, _siteName, _id))
        if _old_config == False:
            return slemp.returnJson(False, "Aksi tidak dibolehkan")

        slemp.writeFile("{}/{}/{}.conf".format(self.proxyPath,
                                            _siteName, _id), _config)
        rule_test = slemp.checkWebConfig()
        if rule_test != True:
            slemp.writeFile("{}/{}/{}.conf".format(self.proxyPath,
                                                _siteName, _id), _old_config)
            return slemp.returnJson(False, "Tes konfigurasi OpenResty gagal, silakan coba lagi: {}".format(rule_test))

        self.operateRedirectConf(_siteName, 'start')
        slemp.restartWeb()
        return slemp.returnJson(True, "ok")

    def getProxyListApi(self):
        _siteName = request.form.get('siteName', '')

        data_path = self.getProxytDataPath(_siteName)
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
        _open_proxy = request.form.get('open_proxy', '')

        if _siteName == "" or _from == "" or _to == "" or _host == "":
            return slemp.returnJson(False, "Bidang yang wajib diisi tidak boleh kosong")

        data_path = self.getProxytDataPath(_siteName)
        data_content = slemp.readFile(
            data_path) if os.path.exists(data_path) else ""
        data = json.loads(data_content) if data_content != "" else []

        rep = "http(s)?\:\/\/([a-zA-Z0-9][-a-zA-Z0-9]{0,62}\.)+([a-zA-Z0-9][a-zA-Z0-9]{0,62})+.?"
        if not re.match(rep, _to):
            return slemp.returnJson(False, "Salah alamat tujuan!")

        # _to = _to.strip("/")
        # get host from url
        try:
            if _host == "$host":
                host_tmp = urlparse(_to)
                _host = host_tmp.netloc
        except:
            return slemp.returnJson(False, "Salah alamat tujuan")

        # location ~* ^{from}(.*)$ {
        tpl = """
# PROXY-START/
location ^~ {from} {
    proxy_pass {to};
    proxy_set_header Host {host};
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header REMOTE-HOST $remote_addr;

    add_header X-Cache $upstream_cache_status;
    proxy_ignore_headers Set-Cookie Cache-Control expires;
    add_header Cache-Control no-cache;

    set $static_files_app 0;
    if ( $uri ~* "\.(gif|png|jpg|css|js|woff|woff2)$" )
    {
        set $static_files_app 1;
        expires 12h;
    }
    if ( $static_files_app = 0 )
    {
        add_header Cache-Control no-cache;
    }
}
# PROXY-END/
        """

        # replace
        if _from[0] != '/':
            _from = '/' + _from
        tpl = tpl.replace("{from}", _from, 999)
        tpl = tpl.replace("{to}", _to)
        tpl = tpl.replace("{host}", _host, 999)

        _id = slemp.md5("{}+{}+{}".format(_from, _to, _siteName))
        for item in data:
            if item["id"] == _id:
                return slemp.returnJson(False, "Aturannya sudah ada!")
            if item["from"] == _from:
                return slemp.returnJson(False, "Direktori proxy sudah ada!")
        data.append({
            "from": _from,
            "to": _to,
            "host": _host,
            "id": _id
        })

        conf_file = "{}/{}.conf".format(self.getProxyPath(_siteName), _id)
        if _open_proxy != 'on':
            conf_file = "{}/{}.conf.txt".format(
                self.getProxyPath(_siteName), _id)

        slemp.writeFile(data_path, json.dumps(data))
        slemp.writeFile(conf_file, tpl)

        self.operateProxyConf(_siteName, 'start')
        slemp.restartWeb()
        return slemp.returnJson(True, "ok", {"hash": _id})

    def delProxyApi(self):
        _siteName = request.form.get("siteName", '')
        _id = request.form.get("id", '')
        if _id == '' or _siteName == '':
            return slemp.returnJson(False, "Bidang yang wajib diisi tidak boleh kosong!")

        try:
            data_path = self.getProxytDataPath(_siteName)
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
            return slemp.returnJson(False, "Gagal menghapus!")

        slemp.restartWeb()
        return slemp.returnJson(True, "Berhasil dihapus!")

    def getSiteTypesApi(self):
        data = slemp.M("site_types").field("id,name").order("id asc").select()
        data.insert(0, {"id": 0, "name": "Kategori default"})
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
            return slemp.returnJson(False, "Nama kategori tidak boleh kosong")
        if len(name) > 18:
            return slemp.returnJson(False, "Panjang nama kategori tidak boleh melebihi 18 karakter")
        if slemp.M('site_types').count() >= 10:
            return slemp.returnJson(False, 'Tambahkan hingga 10 kategori!')
        if slemp.M('site_types').where('name=?', (name,)).count() > 0:
            return slemp.returnJson(False, "Nama kategori yang ditentukan sudah ada!")
        slemp.M('site_types').add("name", (name,))
        return slemp.returnJson(True, 'Berhasil ditambahkan!')

    def removeSiteTypeApi(self):
        mid = request.form.get('id', '')
        if slemp.M('site_types').where('id=?', (mid,)).count() == 0:
            return slemp.returnJson(False, "Kategori yang ditentukan tidak ada!")
        slemp.M('site_types').where('id=?', (mid,)).delete()
        slemp.M("sites").where("type_id=?", (mid,)).save("type_id", (0,))
        return slemp.returnJson(True, "Kategori dihapus!")

    def modifySiteTypeNameApi(self):
        name = request.form.get('name', '').strip()
        mid = request.form.get('id', '')
        if not name:
            return slemp.returnJson(False, "Nama kategori tidak boleh kosong")
        if len(name) > 18:
            return slemp.returnJson(False, "Panjang nama kategori tidak boleh melebihi 18 karakter")
        if slemp.M('site_types').where('id=?', (mid,)).count() == 0:
            return slemp.returnJson(False, "Kategori yang ditentukan tidak ada!")
        slemp.M('site_types').where('id=?', (mid,)).setField('name', name)
        return slemp.returnJson(True, "Berhasil dimodifikasi!")

    def setSiteTypeApi(self):
        site_ids = request.form.get('site_ids', '')
        mid = request.form.get('id', '')
        site_ids = json.loads(site_ids)
        for sid in site_ids:
            print(slemp.M('sites').where('id=?', (sid,)).setField('type_id', mid))
        return slemp.returnJson(True, "Pengaturan berhasil!")

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

    def getProxytDataPath(self, siteName):
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
            return slemp.returnJson(False, 'Lognya kosong')
        return slemp.returnJson(True, slemp.getNumLines(logPath, 100))

    def getErrorLogs(self, siteName):
        logPath = slemp.getLogsDir() + '/' + siteName + '.error.log'
        if not os.path.exists(logPath):
            return slemp.returnJson(False, 'Lognya kosong')
        return slemp.returnJson(True, slemp.getNumLines(logPath, 100))

    def getLogsStatus(self, siteName):
        filename = self.getHostConf(siteName)
        conf = slemp.readFile(filename)
        if conf.find('#ErrorLog') != -1:
            return False
        if conf.find("access_log  /dev/null") != -1:
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
            return slemp.returnJson(False,  'Format dokumen default salah, misalnya: index.html')

        index = index.replace(' ', '')
        index = index.replace(',,', ',')

        if len(index) < 3:
            return slemp.returnJson(False,  'Dokumen default tidak boleh kosong!')

        siteName = slemp.M('sites').where("id=?", (sid,)).getField('name')
        index_l = index.replace(",", " ")
        file = self.getHostConf(siteName)
        conf = slemp.readFile(file)
        if conf:
            rep = "\s+index\s+.+;"
            conf = re.sub(rep, "\n\tindex " + index_l + ";", conf)
            slemp.writeFile(file, conf)

        slemp.writeLog('Manajemen situs web', 'Dokumen default untuk situs [{1}] disetel ke [{2}]', (siteName, index_l))
        return slemp.returnJson(True,  'Pengaturan berhasil!')

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
        slemp.writeLog('Manajemen situs web', 'Pembatasan lalu lintas situs web [{1}] aktif!', (siteName,))
        return slemp.returnJson(True, 'Pengaturan berhasil!')

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
            'Manajemen situs web', 'Pembatasan lalu lintas situs web [{1}] ditutup!', (siteName,))
        return slemp.returnJson(True, 'Pembatasan lalu lintas dimatikan!')

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
            return slemp.returnJson(False, 'Akhiran URL tidak boleh kosong!')
        file = self.getHostConf(name)
        if os.path.exists(file):
            conf = slemp.readFile(file)
            if conf.find('SECURITY-START') != -1:
                rep = "\s{0,4}#SECURITY-START(\n|.){1,500}#SECURITY-END\n?"
                conf = re.sub(rep, '', conf)
                slemp.writeLog('Manajemen situs web', 'Situs [' + name + '] telah mematikan pengaturan anti-leech!')
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
    # SECURITY-END
    include %s/enable-php-''' % (fix.strip().replace(',', '|'), domains.strip().replace(',', ' '), pre_path)
                conf = re.sub(re_path, rconf, conf)
                slemp.writeLog('Manajemen situs web', 'Situs [' + nama + '] memiliki anti-leech!')
            slemp.writeFile(file, conf)
        slemp.restartWeb()
        return slemp.returnJson(True, 'Pengaturan berhasil!')

    def getPhpVersion(self):
        phpVersions = ('00', '52', '53', '54', '55',
                       '56', '70', '71', '72', '73', '74', '80', '81', '82')
        data = []
        for val in phpVersions:
            tmp = {}
            if val == '00':
                tmp['version'] = '00'
                tmp['name'] = 'Statis murni'
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

        return slemp.getJson(data)

    def isToHttps(self, siteName):
        file = self.getHostConf(siteName)
        conf = slemp.readFile(file)
        if conf:
            if conf.find('HTTP_TO_HTTPS_START') != -1:
                return True
            if conf.find('$server_port !~ 443') != -1:
                return True
        return False

    def getRewriteList(self):
        rewriteList = {}
        rewriteList['rewrite'] = []
        rewriteList['rewrite'].append('0.Saat ini')
        for ds in os.listdir('rewrite/nginx'):
            rewriteList['rewrite'].append(ds[0:len(ds) - 5])
        rewriteList['rewrite'] = sorted(rewriteList['rewrite'])
        return rewriteList

    def createRootDir(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
        if not slemp.isAppleSystem():
            slemp.execShell('chown -R www:www ' + path)
        slemp.writeFile(path + '/index.html', 'Situs berhasil dibuat!!!')
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

        logsPath = slemp.getLogsDir()
        content = content.replace('{$LOGPATH}', logsPath)
        slemp.writeFile(vhost_file, content)

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
            return slemp.returnJson(False, 'Situs yang anda tambahkan sudah ada!')

        pid = slemp.M('sites').add('name,path,status,ps,edate,addtime,type_id',
                                (self.siteName, self.sitePath, '1', ps, '0000-00-00', slemp.getDate(), 0,))
        opid = slemp.M('domain').where(
            "name=?", (self.siteName,)).getField('pid')
        if opid:
            if slemp.M('sites').where('id=?', (opid,)).count():
                return slemp.returnJson(False, 'Nama domain yang anda tambahkan sudah ada!')
            slemp.M('domain').where('pid=?', (opid,)).delete()

        for domain in siteMenu['domainlist']:
            sdomain = domain
            swebname = self.siteName
            spid = str(pid)
            self.addDomain(domain, webname, pid)

        slemp.M('domain').add('pid,name,port,addtime',
                           (pid, self.siteName, self.sitePort, slemp.getDate()))

        self.createRootDir(self.sitePath)
        self.nginxAddConf()

        data = {}
        data['siteStatus'] = False
        slemp.restartWeb()
        return slemp.returnJson(True, 'Berhasil ditambahkan')

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

        slemp.M('sites').where("id=?", (sid,)).delete()
        slemp.restartWeb()
        return slemp.returnJson(True, 'Situs berhasil dihapus!')

    def setEndDate(self, sid, edate):
        result = slemp.M('sites').where(
            'id=?', (sid,)).setField('edate', edate)
        siteName = slemp.M('sites').where('id=?', (sid,)).getField('name')
        slemp.writeLog('Manajemen situs web', 'Setelah pengaturan berhasil, situs akan otomatis berhenti setelah habis masa berlakunya!', (siteName, edate))
        return slemp.returnJson(True, 'Jika pengaturan berhasil, situs akan secara otomatis berhenti ketika kedaluwarsa!')

    def setSslConf(self, siteName):
        file = self.getHostConf(siteName)
        conf = slemp.readFile(file)

        keyPath = self.sslDir + siteName + '/privkey.pem'
        certPath = self.sslDir + siteName + '/fullchain.pem'
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
    error_page 497  https://$host$request_uri;
""" % (certPath, keyPath)
            if(conf.find('ssl_certificate') != -1):
                return slemp.returnData(True, 'SSL berhasil diaktifkan!')

            conf = conf.replace('#error_page 404/404.html;', sslStr)

            rep = "listen\s+([0-9]+)\s*[default_server]*;"
            tmp = re.findall(rep, conf)
            if not slemp.inArray(tmp, '443'):
                listen = re.search(rep, conf).group()
                conf = conf.replace(
                    listen, listen + "\n\tlisten 443 ssl http2;")
            shutil.copyfile(file, '/tmp/backup.conf')

            slemp.writeFile(file, conf)
            isError = slemp.checkWebConfig()
            if(isError != True):
                shutil.copyfile('/tmp/backup.conf', file)
                return slemp.returnData(False, 'Kesalahan sertifikat: <br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')

        slemp.restartWeb()
        self.saveCert(keyPath, certPath)

        msg = slemp.getInfo('Situs web [{1}] berhasil mengaktifkan SSL!', siteName)
        slemp.writeLog('Manajemen situs web', msg)
        return slemp.returnData(True, 'SSL berhasil diaktifkan!')

    def saveCert(self, keyPath, certPath):
        try:
            certInfo = self.getCertName(certPath)
            if not certInfo:
                return slemp.returnData(False, 'Penguraian sertifikat gagal!')
            vpath = self.sslDir + certInfo['subject'].strip()
            if not os.path.exists(vpath):
                os.system('mkdir -p ' + vpath)
            slemp.writeFile(vpath + '/privkey.pem',
                         slemp.readFile(keyPath))
            slemp.writeFile(vpath + '/fullchain.pem',
                         slemp.readFile(certPath))
            slemp.writeFile(vpath + '/info.json', json.dumps(certInfo))
            return slemp.returnData(True, 'Sertifikat berhasil disimpan!')
        except Exception as e:
            return slemp.returnData(False, 'Penyimpanan sertifikat gagal!')

    def getCertName(self, certPath):
        try:
            openssl = '/usr/local/openssl/bin/openssl'
            if not os.path.exists(openssl):
                openssl = 'openssl'
            result = slemp.execShell(
                openssl + " x509 -in " + certPath + " -noout -subject -enddate -startdate -issuer")
            tmp = result[0].split("\n")
            data = {}
            data['subject'] = tmp[0].split('=')[-1]
            data['notAfter'] = self.strfToTime(tmp[1].split('=')[1])
            data['notBefore'] = self.strfToTime(tmp[2].split('=')[1])
            data['issuer'] = tmp[3].split('O=')[-1].split(',')[0]
            if data['issuer'].find('/') != -1:
                data['issuer'] = data['issuer'].split('/')[0]
            result = slemp.execShell(
                openssl + " x509 -in " + certPath + " -noout -text|grep DNS")
            data['dns'] = result[0].replace(
                'DNS:', '').replace(' ', '').strip().split(',')
            return data
        except:
            return None

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

    def setDirUserINI(self, newPath):
        filename = newPath + '/.user.ini'
        if os.path.exists(filename):
            slemp.execShell("chattr -i " + filename)
            os.remove(filename)
            return slemp.returnJson(True, 'Pengaturan anti-cross-site dihapus!')

        self.delUserInI(newPath)
        slemp.writeFile(filename, 'open_basedir=' +
                     newPath + '/:/home/slemp/server/php:/tmp/:/proc/')
        slemp.execShell("chattr +i " + filename)

        return slemp.returnJson(True, 'Pengaturan anti-cross-site diaktifkan!')

    def strfToTime(self, sdate):
        import time
        return time.strftime('%Y-%m-%d', time.strptime(sdate, '%b %d %H:%M:%S %Y %Z'))
