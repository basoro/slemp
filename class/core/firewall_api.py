# coding: utf-8

import psutil
import time
import os
import sys
import slemp
import re
import json
import pwd

from flask import request


class firewall_api:

    __isFirewalld = False
    __isUfw = False
    __isMac = False

    def __init__(self):
        if os.path.exists('/usr/sbin/firewalld'):
            self.__isFirewalld = True
        if os.path.exists('/usr/sbin/ufw'):
            self.__isUfw = True
        if slemp.isAppleSystem():
            self.__isMac = True

    def addDropAddressApi(self):
        import re
        port = request.form.get('port', '').strip()
        ps = request.form.get('ps', '').strip()

        rep = "^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\/\d{1,2})?$"
        if not re.search(rep, port):
            return slemp.returnJson(False, 'Alamat IP yang anda masukkan tidak valid!')
        address = port
        if slemp.M('firewall').where("port=?", (address,)).count() > 0:
            return slemp.returnJson(False, 'IP yang ingin anda blokir sudah ada di daftar blokir, tidak perlu mengulangi prosesnya!')
        if self.__isUfw:
            slemp.execShell('ufw deny from ' + address + ' to any')
        else:
            if self.__isFirewalld:
                cmd = 'firewall-cmd --permanent --add-rich-rule=\'rule family=ipv4 source address="' + \
                    address + '" drop\''
                slemp.execShell(cmd)
            else:
                cmd = 'iptables -I INPUT -s ' + address + ' -j DROP'
                slemp.execShell(cmd)

        msg = slemp.getInfo('Blokir IP [{1}] berhasil!', (address,))
        slemp.writeLog("Manajemen Firewall", msg)
        addtime = time.strftime('%Y-%m-%d %X', time.localtime())
        slemp.M('firewall').add('port,ps,addtime', (address, ps, addtime))
        self.firewallReload()
        return slemp.returnJson(True, 'Berhasil ditambahkan!')

    def addAcceptPortApi(self):

        if not self.getFwStatus():
            return slemp.returnJson(False, 'Aturan hanya dapat ditambahkan ketika firewall diaktifkan!')

        port = request.form.get('port', '').strip()
        ps = request.form.get('ps', '').strip()
        stype = request.form.get('type', '').strip()

        data = self.addAcceptPortArgs(port, ps, stype)
        return slemp.getJson(data)

    def addAcceptPortArgs(self, port, ps, stype):
        import re
        import time

        if not self.getFwStatus():
            self.setFw(0)

        rep = "^\d{1,5}(:\d{1,5})?$"
        if not re.search(rep, port):
            return slemp.returnData(False, 'Rentang port salah!')

        if slemp.M('firewall').where("port=?", (port,)).count() > 0:
            return slemp.returnData(False, 'Port yang ingin anda buka sudah ada, tidak perlu dibuka lagi!')

        msg = slemp.getInfo('Port [{1}] berhasil dibuka', (port,))
        slemp.writeLog("Manajemen Firewall", msg)
        addtime = time.strftime('%Y-%m-%d %X', time.localtime())
        slemp.M('firewall').add('port,ps,addtime', (port, ps, addtime))

        self.addAcceptPort(port)
        self.firewallReload()
        return slemp.returnData(True, 'Tambahkan port (' + port + ') untuk dibuka berhasil!')

    def delDropAddressApi(self):
        if not self.getFwStatus():
            return slemp.returnJson(False, 'Aturan hanya dapat dihapus ketika firewall diaktifkan!')

        port = request.form.get('port', '').strip()
        ps = request.form.get('ps', '').strip()
        sid = request.form.get('id', '').strip()
        address = port
        if self.__isUfw:
            slemp.execShell('ufw delete deny from ' + address + ' to any')
        else:
            if self.__isFirewalld:
                slemp.execShell(
                    'firewall-cmd --permanent --remove-rich-rule=\'rule family=ipv4 source address="' + address + '" drop\'')
            elif self.__isMac:
                pass
            else:
                cmd = 'iptables -D INPUT -s ' + address + ' -j DROP'
                slemp.execShell(cmd)

        msg = slemp.getInfo('Buka blokir IP [{1}]!', (address,))
        slemp.writeLog("Manajemen Firewall", msg)
        slemp.M('firewall').where("id=?", (sid,)).delete()

        self.firewallReload()
        return slemp.returnJson(True, 'Berhasil dihapus!')

    def delAcceptPortApi(self):
        port = request.form.get('port', '').strip()
        sid = request.form.get('id', '').strip()
        slemp_port = slemp.readFile('data/port.pl')
        try:
            if(port == slemp_port):
                return slemp.returnJson(False, 'Gagal, tidak dapat menghapus port panel saat ini!')
            if self.__isUfw:
                slemp.execShell('ufw delete allow ' + port + '/tcp')
            else:
                if self.__isFirewalld:
                    slemp.execShell(
                        'firewall-cmd --permanent --zone=public --remove-port=' + port + '/tcp')
                    slemp.execShell(
                        'firewall-cmd --permanent --zone=public --remove-port=' + port + '/udp')
                else:
                    slemp.execShell(
                        'iptables -D INPUT -p tcp -m state --state NEW -m tcp --dport ' + port + ' -j ACCEPT')
            msg = slemp.getInfo('Penghapusan port [{1}] yang diizinkan firewall berhasil!', (port,))
            slemp.writeLog("Manajemen Firewall", msg)
            slemp.M('firewall').where("id=?", (sid,)).delete()

            self.firewallReload()
            return slemp.returnJson(True, 'Berhasil dihapus!')
        except Exception as e:
            return slemp.returnJson(False, 'Gagal menghapus!:' + str(e))

    def getWwwPathApi(self):
        path = slemp.getLogsDir()
        return slemp.getJson({'path': path})

    def getListApi(self):
        p = request.form.get('p', '1').strip()
        limit = request.form.get('limit', '10').strip()
        return self.getList(int(p), int(limit))

    def getLogListApi(self):
        p = request.form.get('p', '1').strip()
        limit = request.form.get('limit', '10').strip()
        search = request.form.get('search', '').strip()
        return self.getLogList(int(p), int(limit), search)

    def getSshInfoApi(self):
        file = '/etc/ssh/sshd_config'
        conf = slemp.readFile(file)
        rep = "#*Port\s+([0-9]+)\s*\n"
        port = re.search(rep, conf).groups(0)[0]

        isPing = True
        try:
            if slemp.isAppleSystem():
                isPing = True
            else:
                file = '/etc/sysctl.conf'
                conf = slemp.readFile(file)
                rep = "#*net\.ipv4\.icmp_echo_ignore_all\s*=\s*([0-9]+)"
                tmp = re.search(rep, conf).groups(0)[0]
                if tmp == '1':
                    isPing = False
        except:
            isPing = True

        import system_api
        panelsys = system_api.system_api()
        version = panelsys.getSystemVersion()
        if os.path.exists('/usr/bin/apt-get'):
            if os.path.exists('/etc/init.d/sshd'):
                cmd = "service sshd status | grep -P '(dead|stop)'|grep -v grep"
                status = slemp.execShell(cmd)
            else:
                cmd = "service ssh status | grep -P '(dead|stop)'|grep -v grep"
                status = slemp.execShell(cmd)
        else:
            if version.find(' 7.') != -1:
                cmd = "systemctl status sshd.service | grep 'dead'|grep -v grep"
                status = slemp.execShell(cmd)
            else:
                cmd = "/etc/init.d/sshd status | grep -e 'stopped' -e '已停'|grep -v grep"
                status = slemp.execShell(cmd)
        if len(status[0]) > 3:
            status = False
        else:
            status = True

        data = {}
        data['port'] = port

        data['status'] = status
        data['ping'] = isPing
        if slemp.isAppleSystem():
            data['firewall_status'] = False
        else:
            data['firewall_status'] = self.getFwStatus()
        return slemp.getJson(data)

    def setSshPortApi(self):
        port = request.form.get('port', '1').strip()
        if int(port) < 22 or int(port) > 65535:
            return slemp.returnJson(False, 'Rentang port harus antara 22-65535!')

        ports = ['21', '25', '80', '443', '7200', '8080', '888', '8888']
        if port in ports:
            return slemp.returnJson(False, '(' + port + ')' + 'Port khusus tidak dapat disetel!')

        file = '/etc/ssh/sshd_config'
        conf = slemp.readFile(file)

        rep = "#*Port\s+([0-9]+)\s*\n"
        conf = re.sub(rep, "Port " + port + "\n", conf)
        slemp.writeFile(file, conf)

        if self.__isFirewalld:
            slemp.execShell('setenforce 0')
            slemp.execShell(
                'sed -i "s#SELINUX=enforcing#SELINUX=disabled#" /etc/selinux/config')
            slemp.execShell("systemctl restart sshd.service")
        elif self.__isUfw:
            slemp.execShell('ufw allow ' + port + '/tcp')
            slemp.execShell("service ssh restart")
        else:
            slemp.execShell(
                'iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport ' + port + ' -j ACCEPT')
            slemp.execShell("/etc/init.d/sshd restart")

        self.firewallReload()
        msg = slemp.getInfo('Ubah port SSH ke [{1}] berhasil!', port)
        slemp.writeLog("Manajemen Firewall", msg)
        return slemp.returnJson(True, 'Berhasil diubah!')

    def setSshStatusApi(self):
        if slemp.isAppleSystem():
            return slemp.returnJson(True, 'Tidak support untuk MacOS!')

        status = request.form.get('status', '1').strip()
        version = slemp.readFile('/etc/redhat-release')
        if int(status) == 1:
            msg = 'Layanan SSH dinonaktifkan'
            act = 'stop'
        else:
            msg = 'Layanan SSH diaktifkan'
            act = 'start'

        if not os.path.exists('/etc/redhat-release'):
            slemp.execShell('service ssh ' + act)
        elif version.find(' 7.') != -1:
            slemp.execShell("systemctl " + act + " sshd.service")
        else:
            slemp.execShell("/etc/init.d/sshd " + act)

        slemp.writeLog("Manajemen Firewall", msg)
        return slemp.returnJson(True, 'Sukses!')

    def setPingApi(self):
        if slemp.isAppleSystem():
            return slemp.returnJson(True, 'Tidak support untuk MacOS!')

        status = request.form.get('status')
        filename = '/etc/sysctl.conf'
        conf = slemp.readFile(filename)
        if conf.find('net.ipv4.icmp_echo') != -1:
            rep = u"net\.ipv4\.icmp_echo.*"
            conf = re.sub(rep, 'net.ipv4.icmp_echo_ignore_all=' + status, conf)
        else:
            conf += "\nnet.ipv4.icmp_echo_ignore_all=" + status

        slemp.writeFile(filename, conf)
        slemp.execShell('sysctl -p')
        return slemp.returnJson(True, 'Pengaturan berhasil!')

    def setFwApi(self):
        if slemp.isAppleSystem():
            return slemp.returnJson(True, 'Tidak support untuk MacOS!')

        status = request.form.get('status', '1')
        return slemp.getJson(self.setFw(status))

    def setFw(self, status):
        if status == '1':
            if self.__isUfw:
                slemp.execShell('/usr/sbin/ufw disable')
            if self.__isFirewalld:
                slemp.execShell('systemctl stop firewalld.service')
                slemp.execShell('systemctl disable firewalld.service')
            elif self.__isMac:
                pass
            else:
                slemp.execShell('/etc/init.d/iptables save')
                slemp.execShell('/etc/init.d/iptables stop')
        else:
            if self.__isUfw:
                slemp.execShell("echo 'y'|sudo ufw enable")
            if self.__isFirewalld:
                slemp.execShell('systemctl start firewalld.service')
                slemp.execShell('systemctl enable firewalld.service')
            elif self.__isMac:
                pass
            else:
                slemp.execShell('/etc/init.d/iptables save')
                slemp.execShell('/etc/init.d/iptables restart')

        return slemp.returnData(True, 'Set successfully!')

    def delPanelLogsApi(self):
        slemp.M('logs').where('id>?', (0,)).delete()
        slemp.writeLog('Pengaturan panel', 'Log panel telah dihapus!')
        return slemp.returnJson(True, 'Log panel telah dihapus!')

    def getList(self, page, limit):

        start = (page - 1) * limit

        _list = slemp.M('firewall').field('id,port,ps,addtime').limit(
            str(start) + ',' + str(limit)).order('id desc').select()
        data = {}
        data['data'] = _list

        count = slemp.M('firewall').count()
        _page = {}
        _page['count'] = count
        _page['tojs'] = 'showAccept'
        _page['p'] = page

        data['page'] = slemp.getPage(_page)
        return slemp.getJson(data)

    def getLogList(self, page, limit, search=''):
        find_search = ''
        if search != '':
            find_search = "type like '%" + search + "%' or log like '%" + \
                search + "%' or addtime like '%" + search + "%'"

        start = (page - 1) * limit

        _list = slemp.M('logs').where(find_search, ()).field(
            'id,type,log,addtime').limit(str(start) + ',' + str(limit)).order('id desc').select()
        data = {}
        data['data'] = _list

        count = slemp.M('logs').where(find_search, ()).count()
        _page = {}
        _page['count'] = count
        _page['tojs'] = 'getLogs'
        _page['p'] = page

        data['page'] = slemp.getPage(_page)
        return slemp.getJson(data)

    def addAcceptPort(self, port):
        if self.__isUfw:
            slemp.execShell('ufw allow ' + port + '/tcp')
        elif self.__isFirewalld:
            port = port.replace(':', '-')
            cmd = 'firewall-cmd --permanent --zone=public --add-port=' + port + '/tcp'
            slemp.execShell(cmd)
        elif self.__isMac:
            pass
        else:
            cmd = 'iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport ' + port + ' -j ACCEPT'
            slemp.execShell(cmd)

    def firewallReload(self):
        if self.__isUfw:
            slemp.execShell('/usr/sbin/ufw reload')
            return
        if self.__isFirewalld:
            slemp.execShell('firewall-cmd --reload')
        elif self.__isMac:
            pass
        else:
            slemp.execShell('/etc/init.d/iptables save')
            slemp.execShell('/etc/init.d/iptables restart')

    def getFwStatus(self):
        if self.__isUfw:
            cmd = "/usr/sbin/ufw status| grep Status | awk -F ':' '{print $2}'"
            data = slemp.execShell(cmd)
            if data[0].strip() == 'inactive':
                return False
            return True
        if self.__isFirewalld:
            cmd = "ps -ef|grep firewalld |grep -v grep | awk '{print $2}'"
            data = slemp.execShell(cmd)
            if data[0] == '':
                return False
            return True
        elif self.__isMac:
            return False
        else:
            cmd = "ps -ef|grep iptables |grep -v grep  | awk '{print $2}'"
            data = slemp.execShell(cmd)
            if data[0] == '':
                return False
            return True
