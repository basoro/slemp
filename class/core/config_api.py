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

    __version = '3.1'

    def __init__(self):
        pass

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

            if os.path.exists("/lib/systemd/system/firewalld.service"):
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
        return slemp.returnJson(True, 'Berhasil disimpan!', info)

    def setAdminPathApi(self):
        admin_path = request.form.get('admin_path', '').strip()
        admin_path_checks = ['/', '/close', '/login', '/do_login', '/site',
                             '/sites', '/download_file', '/control', '/crontab',
                             '/firewall', '/files', 'config', '/soft', '/system',
                             '/code', '/ssl', '/plugins']
        if admin_path == '':
            admin_path = '/'
        if admin_path != '/':
            if len(admin_path) < 6:
                return slemp.returnJson(False, 'Panjang alamat login tidak boleh kurang dari 6 karakter!')
            if admin_path in admin_path_checks:
                return slemp.returnJson(False, 'Path login sudah digunakan oleh panel, silakan gunakan alamat login yang lain!')
            if not re.match("^/[\w\./-_]+$", admin_path):
                return slemp.returnJson(False, 'Format alamat login salah, contoh: /my_panel')
        else:
            domain = slemp.readFile('data/domain.conf')
            if not domain:
                domain = ''
            limitip = slemp.readFile('data/limitip.conf')
            if not limitip:
                limitip = ''
            if not domain.strip() and not limitip.strip():
                return slemp.returnJson(False, 'Peringatan, menutup login keamanan sama dengan mengekspos alamat latar belakang Anda secara langsung ke jaringan eksternal, yang sangat berbahaya. Setidaknya salah satu dari metode keamanan berikut dapat dimatikan: <a style="color:red;"><br>1. Gunakan nama domain<br>2. Gunakan alamat IP</a>')

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
        cert = {}
        cert['privateKey'] = slemp.readFile('ssl/privateKey.pem')
        cert['certPem'] = slemp.readFile('ssl/certificate.pem')
        cert['rep'] = os.path.exists('ssl/input.pl')
        return slemp.getJson(cert)

    def savePanelSslApi(self):
        keyPath = 'ssl/privateKey.pem'
        certPath = 'ssl/certificate.pem'
        checkCert = '/tmp/cert.pl'

        certPem = request.form.get('certPem', '').strip()
        privateKey = request.form.get('privateKey', '').strip()

        slemp.writeFile(checkCert, certPem)
        if privateKey:
            slemp.writeFile(keyPath, privateKey)
        if certPem:
            slemp.writeFile(certPath, certPem)
        if not slemp.checkCert(checkCert):
            return slemp.returnJson(False, 'Kesalahan sertifikat keamanan, harap periksa kembali!')
        slemp.writeFile('ssl/input.pl', 'True')
        return slemp.returnJson(True, 'Sertifikat disimpan!')

    def setPanelSslApi(self):
        sslConf = slemp.getRunDir() + '/data/ssl.pl'
        if os.path.exists(sslConf):
            os.system('rm -f ' + sslConf)
            return slemp.returnJson(True, 'SSL tidak aktif, silakan gunakan protokol http untuk mengakses panel!')
        else:
            os.system('pip install cffi==1.10')
            os.system('pip install cryptography==2.1')
            os.system('pip install pyOpenSSL==16.2')
            try:
                if not self.createSSL():
                    return slemp.returnJson(False, 'Gagal membuka, tidak dapat menginstal komponen pyOpenSSL secara otomatis!<p>Silakan coba instal secara manual: pip install pyOpenSSL</p>')
                slemp.writeFile(sslConf, 'True')
            except Exception as ex:
                return slemp.returnJson(False, 'Gagal membuka, tidak dapat menginstal komponen pyOpenSSL secara otomatis!<p>Silakan coba instal secara manual: pip install pyOpenSSL</p>')
            return slemp.returnJson(True, 'Sukses, silakan gunakan protokol https untuk mengakses panel!')

    def getApi(self):
        data = {}
        return slemp.getJson(data)

    def createSSL(self):
        if os.path.exists('ssl/input.pl'):
            return True
        import OpenSSL
        key = OpenSSL.crypto.PKey()
        key.generate_key(OpenSSL.crypto.TYPE_RSA, 2048)
        cert = OpenSSL.crypto.X509()
        cert.set_serial_number(0)
        cert.get_subject().CN = slemp.getLocalIp()
        cert.set_issuer(cert.get_subject())
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(86400 * 3650)
        cert.set_pubkey(key)
        cert.sign(key, 'md5')
        cert_ca = OpenSSL.crypto.dump_certificate(
            OpenSSL.crypto.FILETYPE_PEM, cert)
        private_key = OpenSSL.crypto.dump_privatekey(
            OpenSSL.crypto.FILETYPE_PEM, key)
        if len(cert_ca) > 100 and len(private_key) > 100:
            slemp.writeFile('ssl/certificate.pem', cert_ca)
            slemp.writeFile('ssl/privateKey.pem', private_key)
            print(cert_ca, private_key)
            return True
        return False

    def getVersion(self):
        return self.__version

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

        data['site_count'] = slemp.M('sites').count()

        data['username'] = slemp.M('users').where(
            "id=?", (1,)).getField('username')

        return data
