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

    ##### ----- start ----- ###
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
                tmp['type'] = 'Every day'
                tmp['cycle'] = slemp.getInfo('Execute at {1} and {2} minutes every day', (str(
                    _list[i]['where_hour']), str(_list[i]['where_minute'])))
            elif _list[i]['type'] == "day-n":
                tmp['type'] = slemp.getInfo(
                    'Every {1} days', (str(_list[i]['where1']),))
                tmp['cycle'] = slemp.getInfo('Execute every {1} days, {2} hours and {3} minutes',  (str(
                    _list[i]['where1']), str(_list[i]['where_hour']), str(_list[i]['where_minute'])))
            elif _list[i]['type'] == "hour":
                tmp['type'] = 'Per hour'
                tmp['cycle'] = slemp.getInfo(
                    'Every hour, {1} minute Execution', (str(_list[i]['where_minute']),))
            elif _list[i]['type'] == "hour-n":
                tmp['type'] = slemp.getInfo(
                    'Every {1} hours', (str(_list[i]['where1']),))
                tmp['cycle'] = slemp.getInfo('Execute every {1} hour, {2} minutes', (str(
                    _list[i]['where1']), str(_list[i]['where_minute'])))
            elif _list[i]['type'] == "minute-n":
                tmp['type'] = slemp.getInfo(
                    'Every {1} minutes', (str(_list[i]['where1']),))
                tmp['cycle'] = slemp.getInfo(
                    'Execute every {1} minutes', (str(_list[i]['where1']),))
            elif _list[i]['type'] == "week":
                tmp['type'] = 'Weekly'
                if not _list[i]['where1']:
                    _list[i]['where1'] = '0'
                tmp['cycle'] = slemp.getInfo('Execute at {1}, {2} and {3} every week', (self.toWeek(int(
                    _list[i]['where1'])), str(_list[i]['where_hour']), str(_list[i]['where_minute'])))
            elif _list[i]['type'] == "month":
                tmp['type'] = 'Per month'
                tmp['cycle'] = slemp.getInfo('Executed at {2} o\'clock {3} on {1} day every month', (str(_list[i]['where1']), str(
                    _list[i]['where_hour']), str(_list[i]['where_minute'])))
            data.append(tmp)

        rdata = {}
        rdata['data'] = data

        count = slemp.M('crontab').where('', ()).count()
        _page = {}
        _page['count'] = count
        _page['p'] = p
        _page['row'] = psize
        _page['tojs'] = "getCronData"

        rdata['list'] = slemp.getPage(_page)
        rdata['p'] = p

        # backup hook
        bh_file = slemp.getPanelDataDir() + "/hook_backup.json"
        if os.path.exists(bh_file):
            hb_data = slemp.readFile(bh_file)
            hb_data = json.loads(hb_data)
            rdata['backup_hook'] = hb_data

        return slemp.getJson(rdata)

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
            'Scheduled Tasks', 'Modify the status of the scheduled task [' + cronInfo['name'] + '] to [' + str(status) + ']')
        return slemp.returnJson(True, 'Successfully set')

    def getCrondFindApi(self):
        sid = request.form.get('id', '')
        data = slemp.M('crontab').where(
            'id=?', (sid,)).field(self.field).find()
        return slemp.getJson(data)

    def cronCheck(self, params):

        if params['stype'] == 'site' or params['stype'] == 'database' or params['stype'].find('database_') > -1 or params['stype'] == 'logs' or params['stype'] == 'path':
            if params['save'] == '':
                return False, 'Reserved copies cannot be empty!'

        if params['type'] == 'day':
            if params['hour'] == '':
                return False, 'Hour cannot be empty!'
            if params['minute'] == '':
                return False, 'Minutes cannot be empty!'

        if params['type'] == 'day-n':
            if params['where1'] == '':
                return False, 'Day cannot be empty!'
            if params['hour'] == '':
                return False, 'Hour cannot be empty!'
            if params['minute'] == '':
                return False, 'Minutes cannot be empty!'
        if params['type'] == 'hour':
            if params['minute'] == '':
                return False, 'Minutes cannot be empty!'

        if params['type'] == 'hour-n':
            if params['where1'] == '':
                return False, 'Hour cannot be empty!'
            if params['minute'] == '':
                return False, 'Minutes cannot be empty!'

        if params['type'] == 'minute-n':
            if params['where1'] == '':
                return False, 'Minutes cannot be empty!'

        if params['type'] == 'week':
            if params['hour'] == '':
                return False, 'Hour cannot be empty!'
            if params['minute'] == '':
                return False, 'Minutes cannot be empty!'

        if params['type'] == 'month':
            if params['where1'] == '':
                return False, 'Day cannot be empty!'
            if params['hour'] == '':
                return False, 'Hour cannot be empty!'
            if params['minute'] == '':
                return False, 'Minutes cannot be empty!'

        return True, 'OK'

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
            return slemp.returnJson(False, 'Task name cannot be empty!')

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

        is_check_pass, msg = self.cronCheck(params)
        if not is_check_pass:
            return slemp.returnJson(is_check_pass, msg)

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

        addData = slemp.M('crontab').where('id=?', (sid,)).save('name,type,where1,where_hour,where_minute,save,backup_to, sname, sbody,urladdress',
                                                             (iname, field_type, get['where1'], get['hour'], get['minute'], get['save'], get['backup_to'], sname, get['sbody'], get['urladdress']))
        self.removeForCrond(cronInfo['echo'])
        self.syncToCrond(cronInfo)
        slemp.writeLog('Scheduled Tasks', 'Modify scheduled task [' + cronInfo['name'] + '] successfully')
        return slemp.returnJson(True, 'Successfully modified')

    def logsApi(self):
        sid = request.form.get('id', '')
        echo = slemp.M('crontab').where("id=?", (sid,)).field('echo').find()
        logFile = slemp.getServerDir() + '/cron/' + echo['echo'] + '.log'
        if not os.path.exists(logFile):
            return slemp.returnJson(False, 'Current log is empty!')
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
            return slemp.returnJson(False, 'Task name cannot be empty!')

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

        is_check_pass, msg = self.cronCheck(params)
        if not is_check_pass:
            return slemp.returnJson(is_check_pass, msg)

        addData = self.add(params)
        if addData > 0:
            return slemp.returnJson(True, 'Added successfully')
        return slemp.returnJson(False, 'Add failed')

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
        return slemp.returnJson(True, 'Task executed!')

    def delApi(self):
        task_id = request.form.get('id', '')
        try:
            data = self.delete(task_id)
            if not data[0]:
                return slemp.returnJson(False, data[1])
            return slemp.returnJson(True, 'Successfully deleted')
        except Exception as e:
            return slemp.returnJson(False, 'Failed to delete:' + str(e))

    def delete(self, tid):

        find = slemp.M('crontab').where("id=?", (tid,)).field('name,echo').find()
        if not self.removeForCrond(find['echo']):
            return (False, 'Unable to write the file, please check whether the system hardening function is enabled!')

        cronPath = slemp.getServerDir() + '/cron'
        sfile = cronPath + '/' + find['echo']

        if os.path.exists(sfile):
            os.remove(sfile)
        sfile = cronPath + '/' + find['echo'] + '.log'
        if os.path.exists(sfile):
            os.remove(sfile)

        slemp.M('crontab').where("id=?", (tid,)).delete()
        slemp.writeLog('Scheduled Tasks', slemp.getInfo('Deleting scheduled task [{1}] succeeded!', (find['name'],)))
        return (True, "OK")

    def delLogsApi(self):
        sid = request.form.get('id', '')
        try:
            echo = slemp.M('crontab').where("id=?", (sid,)).getField('echo')
            logFile = slemp.getServerDir() + '/cron/' + echo + '.log'
            os.remove(logFile)
            return slemp.returnJson(True, 'Mission log has been cleared!')
        except:
            return slemp.returnJson(False, 'Failed to clear task log!')

    def getDataListApi(self):
        stype = request.form.get('type', '')

        bak_data = []
        if stype == 'site' or stype == 'sites' or stype == 'database' or stype.find('database_') > -1 or stype == 'path':
            hookPath = slemp.getPanelDataDir() + "/hook_backup.json"
            if os.path.exists(hookPath):
                t = slemp.readFile(hookPath)
                bak_data = json.loads(t)

        if stype == 'database' or stype.find('database_') > -1:
            sqlite3_name = 'mysql'
            path = slemp.getServerDir() + '/mysql'
            if stype != 'database':
                soft_name = stype.replace('database_', '')
                path = slemp.getServerDir() + '/' + soft_name

                if soft_name == 'postgresql':
                    sqlite3_name = 'pgsql'

            db_list = {}
            db_list['orderOpt'] = bak_data

            if not os.path.exists(path + '/' + sqlite3_name + '.db'):
                db_list['data'] = []
            else:
                db_list['data'] = slemp.M('databases').dbPos(
                    path, sqlite3_name).field('name,ps').select()
            return slemp.getJson(db_list)

        if stype == 'path':
            db_list = {}
            db_list['data'] = [{"name": slemp.getWwwDir(), "ps": "www"}]
            db_list['orderOpt'] = bak_data
            return slemp.getJson(db_list)

        data = {}
        data['orderOpt'] = bak_data

        default_db = 'sites'
        # if stype == 'site' or stype == 'logs':
        #     stype == 'sites'

        data['data'] = slemp.M(default_db).field('name,ps').select()
        return slemp.getJson(data)
    ##### ----- start ----- ###

    def toWeek(self, num):
        wheres = {
            0:   'Day',
            1:   'One',
            2:   'Two',
            3:   'Three',
            4:   'Four',
            5:   'Five',
            6:   'Six'
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
            name = 'Every day'
        elif params['type'] == "day-n":
            cuonConfig = self.getDay_N(params)
            name = slemp.getInfo('Every {1} days', (params['where1'],))
        elif params['type'] == "hour":
            cuonConfig = self.getHour(params)
            name = 'Per hour'
        elif params['type'] == "hour-n":
            cuonConfig = self.getHour_N(params)
            name = 'Per hour'
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
        # try:
        stype = param['stype']
        if stype == 'toFile':
            shell = param.sFile
        else:
            head = "#!/bin/bash\nPATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin\nexport PATH\n"

            source_bin_activate = '''
export LANG=en_US.UTF-8
SLEMP_PATH=%s/bin/activate
if [ -f $SLEMP_PATH ];then
    source $SLEMP_PATH
fi''' % (slemp.getRunDir(),)

            head = head + source_bin_activate + "\n"
            log = '.log'

            script_dir = slemp.getRunDir() + "/scripts"
            source_stype = 'database'
            if stype.find('database_') > -1:
                plugin_name = stype.replace('database_', '')
                script_dir = slemp.getRunDir() + "/plugins/" + plugin_name + "/scripts"

                source_stype = stype
                stype = 'database'

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

                wheres['path'] = head + "python3 " + cfile + \
                    " path " + param['sname'] + " " + str(param['save'])
                wheres['site'] = head + "cd " + slemp.getRunDir() + " && " + slemp.getRunDir() + "/bin/python3 " + cfile + \
                    " site " + param['sname'] + " " + str(param['save'])
                wheres['database'] = head + "cd " + slemp.getRunDir() + " && " + slemp.getRunDir() + "/bin/python3 " + cfile + " " + \
                    source_stype + " " + \
                    param['sname'] + " " + str(param['save'])
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
        return slemp.returnJson(False, 'Failed to write the file, please check whether the system hardening function is enabled!')

    def crondReload(self):
        if slemp.isAppleSystem():
            # slemp.execShell('/usr/sbin/cron restart')
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
