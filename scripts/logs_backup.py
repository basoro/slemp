#!/usr/bin/python
# coding: utf-8
import sys
import os
import shutil
import time
import glob

if sys.platform != 'darwin':
    os.chdir('/home/slemp/server/panel')


chdir = os.getcwd()
sys.path.append(chdir + '/class/core')
# reload(sys)
# sys.setdefaultencoding('utf-8')

import slemp
print('==================================================================')
print('★[' + time.strftime("%Y/%m/%d %H:%M:%S") + ']，cut log')
print('==================================================================')
print('|--Currently keep the latest [' + sys.argv[2] + ']份')
logsPath = slemp.getLogsDir()
px = '.log'


def split_logs(oldFileName, num):
    global logsPath
    if not os.path.exists(oldFileName):
        print('|---' + oldFileName + ' file does not exist!')
        return

    logs = sorted(glob.glob(oldFileName + "_*"))
    count = len(logs)
    num = count - num

    for i in range(count):
        if i > num:
            break
        os.remove(logs[i])
        print('|---redundant log [' + logs[i] + '] deleted!')

    newFileName = oldFileName + '_' + time.strftime("%Y-%m-%d_%H%M%S") + '.log'
    shutil.move(oldFileName, newFileName)
    print('|---Cut log to: ' + newFileName)


def split_all(save):
    sites = slemp.M('sites').field('name').select()
    for site in sites:
        oldFileName = logsPath + site['name'] + px
        split_logs(oldFileName, save)

if __name__ == '__main__':
    num = int(sys.argv[2])
    if sys.argv[1].find('ALL') == 0:
        split_all(num)
    else:
        siteName = sys.argv[1]
        if siteName[-4:] == '.log':
            siteName = siteName[:-4]
        else:
            siteName = siteName.replace("-access_log", '')
        oldFileName = logsPath + '/' + sys.argv[1]
        errOldFileName = logsPath + '/' + \
            sys.argv[1].strip(".log") + ".error.log"
        split_logs(oldFileName, num)
        if os.path.exists(errOldFileName):
            split_logs(errOldFileName, num)
    path = slemp.getServerDir()
    os.system("kill -USR1 `cat " + path + "/openresty/nginx/logs/nginx.pid`")
