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


class crontab_api:

    field = 'id,name,type,where1,where_hour,where_minute,echo,addtime,status,save,backup_to,stype,sname,sbody,urladdress'

    def __init__(self):
        pass

    def listApi(self):
        p = request.args.get('p', 1)
        psize = 10

        startPage = (int(p) - 1) * psize
        pageInfo = str(startPage) + ',' + str(psize)

        _list = slemp.M('crontab').where('', ()).field(
            self.field).limit(pageInfo).order('id desc').select()

        data = []
        for i in range(len(_list)):
            tmp = _list[i]
            if _list[i]['type'] == "day":
                tmp['type'] = 'Setiap Hari'
                tmp['cycle'] = slemp.getInfo('Setiap hari, pada {1}:{2}', (str(
                    _list[i]['where_hour']), str(_list[i]['where_minute'])))
            elif _list[i]['type'] == "day-n":
                tmp['type'] = slemp.getInfo(
                    'Setiap {1} hari', (str(_list[i]['where1']),))
                tmp['cycle'] = slemp.getInfo('Setiap {1} hari, pada {2}:{3} menit',  (str(
                    _list[i]['where1']), str(_list[i]['where_hour']), str(_list[i]['where_minute'])))
            elif _list[i]['type'] == "hour":
                tmp['type'] = 'Setiap Jam'
                tmp['cycle'] = slemp.getInfo(
                    'Setiap jam, {1} menit dijalankan', (str(_list[i]['where_minute']),))
            elif _list[i]['type'] == "hour-n":
                tmp['type'] = slemp.getInfo(
                    'Setiap {1} jam', (str(_list[i]['where1']),))
                tmp['cycle'] = slemp.getInfo('Setiap {1} jam, {2} menit', (str(
                    _list[i]['where1']), str(_list[i]['where_minute'])))
            elif _list[i]['type'] == "minute-n":
                tmp['type'] = slemp.getInfo(
                    'Setiap {1} menit', (str(_list[i]['where1']),))
                tmp['cycle'] = slemp.getInfo(
                    'Jalankan setiap {1} menit', (str(_list[i]['where1']),))
            elif _list[i]['type'] == "week":
                tmp['type'] = 'Setiap Minggu'
                if not _list[i]['where1']:
                    _list[i]['where1'] = '0'
                tmp['cycle'] = slemp.getInfo('Setiap minggu pada {1}, {2}:{3}', (self.toWeek(int(
                    _list[i]['where1'])), str(_list[i]['where_hour']), str(_list[i]['where_minute'])))
            elif _list[i]['type'] == "month":
                tmp['type'] = 'Setiap Bulan'
                tmp['cycle'] = slemp.getInfo('Setiap bulan, {1} hari {2}:{3}', (str(_list[i]['where1']), str(
                    _list[i]['where_hour']), str(_list[i]['where_minute'])))
            data.append(tmp)

        _ret = {}
        _ret['data'] = data

        count = slemp.M('crontab').where('', ()).count()
        _page = {}
        _page['count'] = count
        _page['p'] = p
        _page['row'] = psize
        _page['tojs'] = "getCronData"

        _ret['list'] = slemp.getPage(_page)
        _ret['p'] = p
        return slemp.getJson(_ret)

    def setCronStatusApi(self):
        mid = request.form.get('id', '')
        cronInfo = slemp.M('crontab').where(
            'id=?', (mid,)).field(self.field).find()
        status = 1
        if cronInfo['status'] == status:
            status = 0
            self.removeForCrond(cronInfo['echo'])
        else:
            cronInfo['status'] = 1
            self.syncToCrond(cronInfo)

        slemp.M('crontab').where('id=?', (mid,)).setField('status', status)
        slemp.writeLog(
            'Penjadwalan', 'Ubah status penjadwalan [' + cronInfo['name'] + '] menjadi [' + str(status) + ']')
        return slemp.returnJson(True, 'Pengaturan berhasil')

    def getCrondFindApi(self):
        sid = request.form.get('id', '')
        data = slemp.M('crontab').where(
            'id=?', (sid,)).field(self.field).find()
        return slemp.getJson(data)

    def modifyCrondApi(self):
        sid = request.form.get('id', '')
        iname = request.form.get('name', '')
        field_type = request.form.get('type', '')
        week = request.form.get('week', '')
        where1 = request.form.get('where1', '')
        hour = request.form.get('hour', '')
        minute = request.form.get('minute', '')
        save = request.form.get('save', '')
        backup_to = request.form.get('backup_to', '')
        stype = request.form.get('stype', '')
        sname = request.form.get('sname', '')
        sbody = request.form.get('sbody', '')
        urladdress = request.form.get('urladdress', '')

        if len(iname) < 1:
            return slemp.returnJson(False, 'Nama penjadwalan tidak boleh kosong!')

        params = {
            'name': iname,
            'type': field_type,
            'week': week,
            'where1': where1,
            'hour': hour,
            'minute': minute,
            'save': save,
            'backup_to': backup_to,
            'stype': stype,
            'sname': sname,
            'sbody': sbody,
            'urladdress': urladdress,
        }
        cuonConfig, get, name = self.getCrondCycle(params)
        cronInfo = slemp.M('crontab').where(
            'id=?', (sid,)).field(self.field).find()
        del(cronInfo['id'])
        del(cronInfo['addtime'])
        cronInfo['name'] = get['name']
        cronInfo['type'] = get['type']
        cronInfo['where1'] = get['where1']
        cronInfo['where_hour'] = get['hour']
        cronInfo['where_minute'] = get['minute']
        cronInfo['save'] = get['save']
        cronInfo['backup_to'] = get['backup_to']
        cronInfo['sbody'] = get['sbody']
        cronInfo['urladdress'] = get['urladdress']

        addData = slemp.M('crontab').where('id=?', (sid,)).save('name,type,where1,where_hour,where_minute,save,backup_to,sbody,urladdress', (get[
            'name'], field_type, get['where1'], get['hour'], get['minute'], get['save'], get['backup_to'], get['sbody'], get['urladdress']))
        self.removeForCrond(cronInfo['echo'])
        self.syncToCrond(cronInfo)
        slemp.writeLog('Penjadwalan', 'Ubah penjadwalan [' + cronInfo['name'] + '] sukses!')
        return slemp.returnJson(True, 'Berhasil diubah')

    def logsApi(self):
        sid = request.form.get('id', '')
        echo = slemp.M('crontab').where("id=?", (sid,)).field('echo').find()
        logFile = slemp.getServerDir() + '/cron/' + echo['echo'] + '.log'
        if not os.path.exists(logFile):
            return slemp.returnJson(False, 'Log saat ini kosong!')
        log = slemp.getLastLine(logFile, 500)
        return slemp.returnJson(True, log)

    def addApi(self):
        iname = request.form.get('name', '')
        field_type = request.form.get('type', '')
        week = request.form.get('week', '')
        where1 = request.form.get('where1', '')
        hour = request.form.get('hour', '')
        minute = request.form.get('minute', '')
        save = request.form.get('save', '')
        backup_to = request.form.get('backupTo', '')
        stype = request.form.get('sType', '')
        sname = request.form.get('sName', '')
        sbody = request.form.get('sBody', '')
        urladdress = request.form.get('urladdress', '')

        if len(iname) < 1:
            return slemp.returnJson(False, 'Nama penjadwalan tidak boleh kosong!')

        params = {
            'name': iname,
            'type': field_type,
            'week': week,
            'where1': where1,
            'hour': hour,
            'minute': minute,
            'save': save,
            'backup_to': backup_to,
            'stype': stype,
            'sname': sname,
            'sbody': sbody,
            'urladdress': urladdress,
        }

        addData = self.add(params)
        if addData > 0:
            return slemp.returnJson(True, 'Berhasil ditambahkan')
        return slemp.returnJson(False, 'Tidak berhasil ditambahkan')

    def add(self, params):

        iname = params["name"]
        field_type = params["type"]
        week = params["week"]
        where1 = params["where1"]
        hour = params["hour"]
        minute = params["minute"]
        save = params["save"]
        backup_to = params["backup_to"]
        stype = params["stype"]
        sname = params["sname"]
        sbody = params["sbody"]
        urladdress = params["urladdress"]

        # print params
        cronConfig, get, name = self.getCrondCycle(params)
        cronPath = slemp.getServerDir() + '/cron'
        cronName = self.getShell(params)

        if type(cronName) == dict:
            return cronName

        cronConfig += ' ' + cronPath + '/' + cronName + \
            ' >> ' + cronPath + '/' + cronName + '.log 2>&1'

        # print(cronConfig)
        if not slemp.isAppleSystem():
            wRes = self.writeShell(cronConfig)
            if type(wRes) != bool:
                return wRes
            self.crondReload()

        add_time = time.strftime('%Y-%m-%d %X', time.localtime())
        task_id = slemp.M('crontab').add('name,type,where1,where_hour,where_minute,echo,addtime,status,save,backup_to,stype,sname,sbody,urladdress',
                                      (iname, field_type, where1, hour, minute, cronName, add_time, 1, save, backup_to, stype, sname, sbody, urladdress,))
        return task_id

    def startTaskApi(self):
        sid = request.form.get('id', '')
        echo = slemp.M('crontab').where('id=?', (sid,)).getField('echo')
        execstr = slemp.getServerDir() + '/cron/' + echo
        os.system('chmod +x ' + execstr)
        os.system('nohup ' + execstr + ' >> ' + execstr + '.log 2>&1 &')
        return slemp.returnJson(True, 'Penjadwalan dijalankan!')

    def delApi(self):
        task_id = request.form.get('id', '')
        try:
            data = self.delete(task_id)
            if not data[0]:
                return slemp.returnJson(False, data[1])
            return slemp.returnJson(True, 'Berhasil dihapus')
        except Exception as e:
            return slemp.returnJson(False, 'Gagal menghapus:' + str(e))

    def delete(self, tid):

        find = slemp.M('crontab').where("id=?", (tid,)).field('name,echo').find()
        if not self.removeForCrond(find['echo']):
            return (False, 'File tidak dapat ditulis, harap periksa apakah fungsi keamanan sistem diaktifkan!')

        cronPath = slemp.getServerDir() + '/cron'
        sfile = cronPath + '/' + find['echo']

        if os.path.exists(sfile):
            os.remove(sfile)
        sfile = cronPath + '/' + find['echo'] + '.log'
        if os.path.exists(sfile):
            os.remove(sfile)

        slemp.M('crontab').where("id=?", (tid,)).delete()
        slemp.writeLog('Penjadwalan', slemp.getInfo('Hapus penjadwalan [{1}] berhasil!', (find['name'],)))
        return (True, "OK")

    def delLogsApi(self):
        sid = request.form.get('id', '')
        try:
            echo = slemp.M('crontab').where("id=?", (sid,)).getField('echo')
            logFile = slemp.getServerDir() + '/cron/' + echo + '.log'
            os.remove(logFile)
            return slemp.returnJson(True, 'Log telah dihapus!')
        except:
            return slemp.returnJson(False, 'Gagal menghapus log!')

    def getDataListApi(self):
        stype = request.form.get('type', '')

        bak_data = []

        if stype == 'sites' or stype == 'databases':
            hookPath = slemp.getPanelDataDir() + "/hook_backup.json"
            if os.path.exists(hookPath):
                t = slemp.readFile(hookPath)
                bak_data = json.loads(t)

        if stype == 'databases':
            db_list = {}
            db_list['orderOpt'] = bak_data
            path = slemp.getServerDir() + '/mysql'
            if not os.path.exists(path + '/mysql.db'):
                db_list['data'] = []
            else:
                db_list['data'] = slemp.M('databases').dbPos(
                    path, 'mysql').field('name,ps').select()
            return slemp.getJson(db_list)

        data = {}
        data['orderOpt'] = bak_data
        data['data'] = slemp.M(stype).field('name,ps').select()
        return slemp.getJson(data)

    def toWeek(self, num):
        wheres = {
            0:   'Hari',
            1:   'Satu',
            2:   'Dua',
            3:   'Tiga',
            4:   'Empat',
            5:   'Lima',
            6:   'Enam'
        }
        try:
            return wheres[num]
        except:
            return ''

    def getCrondCycle(self, params):
        cuonConfig = ''
        name = ''
        if params['type'] == "day":
            cuonConfig = self.getDay(params)
            name = 'Setiap Hari'
        elif params['type'] == "day-n":
            cuonConfig = self.getDay_N(params)
            name = slemp.getInfo('Setiap {1} hari', (params['where1'],))
        elif params['type'] == "hour":
            cuonConfig = self.getHour(params)
            name = 'Setiap Jam'
        elif params['type'] == "hour-n":
            cuonConfig = self.getHour_N(params)
            name = 'Setiap Jam'
        elif params['type'] == "minute-n":
            cuonConfig = self.minute_N(params)
        elif params['type'] == "week":
            params['where1'] = params['week']
            cuonConfig = self.week(params)
        elif params['type'] == "month":
            cuonConfig = self.month(params)
        return cuonConfig, params, name

    def getDay(self, param):
        cuonConfig = "{0} {1} * * * ".format(param['minute'], param['hour'])
        return cuonConfig

    def getDay_N(self, param):
        cuonConfig = "{0} {1} */{2} * * ".format(
            param['minute'], param['hour'], param['where1'])
        return cuonConfig

    def getHour(self, param):
        cuonConfig = "{0} * * * * ".format(param['minute'])
        return cuonConfig

    def getHour_N(self, param):
        cuonConfig = "{0} */{1} * * * ".format(
            param['minute'], param['where1'])
        return cuonConfig

    def minute_N(self, param):
        cuonConfig = "*/{0} * * * * ".format(param['where1'])
        return cuonConfig

    def week(self, param):
        cuonConfig = "{0} {1} * * {2}".format(
            param['minute'], param['hour'], param['week'])
        return cuonConfig

    def month(self, param):
        cuonConfig = "{0} {1} {2} * * ".format(
            param['minute'], param['hour'], param['where1'])
        return cuonConfig

    def getShell(self, param):
        stype = param['stype']
        if stype == 'toFile':
            shell = param.sFile
        else:
            head = "#!/bin/bash\nPATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin\nexport PATH\n"
            log = '.log'

            panel_dir = slemp.getServerDir() + "/panel"
            script_dir = slemp.getServerDir() + "/panel/scripts"

            wheres = {
                'path': head + "python3 " + script_dir + "/backup.py path " + param['sname'] + " " + str(param['save']),
                'site':   head + "python3 " + script_dir + "/backup.py site " + param['sname'] + " " + str(param['save']),
                'database': head + "python3 " + script_dir + "/backup.py database " + param['sname'] + " " + str(param['save']),
                'logs':   head + "python3 " + script_dir + "/logs_backup.py " + param['sname'] + log + " " + str(param['save']),
                'rememory': head + "/bin/bash " + script_dir + '/rememory.sh'
            }
            if param['backup_to'] != 'localhost':
                cfile = slemp.getPluginDir() + "/" + \
                    param['backup_to'] + "/index.py"
                wheres = {
                    'path': head + "python3 " + cfile + " path " + param['sname'] + " " + str(param['save']),
                    'site':   head + "cd " + panel_dir + " && " + panel_dir + "/bin/python3 " + cfile + " site " + param['sname'] + " " + str(param['save']),
                    'database': head + "cd " + panel_dir + " && " + panel_dir + "/bin/python3 " + cfile + " database " + param['sname'] + " " + str(param['save']),
                    'logs':   head + "python3 " + script_dir + "/logs_backup.py " + param['sname'] + log + " " + str(param['save']),
                    'rememory': head + "/bin/bash " + script_dir + '/rememory.sh'
                }
            try:
                shell = wheres[stype]
            except:
                if stype == 'toUrl':
                    shell = head + "curl -sS --connect-timeout 10 -m 60 '" + \
                        param['urladdress'] + "'"
                else:
                    shell = head + param['sbody'].replace("\r\n", "\n")

                shell += '''
echo "----------------------------------------------------------------------------"
endDate=`date +"%Y-%m-%d %H:%M:%S"`
echo "★[$endDate] Successful"
echo "----------------------------------------------------------------------------"
'''
        cronPath = slemp.getServerDir() + '/cron'
        if not os.path.exists(cronPath):
            slemp.execShell('mkdir -p ' + cronPath)

        if not 'echo' in param:
            cronName = slemp.md5(slemp.md5(str(time.time()) + '_slemp'))
        else:
            cronName = param['echo']
        file = cronPath + '/' + cronName
        slemp.writeFile(file, self.checkScript(shell))
        slemp.execShell('chmod 750 ' + file)
        return cronName

    def checkScript(self, shell):
        keys = ['shutdown', 'init 0', 'mkfs', 'passwd',
                'chpasswd', '--stdin', 'mkfs.ext', 'mke2fs']
        for key in keys:
            shell = shell.replace(key, '[***]')
        return shell

    def writeShell(self, config):
        u_file = '/var/spool/cron/crontabs/root'
        if not os.path.exists(u_file):
            file = '/var/spool/cron/root'
            if slemp.isAppleSystem():
                file = '/etc/crontab'
        else:
            file = u_file

        if not os.path.exists(file):
            slemp.writeFile(file, '')
        conf = slemp.readFile(file)
        conf += str(config) + "\n"
        if slemp.writeFile(file, conf):
            if not os.path.exists(u_file):
                slemp.execShell("chmod 600 '" + file +
                             "' && chown root.root " + file)
            else:
                slemp.execShell("chmod 600 '" + file +
                             "' && chown root.crontab " + file)
            return True
        return slemp.returnJson(False, 'Penulisan file gagal, harap periksa apakah fungsi keamanan sistem diaktifkan!')

    def crondReload(self):
        if slemp.isAppleSystem():
            if os.path.exists('/etc/crontab'):
                pass
        else:
            if os.path.exists('/etc/init.d/crond'):
                slemp.execShell('/etc/init.d/crond reload')
            elif os.path.exists('/etc/init.d/cron'):
                slemp.execShell('service cron restart')
            else:
                slemp.execShell("systemctl reload crond")

    def removeForCrond(self, echo):
        u_file = '/var/spool/cron/crontabs/root'
        if not os.path.exists(u_file):
            file = '/var/spool/cron/root'
            if slemp.isAppleSystem():
                file = '/etc/crontab'

            if not os.path.exists(file):
                return False
        else:
            file = u_file

        if slemp.isAppleSystem():
            return True

        conf = slemp.readFile(file)
        rep = ".+" + str(echo) + ".+\n"
        conf = re.sub(rep, "", conf)
        if not slemp.writeFile(file, conf):
            return False
        self.crondReload()
        return True

    def syncToCrond(self, cronInfo):
        if 'status' in cronInfo:
            if cronInfo['status'] == 0:
                return False
        if 'where_hour' in cronInfo:
            cronInfo['hour'] = cronInfo['where_hour']
            cronInfo['minute'] = cronInfo['where_minute']
            cronInfo['week'] = cronInfo['where1']
        cuonConfig, cronInfo, name = self.getCrondCycle(cronInfo)
        cronPath = slemp.getServerDir() + '/cron'
        cronName = self.getShell(cronInfo)
        if type(cronName) == dict:
            return cronName
        cuonConfig += ' ' + cronPath + '/' + cronName + \
            ' >> ' + cronPath + '/' + cronName + '.log 2>&1'
        wRes = self.writeShell(cuonConfig)
        if type(wRes) != bool:
            return False
        self.crondReload()
