# coding: utf-8

import sys
import os
import re
import time

if sys.platform != 'darwin':
    os.chdir('/home/slemp/server/panel')


chdir = os.getcwd()
sys.path.append(chdir + '/class/core')

# reload(sys)
# sys.setdefaultencoding('utf-8')


import slemp
import db


class backupTools:

    def backupDatabase(self, name, count):
        db_path = slemp.getServerDir() + '/mariadb'
        db_sock = slemp.getServerDir() + '/mariadb/'
        db_name = 'mysql'
        name = slemp.M('databases').dbPos(db_path, 'mysql').where(
            'name=?', (name,)).getField('name')
        startTime = time.time()
        if not name:
            endDate = time.strftime('%Y/%m/%d %X', time.localtime())
            log = "Database [" + name + "] does not exist!"
            print("★[" + endDate + "] " + log)
            print(
                "----------------------------------------------------------------------------")
            return

        backup_path = slemp.getRootDir() + '/backup/database/mariadb'
        if not os.path.exists(backup_path):
            slemp.execShell("mkdir -p " + backup_path)

        filename = backup_path + "/db_" + name + "_" + \
            time.strftime('%Y%m%d_%H%M%S', time.localtime()) + ".sql.gz"

        mysql_root = slemp.M('config').dbPos(db_path, db_name).where(
            "id=?", (1,)).getField('mysql_root')

        my_conf_path = db_path + '/etc/my.cnf'
        content = slemp.readFile(my_conf_path)
        rep = "\[mysqldump\]\nuser=root"
        sea = "[mysqldump]\n"
        subStr = sea + "user=root\npassword=" + mysql_root + "\n"
        content = content.replace(sea, subStr)
        if len(content) > 100:
            slemp.writeFile(my_conf_path, content)

        # slemp.execShell(db_path + "/bin/mysqldump --defaults-file=" + my_conf_path + " --opt --default-character-set=utf8 " +
        #              name + " | gzip > " + filename)

        # slemp.execShell(db_path + "/bin/mysqldump --defaults-file=" + my_conf_path + " --skip-lock-tables --default-character-set=utf8 " +
        #              name + " | gzip > " + filename)

        cmd = db_path + "/bin/mysqldump --defaults-file=" + my_conf_path + "  --single-transaction --quick --default-character-set=utf8 " + \
            name + " | gzip > " + filename
        slemp.execShell(cmd)

        if not os.path.exists(filename):
            endDate = time.strftime('%Y/%m/%d %X', time.localtime())
            log = "Backup of database ["+name+"] failed!"
            print("★[" + endDate + "] " + log)
            print(
                "----------------------------------------------------------------------------")
            return

        mycnf = slemp.readFile(db_path + '/etc/my.cnf')
        mycnf = mycnf.replace(subStr, sea)
        if len(mycnf) > 100:
            slemp.writeFile(db_path + '/etc/my.cnf', mycnf)

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
        print("|---File name:" + filename)

        backups = slemp.M('backup').where(
            'type=? and pid=?', ('1', pid)).field('id,filename').select()

        num = len(backups) - int(count)
        if num > 0:
            for backup in backups:
                slemp.execShell("rm -f " + backup['filename'])
                slemp.M('backup').where('id=?', (backup['id'],)).delete()
                num -= 1
                print("|---Outdated backup files cleaned up：" + backup['filename'])
                if num < 1:
                    break

    def backupDatabaseAll(self, save):
        db_path = slemp.getServerDir() + '/mariadb'
        db_name = 'mysql'
        databases = slemp.M('databases').dbPos(
            db_path, db_name).field('name').select()
        for database in databases:
            self.backupDatabase(database['name'], save)


if __name__ == "__main__":
    backup = backupTools()
    type = sys.argv[1]
    if type == 'database':
        if sys.argv[2] == 'ALL':
            backup.backupDatabaseAll(sys.argv[3])
        else:
            backup.backupDatabase(sys.argv[2], sys.argv[3])
