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
    __isIptables = False
    __isUfw = False
    __isMac = False

    def __init__(self):
        iptables_file = slemp.systemdCfgDir() + '/iptables.service'
        if os.path.exists('/usr/sbin/firewalld'):
            self.__isFirewalld = True
        elif os.path.exists('/usr/sbin/ufw'):
            self.__isUfw = True
        elif os.path.exists(iptables_file):
            self.__isIptables = True
        elif slemp.isAppleSystem():
            self.__isMac = True

    ##### ----- start ----- ###
    def addDropAddressApi(self):
        import re
        port = request.form.get('port', '').strip()
        ps = request.form.get('ps', '').strip()

        rep = "^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\/\d{1,2})?$"
        if not re.search(rep, port):
            return slemp.returnJson(False, 'The IP address you entered is invalid!')
        address = port
        if slemp.M('firewall').where("port=?", (address,)).count() > 0:
            return slemp.returnJson(False, 'The IP you want to block already exists in the block list, so there is no need to repeat it!')
        if self.__isUfw:
            slemp.execShell('ufw deny from ' + address + ' to any')
        else:
            if self.__isIptables:
                cmd = 'iptables -I INPUT -s ' + address + ' -j DROP'
                slemp.execShell(cmd)
            elif self.__isFirewalld:
                cmd = 'firewall-cmd --permanent --add-rich-rule=\'rule family=ipv4 source address="' + \
                    address + '" drop\''
                slemp.execShell(cmd)
            else:
                pass

        msg = slemp.getInfo('Block IP [{1}] successfully!', (address,))
        slemp.writeLog("Firewall management", msg)
        addtime = time.strftime('%Y-%m-%d %X', time.localtime())
        slemp.M('firewall').add('port,ps,addtime', (address, ps, addtime))
        self.firewallReload()
        return slemp.returnJson(True, 'Added successfully!')

    def addAcceptPortApi(self):
        if not self.getFwStatus():
            return slemp.returnJson(False, 'Rules can only be added when the firewall is started!')

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
            return slemp.returnData(False, 'Incorrect port range!')

        if slemp.M('firewall').where("port=?", (port,)).count() > 0:
            return slemp.returnData(False, 'The port you want to allow already exists, so there is no need to allow it again!')

        msg = slemp.getInfo('Successfully released port [{1}]', (port,))
        slemp.writeLog("Firewall management", msg)
        addtime = time.strftime('%Y-%m-%d %X', time.localtime())
        slemp.M('firewall').add('port,ps,addtime', (port, ps, addtime))

        self.addAcceptPort(port)
        self.firewallReload()
        return slemp.returnData(True, 'Add release (' + port + ') port successfully!')

    def delDropAddressApi(self):
        if not self.getFwStatus():
            return slemp.returnJson(False, 'Rules can only be deleted when the firewall is started!')

        port = request.form.get('port', '').strip()
        ps = request.form.get('ps', '').strip()
        sid = request.form.get('id', '').strip()
        address = port
        if self.__isUfw:
            slemp.execShell('ufw delete deny from ' + address + ' to any')
        elif self.__isFirewalld:
            slemp.execShell(
                'firewall-cmd --permanent --remove-rich-rule=\'rule family=ipv4 source address="' + address + '" drop\'')
        else:
            pass

        msg = slemp.getInfo('Unblock IP[{1}]!', (address,))
        slemp.writeLog("Firewall management", msg)
        slemp.M('firewall').where("id=?", (sid,)).delete()

        self.firewallReload()
        return slemp.returnJson(True, 'Successfully deleted!')

    def delAcceptPortApi(self):
        port = request.form.get('port', '').strip()
        sid = request.form.get('id', '').strip()
        slemp_port = slemp.readFile('data/port.pl')
        try:
            if(port == slemp_port):
                return slemp.returnJson(False, 'Failed, cannot delete current panel port!')
            if self.__isUfw:
                slemp.execShell('ufw delete allow ' + port + '/tcp')
            elif self.__isFirewalld:
                port = port.replace(':', '-')
                slemp.execShell(
                    'firewall-cmd --permanent --zone=public --remove-port=' + port + '/tcp')
                slemp.execShell(
                    'firewall-cmd --permanent --zone=public --remove-port=' + port + '/udp')
            elif self.__isIptables:
                slemp.execShell(
                    'iptables -D INPUT -p tcp -m state --state NEW -m tcp --dport ' + port + ' -j ACCEPT')
            else:
                pass
            msg = slemp.getInfo('Deleting the firewall port [{1}] succeeded!', (port,))
            slemp.writeLog("Firewall management", msg)
            slemp.M('firewall').where("id=?", (sid,)).delete()

            self.firewallReload()
            return slemp.returnJson(True, 'Successfully deleted!')
        except Exception as e:
            return slemp.returnJson(False, 'Failed to delete!:' + str(e))

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
        data = {}

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
                sys_conf = slemp.readFile(file)
                rep = "#*net\.ipv4\.icmp_echo_ignore_all\s*=\s*([0-9]+)"
                tmp = re.search(rep, sys_conf).groups(0)[0]
                if tmp == '1':
                    isPing = False
        except:
            isPing = True

        status = True
        cmd = "service sshd status | grep -P '(dead|stop)'|grep -v grep"
        ssh_status = slemp.execShell(cmd)
        if ssh_status[0] != '':
            status = False

        cmd = "systemctl status sshd.service | grep 'dead'|grep -v grep"
        ssh_status = slemp.execShell(cmd)
        if ssh_status[0] != '':
            status = False

        data['pass_prohibit_status'] = False
        pass_rep = "#PasswordAuthentication\s+(\w*)\s*\n"
        pass_status = re.search(pass_rep, conf)
        if pass_status:
            data['pass_prohibit_status'] = True

        if not data['pass_prohibit_status']:
            pass_rep = "PasswordAuthentication\s+(\w*)\s*\n"
            pass_status = re.search(pass_rep, conf)
            if pass_status and pass_status.groups(0)[0].strip() == 'no':
                data['pass_prohibit_status'] = True

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
            return slemp.returnJson(False, 'The port range must be between 22-65535!')

        ports = ['21', '25', '80', '443', '888']
        if port in ports:
            return slemp.returnJson(False, '(' + port + ')' + ' special port cannot be set!')

        file = '/etc/ssh/sshd_config'
        conf = slemp.readFile(file)

        rep = "#*Port\s+([0-9]+)\s*\n"
        conf = re.sub(rep, "Port " + port + "\n", conf)
        slemp.writeFile(file, conf)

        self.addAcceptPortArgs(port, 'SSH port modification', 'port')
        if self.__isUfw:
            slemp.execShell("service ssh restart")
        elif self.__isIptables:
            slemp.execShell("/etc/init.d/sshd restart")
        elif self.__isFirewalld:
            slemp.execShell("systemctl restart sshd.service")
        else:
            return slemp.returnJson(False, 'Fail to edit!')
        return slemp.returnJson(True, 'Successfully modified!')

    def setSshStatusApi(self):
        if slemp.isAppleSystem():
            return slemp.returnJson(True, 'The development machine cannot operate!')

        status = request.form.get('status', '1').strip()
        msg = 'SSH service is enabled'
        act = 'start'
        if status == "1":
            msg = 'SSH service is disabled'
            act = 'stop'

        ssh_service = slemp.systemdCfgDir() + '/sshd.service'
        if os.path.exists(ssh_service):
            slemp.execShell("systemctl " + act + " sshd.service")
        else:
            slemp.execShell('service sshd ' + act)

        if os.path.exists('/etc/init.d/sshd'):
            slemp.execShell('/etc/init.d/sshd ' + act)

        slemp.writeLog("Firewall management", msg)
        return slemp.returnJson(True, 'Successful operation!')

    def setSshPassStatusApi(self):
        if slemp.isAppleSystem():
            return slemp.returnJson(True, 'The development machine cannot operate!')

        status = request.form.get('status', '1').strip()
        msg = 'Prohibition of password login success'
        if status == "1":
            msg = 'Open the password and log in successfully'

        file = '/etc/ssh/sshd_config'
        if not os.path.exists(file):
            return slemp.returnJson(False, 'Cannot be set!')

        conf = slemp.readFile(file)

        if status == '1':
            rep = "(#)?PasswordAuthentication\s+(\w*)\s*\n"
            conf = re.sub(rep, "PasswordAuthentication yes\n", conf)
        else:
            rep = "(#)?PasswordAuthentication\s+(\w*)\s*\n"
            conf = re.sub(rep, "PasswordAuthentication no\n", conf)
        slemp.writeFile(file, conf)
        slemp.execShell("systemctl restart sshd.service")
        slemp.writeLog("SSH management", msg)
        return slemp.returnJson(True, msg)

    def setPingApi(self):
        if slemp.isAppleSystem():
            return slemp.returnJson(True, 'The development machine cannot operate!')

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
        return slemp.returnJson(True, 'Successfully set!')

    def setFwApi(self):
        if slemp.isAppleSystem():
            return slemp.returnJson(True, 'The development machine cannot be set!')

        status = request.form.get('status', '1')
        return slemp.getJson(self.setFw(status))

    def setFwIptables(self, status):
        if status == '1':
            slemp.execShell('service iptables save')
            slemp.execShell('service iptables stop')
        else:
            _list = slemp.M('firewall').field('id,port,ps,addtime').limit(
                '0,1000').order('id desc').select()

            slemp.execShell('iptables -P INPUT DROP')
            slemp.execShell('iptables -P OUTPUT ACCEPT')
            for x in _list:
                port = x['port']
                if slemp.isIpAddr(port):
                    cmd = 'iptables -I INPUT -s ' + port + ' -j DROP'
                    slemp.execShell(cmd)
                else:
                    self.addAcceptPort(port)

            slemp.execShell('service iptables save')
            slemp.execShell('service iptables start')

    def setFw(self, status):

        if self.__isIptables:
            self.setFwIptables(status)
            return slemp.returnData(True, 'Successfully set!')

        if status == '1':
            if self.__isUfw:
                slemp.execShell('/usr/sbin/ufw disable')

            elif self.__isFirewalld:
                slemp.execShell('systemctl stop firewalld.service')
                slemp.execShell('systemctl disable firewalld.service')
            else:
                pass
        else:
            if self.__isUfw:
                slemp.execShell("echo 'y'| ufw enable")
            elif self.__isFirewalld:
                slemp.execShell('systemctl start firewalld.service')
                slemp.execShell('systemctl enable firewalld.service')
            else:
                pass

        return slemp.returnData(True, 'Successfully set!')

    def delPanelLogsApi(self):
        slemp.M('logs').where('id>?', (0,)).delete()
        slemp.writeLog('Panel settings', 'Panel operation log has been cleared!')
        return slemp.returnJson(True, 'Panel operation log has been cleared!')

    ##### ----- start ----- ###

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
        elif self.__isIptables:
            cmd = 'iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport ' + port + ' -j ACCEPT'
            slemp.execShell(cmd)
        else:
            pass
        return True

    def firewallReload(self):
        if self.__isUfw:
            slemp.execShell('/usr/sbin/ufw reload')
            return
        elif self.__isIptables:
            slemp.execShell('service iptables save')
            slemp.execShell('service iptables restart')
        elif self.__isFirewalld:
            slemp.execShell('firewall-cmd --reload')
        else:
            pass

    def getFwStatus(self):
        if self.__isUfw:
            cmd = "/usr/sbin/ufw status| grep Status | awk -F ':' '{print $2}'"
            data = slemp.execShell(cmd)
            if data[0].strip() == 'inactive':
                return False
            return True
        elif self.__isIptables:
            cmd = "systemctl status iptables | grep 'inactive'"
            data = slemp.execShell(cmd)
            if data[0] != '':
                return False
            return True
        elif self.__isFirewalld:
            cmd = "ps -ef|grep firewalld |grep -v grep | awk '{print $2}'"
            data = slemp.execShell(cmd)
            if data[0] == '':
                return False
            return True
        else:
            return False
