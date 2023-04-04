# coding: utf-8

import sys
import os
import re

if sys.platform != 'darwin':
    os.chdir('/home/slemp/server/panel')


chdir = os.getcwd()
sys.path.append(chdir + '/class/core')

# reload(sys)
# sys.setdefaultencoding('utf-8')


import slemp
import db
import time


class backupTools:

    def backupSite(self, name, count):
        sql = db.Sql()
        path = sql.table('sites').where('name=?', (name,)).getField('path')
        startTime = time.time()
        if not path:
            endDate = time.strftime('%Y/%m/%d %X', time.localtime())
            log = "网站[" + name + "]不存在!"
            print("★[" + endDate + "] " + log)
            print(
                "----------------------------------------------------------------------------")
            return

        backup_path = slemp.getBackupDir() + '/site'
        if not os.path.exists(backup_path):
            slemp.execShell("mkdir -p " + backup_path)

        filename = backup_path + "/web_" + name + "_" + \
            time.strftime('%Y%m%d_%H%M%S', time.localtime()) + '.tar.gz'

        cmd = "cd " + os.path.dirname(path) + " && tar zcvf '" + \
            filename + "' '" + os.path.basename(path) + "' > /dev/null"

        # print(cmd)
        slemp.execShell(cmd)

        endDate = time.strftime('%Y/%m/%d %X', time.localtime())
        print(filename)
        if not os.path.exists(filename):
            log = "Website ["+name+"] backup failed!"
            print("★[" + endDate + "] " + log)
            print(
                "----------------------------------------------------------------------------")
            return

        outTime = time.time() - startTime
        pid = sql.table('sites').where('name=?', (name,)).getField('id')
        sql.table('backup').add('type,name,pid,filename,addtime,size', ('0', os.path.basename(
            filename), pid, filename, endDate, os.path.getsize(filename)))
        log = "The website [" + name + "] was backed up successfully, and it took [" + str(round(outTime, 2)) + "] seconds"
        slemp.writeLog('Scheduled Tasks', log)
        print("★[" + endDate + "] " + log)
        print("|---Keep the most recent [" + count + "] backups")
        print("|---File name:" + filename)

        backups = sql.table('backup').where(
            'type=? and pid=?', ('0', pid)).field('id,filename').select()

        num = len(backups) - int(count)
        if num > 0:
            for backup in backups:
                slemp.execShell("rm -f " + backup['filename'])
                sql.table('backup').where('id=?', (backup['id'],)).delete()
                num -= 1
                print("|---Outdated backup files cleaned up：" + backup['filename'])
                if num < 1:
                    break

    def getConf(self, mtype='mysql'):
        path = slemp.getServerDir() + '/' + mtype + '/etc/my.cnf'
        return path

    def mypass(self, act, root):
        conf_file = self.getConf('mysql')
        slemp.execShell("sed -i '/user=root/d' {}".format(conf_file))
        slemp.execShell("sed -i '/password=/d' {}".format(conf_file))
        if act:
            mycnf = slemp.readFile(conf_file)
            src_dump = "[mysqldump]\n"
            sub_dump = src_dump + "user=root\npassword=\"{}\"\n".format(root)
            if not mycnf:
                return False
            mycnf = mycnf.replace(src_dump, sub_dump)
            if len(mycnf) > 100:
                slemp.writeFile(conf_file, mycnf)
            return True
        return True

    def backupDatabase(self, name, count):
        db_path = slemp.getServerDir() + '/mysql'
        db_name = 'mysql'
        name = slemp.M('databases').dbPos(db_path, 'mysql').where(
            'name=?', (name,)).getField('name')
        startTime = time.time()
        if not name:
            endDate = time.strftime('%Y/%m/%d %X', time.localtime())
            log = "Database ["+name+"] does not exist!"
            print("★[" + endDate + "] " + log)
            print(
                "----------------------------------------------------------------------------")
            return

        backup_path = slemp.getBackupDir() + '/database'
        if not os.path.exists(backup_path):
            slemp.execShell("mkdir -p " + backup_path)

        filename = backup_path + "/db_" + name + "_" + \
            time.strftime('%Y%m%d_%H%M%S', time.localtime()) + ".sql.gz"

        mysql_root = slemp.M('config').dbPos(db_path, db_name).where(
            "id=?", (1,)).getField('mysql_root')

        my_cnf = self.getConf('mysql')
        self.mypass(True, mysql_root)

        # slemp.execShell(db_path + "/bin/mysqldump --opt --default-character-set=utf8 " +
        #              name + " | gzip > " + filename)

        # slemp.execShell(db_path + "/bin/mysqldump --skip-lock-tables --default-character-set=utf8 " +
        #              name + " | gzip > " + filename)

        # slemp.execShell(db_path + "/bin/mysqldump  --single-transaction --quick --default-character-set=utf8 " +
        #              name + " | gzip > " + filename)

        cmd = db_path + "/bin/mysqldump --defaults-file=" + my_cnf + "  --force --opt --default-character-set=utf8 " + \
            name + " | gzip > " + filename
        # print(cmd)
        slemp.execShell(cmd)

        if not os.path.exists(filename):
            endDate = time.strftime('%Y/%m/%d %X', time.localtime())
            log = "Backup of database ["+name+"] failed!"
            print("★[" + endDate + "] " + log)
            print(
                "----------------------------------------------------------------------------")
            return

        self.mypass(False, mysql_root)

        endDate = time.strftime('%Y/%m/%d %X', time.localtime())
        outTime = time.time() - startTime
        pid = slemp.M('databases').dbPos(db_path, db_name).where(
            'name=?', (name,)).getField('id')

        slemp.M('backup').add('type,name,pid,filename,addtime,size', (1, os.path.basename(
            filename), pid, filename, endDate, os.path.getsize(filename)))
        log = "The database [" + name + "] was backed up successfully, and it took [" + str(round(outTime, 2)) + "] seconds"
        slemp.writeLog('Scheduled Tasks', log)
        print("★[" + endDate + "] " + log)
        print("|---Keep the most recent [" + count + "] backups")
        print("|---Filename:" + filename)

        backups = slemp.M('backup').where(
            'type=? and pid=?', ('1', pid)).field('id,filename').select()

        num = len(backups) - int(count)
        if num > 0:
            for backup in backups:
                slemp.execShell("rm -f " + backup['filename'])
                slemp.M('backup').where('id=?', (backup['id'],)).delete()
                num -= 1
                print("|---Expired backup files cleaned up: " + backup['filename'])
                if num < 1:
                    break

    def backupSiteAll(self, save):
        sites = slemp.M('sites').field('name').select()
        for site in sites:
            self.backupSite(site['name'], save)

    def backupDatabaseAll(self, save):
        db_path = slemp.getServerDir() + '/mysql'
        db_name = 'mysql'
        databases = slemp.M('databases').dbPos(
            db_path, db_name).field('name').select()
        for database in databases:
            self.backupDatabase(database['name'], save)

    def findPathName(self, path, filename):
        f = os.scandir(path)
        l = []
        for ff in f:
            if ff.name.find(filename) > -1:
                l.append(ff.name)
        return l

    def backupPath(self, path, count):

        slemp.echoStart('Backup')

        backup_path = slemp.getBackupDir() + '/path'
        if not os.path.exists(backup_path):
            slemp.execShell("mkdir -p " + backup_path)

        dirname = os.path.basename(path)
        fname = 'path_{}_{}.tar.gz'.format(
            dirname, slemp.formatDate("%Y%m%d_%H%M%S"))
        dfile = os.path.join(backup_path, fname)

        p_size = slemp.getPathSize(path)
        stime = time.time()

        cmd = "cd " + os.path.dirname(path) + " && tar zcvf '" + dfile + "' '" + dirname + "' 2>{err_log} 1> /dev/null".format(
            err_log='/tmp/backup_err.log')
        slemp.execShell(cmd)

        tar_size = os.path.getsize(dfile)

        slemp.echoInfo('Backup directory：' + path)
        slemp.echoInfo('Directory is backed up to：' + dfile)
        slemp.echoInfo("Directory size：{}".format(slemp.toSize(p_size)))
        slemp.echoInfo("Start compressing files：{}".format(slemp.formatDate(times=stime)))
        slemp.echoInfo("The file compression is completed, it takes {:.2f} seconds, and the size of the compressed package：{}".format(
            time.time() - stime, slemp.toSize(tar_size)))
        slemp.echoInfo('Keep the most recent backup number：' + count + '份')

        backups = self.findPathName(backup_path, 'path_{}'.format(dirname))
        num = len(backups) - int(count)
        backups.sort()
        if num > 0:
            for backup in backups:
                abspath_bk = backup_path + "/" + backup
                slemp.execShell("rm -f " + abspath_bk)
                slemp.echoInfo("|---Outdated backup files cleaned up：" + abspath_bk)
                num -= 1
                if num < 1:
                    break

        slemp.echoEnd('Backup')

if __name__ == "__main__":
    backup = backupTools()
    stype = sys.argv[1]
    if stype == 'site':
        if sys.argv[2] == 'ALL':
            backup.backupSiteAll(sys.argv[3])
        else:
            backup.backupSite(sys.argv[2], sys.argv[3])
    elif stype == 'database':
        if sys.argv[2] == 'ALL':
            backup.backupDatabaseAll(sys.argv[3])
        else:
            backup.backupDatabase(sys.argv[2], sys.argv[3])
    elif stype == 'path':
        backup.backupPath(sys.argv[2], sys.argv[3])
