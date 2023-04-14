# coding: utf-8

import psutil
import time
import os
import sys
import slemp
import re
import json
import pwd

from flask import session
from flask import request


class config_api:

    __version = '3.6'
    __api_addr = 'data/api.json'

    def __init__(self):
        pass

    def getVersion(self):
        return self.__version

    ##### ----- start ----- ###

    def getPanelListApi(self):
        data = slemp.M('panel').field(
            'id,title,url,username,password,click,addtime').order('click desc').select()
        return slemp.getJson(data)

    def addPanelInfoApi(self):
        title = request.form.get('title', '')
        url = request.form.get('url', '')
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        isAdd = slemp.M('panel').where(
            'title=? OR url=?', (title, url)).count()
        if isAdd:
            return slemp.returnJson(False, 'Alamat paanel sudah terdaftar!')
        isRe = slemp.M('panel').add('title,url,username,password,click,addtime',
                                 (title, url, username, password, 0, int(time.time())))
        if isRe:
            return slemp.returnJson(True, 'Alamat panel berhasil ditambah!')
        return slemp.returnJson(False, 'Penambahan alamat panel gagal!')

    def delPanelInfoApi(self):
        mid = request.form.get('id', '')
        isExists = slemp.M('panel').where('id=?', (mid,)).count()
        if not isExists:
            return slemp.returnJson(False, 'Data alamat panel yang diinginkan tidak ada!')
        slemp.M('panel').where('id=?', (mid,)).delete()
        return slemp.returnJson(True, 'Data alamat panel berhasil dihapus!')

    def setPanelInfoApi(self):
        title = request.form.get('title', '')
        url = request.form.get('url', '')
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        mid = request.form.get('id', '')
        isSave = slemp.M('panel').where(
            '(title=? OR url=?) AND id!=?', (title, url, mid)).count()
        if isSave:
            return slemp.returnJson(False, 'Alamat paanel sudah terdaftar!')

        isRe = slemp.M('panel').where('id=?', (mid,)).save(
            'title,url,username,password', (title, url, username, password))
        if isRe:
            return slemp.returnJson(True, 'Alamat panel berhasil diubah!')
        return slemp.returnJson(False, 'Gagal mengganti alamat panel!')

    def syncDateApi(self):
        if slemp.isAppleSystem():
            return slemp.returnJson(True, 'Sinkronisasi waktu tidak disupport!')

        data = slemp.execShell('ntpdate -s time.nist.gov')
        if data[0] == '':
            return slemp.returnJson(True, 'Sinkronisasi waktu berhasil dilakukan!')
        return slemp.returnJson(False, 'Sinkronisasi waktu gagal:' + data[0])

    def setPasswordApi(self):
        password1 = request.form.get('password1', '')
        password2 = request.form.get('password2', '')
        if password1 != password2:
            return slemp.returnJson(False, 'Kata sandi yang dimasukkan dua kali tidak cocok, harap masukkan kembali!')
        if len(password1) < 5:
            return slemp.returnJson(False, 'Kata sandi pengguna tidak boleh kurang dari 5 digit!')
        slemp.M('users').where("username=?", (session['username'],)).setField(
            'password', slemp.md5(password1.strip()))
        return slemp.returnJson(True, 'Penyetelan ulang kata sandi selesai!')

    def setNameApi(self):
        name1 = request.form.get('name1', '')
        name2 = request.form.get('name2', '')
        if name1 != name2:
            return slemp.returnJson(False, 'Nama pengguna yang dimasukkan dua kali tidak cocok, harap masukkan kembali!')
        if len(name1) < 3:
            return slemp.returnJson(False, 'Nama pengguna minimal 3 karakter')

        slemp.M('users').where("username=?", (session['username'],)).setField(
            'username', name1.strip())

        session['username'] = name1
        return slemp.returnJson(True, 'Akun pengguna berhasil dimodifikasi!')

    def setWebnameApi(self):
        webname = request.form.get('webname', '')
        if webname != slemp.getConfig('title'):
            slemp.setConfig('title', webname)
        return slemp.returnJson(True, 'Panel alias saved successfully!')

    def setPortApi(self):
        port = request.form.get('port', '')
        if port != slemp.getHostPort():
            import system_api
            import firewall_api

            sysCfgDir = slemp.systemdCfgDir()
            if os.path.exists(sysCfgDir + "/firewalld.service"):
                if not firewall_api.firewall_api().getFwStatus():
                    return slemp.returnJson(False, 'firewalld must be started first!')

            slemp.setHostPort(port)

            msg = slemp.getInfo('Successfully released port [{1}]', (port,))
            slemp.writeLog("Firewall management", msg)
            addtime = time.strftime('%Y-%m-%d %X', time.localtime())
            slemp.M('firewall').add('port,ps,addtime', (port, "Configuration modification", addtime))

            firewall_api.firewall_api().addAcceptPort(port)
            firewall_api.firewall_api().firewallReload()

            system_api.system_api().restartSlemp()

        return slemp.returnJson(True, 'Port saved successfully!')

    def setIpApi(self):
        host_ip = request.form.get('host_ip', '')
        if host_ip != slemp.getHostAddr():
            slemp.setHostAddr(host_ip)
        return slemp.returnJson(True, 'IP saved successfully!')

    def setWwwDirApi(self):
        sites_path = request.form.get('sites_path', '')
        if sites_path != slemp.getWwwDir():
            slemp.setWwwDir(sites_path)
        return slemp.returnJson(True, 'Modify the default website directory successfully!')

    def setBackupDirApi(self):
        backup_path = request.form.get('backup_path', '')
        if backup_path != slemp.getBackupDir():
            slemp.setBackupDir(backup_path)
        return slemp.returnJson(True, 'Modify the default backup directory successfully!')

    def setBasicAuthApi(self):
        basic_user = request.form.get('basic_user', '').strip()
        basic_pwd = request.form.get('basic_pwd', '').strip()
        basic_open = request.form.get('is_open', '').strip()

        salt = '_md_salt'
        path = 'data/basic_auth.json'
        is_open = True

        if basic_open == 'false':
            if os.path.exists(path):
                os.remove(path)
            return slemp.returnJson(True, 'Delete BasicAuth successfully!')

        if basic_user == '' or basic_pwd == '':
            return slemp.returnJson(True, 'User and password cannot be empty!')

        ba_conf = None
        if os.path.exists(path):
            try:
                ba_conf = json.loads(slemp.readFile(path))
            except:
                os.remove(path)

        if not ba_conf:
            ba_conf = {
                "basic_user": slemp.md5(basic_user + salt),
                "basic_pwd": slemp.md5(basic_pwd + salt),
                "open": is_open
            }
        else:
            ba_conf['basic_user'] = slemp.md5(basic_user + salt)
            ba_conf['basic_pwd'] = slemp.md5(basic_pwd + salt)
            ba_conf['open'] = is_open

        slemp.writeFile(path, json.dumps(ba_conf))
        os.chmod(path, 384)
        slemp.writeLog('Panel settings', 'Set the BasicAuth state to: %s' % is_open)

        slemp.restartSlemp()
        return slemp.returnJson(True, 'Successfully set!')

    def setApi(self):
        webname = request.form.get('webname', '')
        port = request.form.get('port', '')
        host_ip = request.form.get('host_ip', '')
        domain = request.form.get('domain', '')
        sites_path = request.form.get('sites_path', '')
        backup_path = request.form.get('backup_path', '')

        if domain != '':
            reg = "^([\w\-\*]{1,100}\.){1,4}(\w{1,10}|\w{1,10}\.\w{1,10})$"
            if not re.match(reg, domain):
                return slemp.returnJson(False, 'Format nama domain utama salah')

        if int(port) >= 65535 or int(port) < 100:
            return slemp.returnJson(False, 'Rentang port salah!')

        if webname != slemp.getConfig('title'):
            slemp.setConfig('title', webname)

        if sites_path != slemp.getWwwDir():
            slemp.setWwwDir(sites_path)

        if backup_path != slemp.getWwwDir():
            slemp.setBackupDir(backup_path)

        if port != slemp.getHostPort():
            import system_api
            import firewall_api

            sysCfgDir = slemp.systemdCfgDir()
            if os.path.exists(sysCfgDir + "/firewalld.service"):
                if not firewall_api.firewall_api().getFwStatus():
                    return slemp.returnJson(False, 'Firewalld harus dijalankan terlebih dahulu!')

            slemp.setHostPort(port)

            msg = slemp.getInfo('Port [{1}] berhasil dibuka', (port,))
            slemp.writeLog("Manajemen Firewall", msg)
            addtime = time.strftime('%Y-%m-%d %X', time.localtime())
            slemp.M('firewall').add('port,ps,addtime', (port, "Modifikasi konfigurasi", addtime))

            firewall_api.firewall_api().addAcceptPort(port)
            firewall_api.firewall_api().firewallReload()

            system_api.system_api().restartSlemp()

        if host_ip != slemp.getHostAddr():
            slemp.setHostAddr(host_ip)

        mhost = slemp.getHostAddr()
        info = {
            'uri': '/config',
            'host': mhost + ':' + port
        }
        return slemp.returnJson(True, 'Saved successfully!', info)

    def setAdminPathApi(self):
        admin_path = request.form.get('admin_path', '').strip()
        admin_path_checks = ['/', '/close', '/login',
                             '/do_login', '/site', '/sites',
                             '/download_file', '/control', '/crontab',
                             '/firewall', '/files', 'config',
                             '/soft', '/system', '/code',
                             '/ssl', '/plugins', '/hook']
        if admin_path == '':
            admin_path = '/'
        if admin_path != '/':
            if len(admin_path) < 6:
                return slemp.returnJson(False, 'Panjang alamat login tidak boleh kurang dari 6 karakter!')
            if admin_path in admin_path_checks:
                return slemp.returnJson(False, 'Path login sudah digunakan oleh panel, silakan gunakan alamat login yang lain!')
            if not re.match("^/[\w\./-_]+$", admin_path):
                return slemp.returnJson(False, 'Format alamat login salah, contoh: /random_string')

        admin_path_file = 'data/admin_path.pl'
        admin_path_old = '/'
        if os.path.exists(admin_path_file):
            admin_path_old = slemp.readFile(admin_path_file).strip()

        if admin_path_old != admin_path:
            slemp.writeFile(admin_path_file, admin_path)
            slemp.restartSlemp()
        return slemp.returnJson(True, 'Berhasil dimodifikasi!')

    def closePanelApi(self):
        filename = 'data/close.pl'
        if os.path.exists(filename):
            os.remove(filename)
            return slemp.returnJson(True, 'Panel sudah dibuka')
        slemp.writeFile(filename, 'True')
        slemp.execShell("chmod 600 " + filename)
        slemp.execShell("chown root.root " + filename)
        return slemp.returnJson(True, 'Panel ditutup!')

    def openDebugApi(self):
        filename = 'data/debug.pl'
        if os.path.exists(filename):
            os.remove(filename)
            return slemp.returnJson(True, 'Development mode off!')
        slemp.writeFile(filename, 'True')
        return slemp.returnJson(True, 'Development mode on!')

    def setIpv6StatusApi(self):
        ipv6_file = 'data/ipv6.pl'
        if os.path.exists('data/ipv6.pl'):
            os.remove(ipv6_file)
            slemp.writeLog('Pengaturan panel', 'Tutup panel dengan IPv6!')
        else:
            slemp.writeFile(ipv6_file, 'True')
            slemp.writeLog('Pengaturan panel', 'Aktifkan panel dengan IPv6!')
        slemp.restartSlemp()
        return slemp.returnJson(True, 'Pengaturan berhasil!')

    def getPanelSslApi(self):
        cert = self.getPanelSslData()
        return slemp.getJson(cert)

    def getPanelSslData(self):
        cert = {}
        keyPath = 'ssl/private.pem'
        certPath = 'ssl/cert.pem'
        if not os.path.exists(certPath):
            # slemp.createSSL()
            cert['privateKey'] = ''
            cert['is_https'] = ''
            cert['certPem'] = ''
            cert['rep'] = os.path.exists('ssl/input.pl')
            cert['info'] = {'endtime': 0, 'subject': 'no',
                            'notAfter': 'no', 'notBefore': 'no', 'issuer': 'no'}
            return cert

        panel_ssl = slemp.getServerDir() + "/web_conf/nginx/vhost/panel.conf"
        if not os.path.exists(panel_ssl):
            cert['is_https'] = ''
        else:
            ssl_data = slemp.readFile(panel_ssl)
            if ssl_data.find('$server_port !~ 443') != -1:
                cert['is_https'] = 'checked'

        cert['privateKey'] = slemp.readFile(keyPath)
        cert['certPem'] = slemp.readFile(certPath)
        cert['rep'] = os.path.exists('ssl/input.pl')
        cert['info'] = slemp.getCertName(certPath)
        return cert

    def savePanelSslApi(self):
        keyPath = 'ssl/private.pem'
        certPath = 'ssl/cert.pem'
        checkCert = '/tmp/cert.pl'

        certPem = request.form.get('certPem', '').strip()
        privateKey = request.form.get('privateKey', '').strip()

        if(privateKey.find('KEY') == -1):
            return slemp.returnJson(False, 'The key is wrong, please check!')
        if(certPem.find('CERTIFICATE') == -1):
            return slemp.returnJson(False, 'Certificate error, please check!')

        slemp.writeFile(checkCert, certPem)
        if privateKey:
            slemp.writeFile(keyPath, privateKey)
        if certPem:
            slemp.writeFile(certPath, certPem)
        if not slemp.checkCert(checkCert):
            return slemp.returnJson(False, 'Certificate error, please check!')
        slemp.writeFile('ssl/input.pl', 'True')
        return slemp.returnJson(True, 'Certificate saved!')

    def setPanelHttpToHttpsApi(self):

        bind_domain = 'data/bind_domain.pl'
        if not os.path.exists(bind_domain):
            return slemp.returnJson(False, 'Bind the domain name first!')

        keyPath = 'ssl/private.pem'
        if not os.path.exists(keyPath):
            return slemp.returnJson(False, 'No SSL certificate applied!')

        is_https = request.form.get('https', '').strip()

        panel_ssl = slemp.getServerDir() + "/web_conf/nginx/vhost/panel.conf"
        if not os.path.exists(panel_ssl):
            return slemp.returnJson(False, 'Panel SSL is not turned on!')

        if is_https == 'false':
            conf = slemp.readFile(panel_ssl)
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
                slemp.writeFile(panel_ssl, conf)
        else:
            conf = slemp.readFile(panel_ssl)
            if conf:
                rep = "\n\s*#HTTP_TO_HTTPS_START(.|\n){1,300}#HTTP_TO_HTTPS_END"
                conf = re.sub(rep, '', conf)
                rep = "\s+if.+server_port.+\n.+\n\s+\s*}"
                conf = re.sub(rep, '', conf)
                slemp.writeFile(panel_ssl, conf)

        slemp.restartWeb()

        action = 'Turn on'
        if is_https == 'true':
            action = 'Turn off'
        return slemp.returnJson(True, action + 'HTTPS jump successfully!')

    def delPanelSslApi(self):
        bind_domain = 'data/bind_domain.pl'
        if not os.path.exists(bind_domain):
            return slemp.returnJson(False, 'Unbound domain name!')

        siteName = slemp.readFile(bind_domain).strip()

        src_letpath = slemp.getServerDir() + '/web_conf/letsencrypt/' + siteName

        dst_letpath = slemp.getRunDir() + '/ssl'
        dst_csrpath = dst_letpath + '/cert.pem'
        dst_keypath = dst_letpath + '/private.pem'

        if os.path.exists(src_letpath) or os.path.exists(dst_csrpath):
            if os.path.exists(src_letpath):
                slemp.execShell('rm -rf ' + src_letpath)
            if os.path.exists(dst_csrpath):
                slemp.execShell('rm -rf ' + dst_csrpath)
            if os.path.exists(dst_keypath):
                slemp.execShell('rm -rf ' + dst_keypath)
            # slemp.restartWeb()
            return slemp.returnJson(True, 'SSL removed!')

        # slemp.restartWeb()
        return slemp.returnJson(False, 'SSL no longer exists!')

    def applyPanelLetSslApi(self):

        # check domain is bind?
        bind_domain = 'data/bind_domain.pl'
        if not os.path.exists(bind_domain):
            return slemp.returnJson(False, 'Bind the domain name first!')

        siteName = slemp.readFile(bind_domain).strip()
        auth_to = slemp.getRunDir() + "/tmp"
        to_args = {
            'domains': [siteName],
            'auth_type': 'http',
            'auth_to': auth_to,
        }

        src_letpath = slemp.getServerDir() + '/web_conf/letsencrypt/' + siteName
        src_csrpath = src_letpath + "/fullchain.pem"
        src_keypath = src_letpath + "/privkey.pem"

        dst_letpath = slemp.getRunDir() + '/ssl'
        dst_csrpath = dst_letpath + '/cert.pem'
        dst_keypath = dst_letpath + '/private.pem'

        is_already_apply = False

        if not os.path.exists(src_letpath):
            import cert_api
            data = cert_api.cert_api().applyCertApi(to_args)
            if not data['status']:
                msg = data['msg']
                if type(data['msg']) != str:
                    msg = data['msg'][0]
                    emsg = data['msg'][1]['challenges'][0]['error']
                    msg = msg + '<p><span>Response status:</span>' + str(emsg['status']) + '</p><p><span>Error type:</span>' + emsg[
                        'type'] + '</p><p><span>Error code:</span>' + emsg['detail'] + '</p>'
                return slemp.returnJson(data['status'], msg, data['msg'])

        else:
            is_already_apply = True

        slemp.buildSoftLink(src_csrpath, dst_csrpath, True)
        slemp.buildSoftLink(src_keypath, dst_keypath, True)
        slemp.execShell('echo "lets" > "' + dst_letpath + '/README"')

        data = self.getPanelSslData()

        tmp_well_know = auth_to + '/.well-known'
        if os.path.exists(tmp_well_know):
            slemp.execShell('rm -rf ' + tmp_well_know)

        if is_already_apply:
            return slemp.returnJson(True, 'Repeat application!', data)

        return slemp.returnJson(True, 'Successful application!', data)

    def setPanelDomainApi(self):
        domain = request.form.get('domain', '')

        panel_tpl = slemp.getRunDir() + "/data/tpl/nginx_panel.conf"
        dst_panel_path = slemp.getServerDir() + "/web_conf/nginx/vhost/panel.conf"

        cfg_domain = 'data/bind_domain.pl'
        if domain == '':
            os.remove(cfg_domain)
            os.remove(dst_panel_path)
            slemp.restartWeb()
            return slemp.returnJson(True, 'The domain name was cleared successfully!')

        reg = r"^([\w\-\*]{1,100}\.){1,4}(\w{1,10}|\w{1,10}\.\w{1,10})$"
        if not re.match(reg, domain):
            return slemp.returnJson(False, 'Primary domain name format is incorrect')

        op_dir = slemp.getServerDir() + "/openresty"
        if not os.path.exists(op_dir):
            return slemp.returnJson(False, 'Rely on OpenResty, first install and start it!')

        content = slemp.readFile(panel_tpl)
        content = content.replace("{$PORT}", "80")
        content = content.replace("{$SERVER_NAME}", domain)
        content = content.replace("{$PANAL_PORT}", slemp.readFile('data/port.pl'))
        content = content.replace("{$LOGPATH}", slemp.getRunDir() + '/logs')
        content = content.replace("{$PANAL_ADDR}", slemp.getRunDir())
        slemp.writeFile(dst_panel_path, content)
        slemp.restartWeb()

        slemp.writeFile(cfg_domain, domain)
        return slemp.returnJson(True, 'Successfully set domain name!')

    def setPanelSslApi(self):
        sslConf = slemp.getRunDir() + '/data/ssl.pl'

        panel_tpl = slemp.getRunDir() + "/data/tpl/nginx_panel.conf"
        dst_panel_path = slemp.getServerDir() + "/web_conf/nginx/vhost/panel.conf"
        if os.path.exists(sslConf):
            os.system('rm -f ' + sslConf)

            conf = slemp.readFile(dst_panel_path)
            if conf:
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
                slemp.writeFile(dst_panel_path, conf)

            slemp.writeLog('Panel configuration', 'Panel SSL closed successfully!')
            slemp.restartWeb()
            return slemp.returnJson(True, 'SSL is closed, please use the http protocol to access the panel!')
        else:
            try:
                if not os.path.exists('ssl/input.ssl'):
                    slemp.createSSL()
                slemp.writeFile(sslConf, 'True')

                keyPath = slemp.getRunDir() + '/ssl/private.pem'
                certPath = slemp.getRunDir() + '/ssl/cert.pem'

                conf = slemp.readFile(dst_panel_path)
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
                        return slemp.returnJson(True, 'SSL opened successfully!')

                    conf = conf.replace('#error_page 404/404.html;', sslStr)

                    rep = "listen\s+([0-9]+)\s*[default_server]*;"
                    tmp = re.findall(rep, conf)
                    if not slemp.inArray(tmp, '443'):
                        listen = re.search(rep, conf).group()
                        http_ssl = "\n\tlisten 443 ssl http2;"
                        http_ssl = http_ssl + "\n\tlisten [::]:443 ssl http2;"
                        conf = conf.replace(listen, listen + http_ssl)

                    slemp.backFile(dst_panel_path)
                    slemp.writeFile(dst_panel_path, conf)
                    isError = slemp.checkWebConfig()
                    if(isError != True):
                        slemp.restoreFile(dst_panel_path)
                        return slemp.returnJson(False, 'Certificate error: <br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')
            except Exception as ex:
                return slemp.returnJson(False, 'Failed to open:' + str(ex))
            slemp.restartWeb()
            return slemp.returnJson(True, 'Open successfully, please use the https protocol to access the panel!')

    def getApi(self):
        data = {}
        return slemp.getJson(data)
    ##### ----- end ----- ###

    def getTempLoginApi(self):
        if 'tmp_login_expire' in session:
            return slemp.returnJson(False, 'Permission denied')
        limit = request.form.get('limit', '10').strip()
        p = request.form.get('p', '1').strip()
        tojs = request.form.get('tojs', '').strip()

        tempLoginM = slemp.M('temp_login')
        tempLoginM.where('state=? and expire<?',
                         (0, int(time.time()))).setField('state', -1)

        start = (int(p) - 1) * (int(limit))
        vlist = tempLoginM.limit(str(start) + ',' + str(limit)).order('id desc').field(
            'id,addtime,expire,login_time,login_addr,state').select()

        data = {}
        data['data'] = vlist

        count = tempLoginM.count()
        page_args = {}
        page_args['count'] = count
        page_args['tojs'] = 'get_temp_login'
        page_args['p'] = p
        page_args['row'] = limit

        data['page'] = slemp.getPage(page_args)
        return slemp.getJson(data)

    def removeTempLoginApi(self):
        if 'tmp_login_expire' in session:
            return slemp.returnJson(False, 'Permission denied')
        sid = request.form.get('id', '10').strip()
        if slemp.M('temp_login').where('id=?', (sid,)).delete():
            slemp.writeLog('Panel settings', 'Delete temporary login connection')
            return slemp.returnJson(True, 'Successfully deleted')
        return slemp.returnJson(False, 'Failed to delete')

    def setTempLoginApi(self):
        if 'tmp_login_expire' in session:
            return slemp.returnJson(False, 'Permission denied')
        s_time = int(time.time())
        slemp.M('temp_login').where(
            'state=? and expire>?', (0, s_time)).delete()
        token = slemp.getRandomString(48)
        salt = slemp.getRandomString(12)

        pdata = {
            'token': slemp.md5(token + salt),
            'salt': salt,
            'state': 0,
            'login_time': 0,
            'login_addr': '',
            'expire': s_time + 3600,
            'addtime': s_time
        }

        if not slemp.M('temp_login').count():
            pdata['id'] = 101

        if slemp.M('temp_login').insert(pdata):
            slemp.writeLog('Panel settings', 'Generate temporary connection, expiration time:{}'.format(
                slemp.formatDate(times=pdata['expire'])))
            return slemp.getJson({'status': True, 'msg': "A temporary connection has been created", 'token': token, 'expire': pdata['expire']})
        return slemp.returnJson(False, 'Connection generation failed')

    def getTempLoginLogsApi(self):
        if 'tmp_login_expire' in session:
            return slemp.returnJson(False, 'Permission denied')

        logs_id = request.form.get('id', '').strip()
        logs_id = int(logs_id)
        data = slemp.M('logs').where(
            'uid=?', (logs_id,)).order('id desc').field(
            'id,type,uid,log,addtime').select()
        return slemp.returnJson(False, 'ok', data)

    def checkPanelToken(self):
        api_file = self.__api_addr
        if not os.path.exists(api_file):
            return False, ''

        tmp = slemp.readFile(api_file)
        data = json.loads(tmp)
        if data['open']:
            return True, data
        else:
            return False, ''

    def setStatusCodeApi(self):
        status_code = request.form.get('status_code', '').strip()
        if re.match("^\d+$", status_code):
            status_code = int(status_code)
            if status_code != 0:
                if status_code < 100 or status_code > 999:
                    return slemp.returnJson(False, 'Status code range error!')
        else:
            return slemp.returnJson(False, 'Status code range error!')

        slemp.writeFile('data/unauthorized_status.pl', str(status_code))
        slemp.writeLog('Panel settings', 'Set the Unauthorized response status code to:{}'.format(status_code))
        return slemp.returnJson(True, 'Successfully set!')

    def getNotifyApi(self):
        data = slemp.getNotifyData(True)
        return slemp.returnData(True, 'ok', data)

    def setNotifyApi(self):
        tag = request.form.get('tag', '').strip()
        data = request.form.get('data', '').strip()

        cfg = slemp.getNotifyData(False)

        crypt_data = slemp.enDoubleCrypt(tag, data)
        if tag in cfg:
            cfg[tag]['cfg'] = crypt_data
        else:
            t = {'cfg': crypt_data}
            cfg[tag] = t

        slemp.writeNotify(cfg)
        return slemp.returnData(True, 'Successfully set')

    def setNotifyTestApi(self):
        tag = request.form.get('tag', '').strip()
        tag_data = request.form.get('data', '').strip()

        if tag == 'tgbot':
            t = json.loads(tag_data)
            test_bool = slemp.tgbotNotifyTest(t['app_token'], t['chat_id'])
            if test_bool:
                return slemp.returnData(True, 'Verification successful')
            return slemp.returnData(False, 'Verification failed')

        return slemp.returnData(False, 'This verification is not currently supported')

    def setNotifyEnableApi(self):
        tag = request.form.get('tag', '').strip()
        tag_enable = request.form.get('enable', '').strip()

        data = slemp.getNotifyData(False)
        op_enable = True
        op_action = 'Turn on'
        if tag_enable != 'true':
            op_enable = False
            op_action = 'Turn off'

        if tag in data:
            data[tag]['enable'] = op_enable

        slemp.writeNotify(data)

        return slemp.returnData(True, op_action + 'success')

    def getPanelTokenApi(self):
        api_file = self.__api_addr
        tmp = slemp.readFile(api_file)
        if not os.path.exists(api_file):
            ready_data = {"open": False, "token": "", "limit_addr": []}
            slemp.writeFile(api_file, json.dumps(ready_data))
            slemp.execShell("chmod 600 " + api_file)
            tmp = slemp.readFile(api_file)
        data = json.loads(tmp)

        if not 'key' in data:
            data['key'] = slemp.getRandomString(16)
            slemp.writeFile(api_file, json.dumps(data))

        if 'token_crypt' in data:
            data['token'] = slemp.deCrypt(data['token'], data['token_crypt'])
        else:
            token = slemp.getRandomString(32)
            data['token'] = slemp.md5(token)
            data['token_crypt'] = slemp.enCrypt(
                data['token'], token)
            slemp.writeFile(api_file, json.dumps(data))
            data['token'] = "***********************************"

        data['limit_addr'] = '\n'.join(data['limit_addr'])

        del(data['key'])
        return slemp.returnJson(True, 'ok', data)

    def setPanelTokenApi(self):
        op_type = request.form.get('op_type', '').strip()

        if op_type == '1':
            token = slemp.getRandomString(32)
            data['token'] = slemp.md5(token)
            data['token_crypt'] = slemp.enCrypt(
                data['token'], token).decode('utf-8')
            slemp.writeLog('API configuration', 'Regenerate API-Token')
            slemp.writeFile(api_file, json.dumps(data))
            return slemp.returnJson(True, 'ok', token)

        api_file = self.__api_addr
        if not os.path.exists(api_file):
            return slemp.returnJson(False, "First configure the API interface")
        else:
            tmp = slemp.readFile(api_file)
            data = json.loads(tmp)

        if op_type == '2':
            data['open'] = not data['open']
            stats = {True: 'Turn on', False: 'Turn off'}
            if not 'token_crypt' in data:
                token = slemp.getRandomString(32)
                data['token'] = slemp.md5(token)
                data['token_crypt'] = slemp.enCrypt(
                    data['token'], token).decode('utf-8')

            token = stats[data['open']] + 'success!'
            slemp.writeLog('API configuration', '%s API interface' % stats[data['open']])
            slemp.writeFile(api_file, json.dumps(data))
            return slemp.returnJson(not not data['open'], token)

        elif op_type == '3':

            limit_addr = request.form.get('limit_addr', '').strip()
            data['limit_addr'] = limit_addr.split('\n')
            slemp.writeLog('API configuration', 'Changing the IP limit is [%s]' % limit_addr)
            slemp.writeFile(api_file, json.dumps(data))
            return slemp.returnJson(True, 'Saved successfully!')

    def renderUnauthorizedStatus(self, data):
        cfg_unauth_status = 'data/unauthorized_status.pl'
        if os.path.exists(cfg_unauth_status):
            status_code = slemp.readFile(cfg_unauth_status)
            data['status_code'] = status_code
            data['status_code_msg'] = status_code
            if status_code == '0':
                data['status_code_msg'] = "Default - Security Entrance Error Prompt"
            elif status_code == '400':
                data['status_code_msg'] = "400 - Client request error"
            elif status_code == '401':
                data['status_code_msg'] = "401 - Unauthorized access"
            elif status_code == '403':
                data['status_code_msg'] = "403 - Access denied"
            elif status_code == '404':
                data['status_code_msg'] = "404 - Page does not exist"
            elif status_code == '408':
                data['status_code_msg'] = "408 - Client timeout"
            elif status_code == '416':
                data['status_code_msg'] = "416 - Invalid Request"
        else:
            data['status_code'] = '0'
            data['status_code_msg'] = "Default - Security Entrance Error Prompt"
        return data

    def get(self):

        data = {}
        data['title'] = slemp.getConfig('title')
        data['site_path'] = slemp.getWwwDir()
        data['backup_path'] = slemp.getBackupDir()
        sformat = 'date +"%Y-%m-%d %H:%M:%S %Z %z"'
        data['systemdate'] = slemp.execShell(sformat)[0].strip()

        data['port'] = slemp.getHostPort()
        data['ip'] = slemp.getHostAddr()

        admin_path_file = 'data/admin_path.pl'
        if not os.path.exists(admin_path_file):
            data['admin_path'] = '/'
        else:
            data['admin_path'] = slemp.readFile(admin_path_file)

        ipv6_file = 'data/ipv6.pl'
        if os.path.exists(ipv6_file):
            data['ipv6'] = 'checked'
        else:
            data['ipv6'] = ''

        debug_file = 'data/debug.pl'
        if os.path.exists(debug_file):
            data['debug'] = 'checked'
        else:
            data['debug'] = ''

        ssl_file = 'data/ssl.pl'
        if os.path.exists('data/ssl.pl'):
            data['ssl'] = 'checked'
        else:
            data['ssl'] = ''

        basic_auth = 'data/basic_auth.json'
        if os.path.exists(basic_auth):
            bac = slemp.readFile(basic_auth)
            bac = json.loads(bac)
            if bac['open']:
                data['basic_auth'] = 'checked'
        else:
            data['basic_auth'] = ''

        cfg_domain = 'data/bind_domain.pl'
        if os.path.exists(cfg_domain):
            domain = slemp.readFile(cfg_domain)
            data['bind_domain'] = domain.strip()
        else:
            data['bind_domain'] = ''

        data = self.renderUnauthorizedStatus(data)

        api_token = self.__api_addr
        if os.path.exists(api_token):
            bac = slemp.readFile(api_token)
            bac = json.loads(bac)
            if bac['open']:
                data['api_token'] = 'checked'
        else:
            data['api_token'] = ''

        data['site_count'] = slemp.M('sites').count()

        data['username'] = slemp.M('users').where(
            "id=?", (1,)).getField('username')

        data['hook_tag'] = request.args.get('tag', '')

        database_hook_file = 'data/hook_database.json'
        if os.path.exists(database_hook_file):
            df = slemp.readFile(database_hook_file)
            df = json.loads(df)
            data['hook_database'] = df
        else:
            data['hook_database'] = []

        menu_hook_file = 'data/hook_menu.json'
        if os.path.exists(menu_hook_file):
            df = slemp.readFile(menu_hook_file)
            df = json.loads(df)
            data['hook_menu'] = df
        else:
            data['hook_menu'] = []

        # global_static hook
        global_static_hook_file = 'data/hook_global_static.json'
        if os.path.exists(global_static_hook_file):
            df = slemp.readFile(global_static_hook_file)
            df = json.loads(df)
            data['hook_global_static'] = df
        else:
            data['hook_global_static'] = []

        # notiy config
        notify_data = slemp.getNotifyData(True)
        notify_tag_list = ['tgbot', 'email']
        for tag in notify_tag_list:
            new_tag = 'notify_' + tag + '_enable'
            data[new_tag] = ''
            if tag in notify_data and 'enable' in notify_data[tag]:
                if notify_data[tag]['enable']:
                    data[new_tag] = 'checked'

        return data
