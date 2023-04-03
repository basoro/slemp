# coding: utf-8

import os
import sys
import time
import string
import json
import hashlib
import shlex
import datetime
import subprocess
import re
import hashlib
from random import Random

import slemp
import db

from flask import redirect


def init():
    initDB()
    initUserInfo()
    initInitD()
    initInitTask()


def local():
    result = checkClose()
    if result:
        return result


def checkClose():
    if os.path.exists('data/close.pl'):
        return redirect('/close')


def initDB():
    try:
        sql = db.Sql().dbfile('default')
        csql = slemp.readFile('data/sql/default.sql')
        csql_list = csql.split(';')
        for index in range(len(csql_list)):
            sql.execute(csql_list[index], ())

    except Exception as ex:
        print(str(ex))


def doContentReplace(src, dst):
    content = slemp.readFile(src)
    content = content.replace("{$SERVER_PATH}", slemp.getRunDir())
    slemp.writeFile(dst, content)


def initInitD():

    # systemctl
    # sysCfgDir = slemp.systemdCfgDir()
    # if os.path.exists(sysCfgDir) and slemp.getOsName() == 'centos' and slemp.getOsID() == '9':
    #     systemd_slemp = sysCfgDir + '/slemp.service'
    #     systemd_slemp_task = sysCfgDir + '/slemp-task.service'

    #     systemd_slemp_tpl = slemp.getRunDir() + '/scripts/init.d/slemp.service.tpl'
    #     systemd_slemp_task_tpl = slemp.getRunDir() + '/scripts/init.d/slemp-task.service.tpl'

    #     if os.path.exists(systemd_slemp):
    #         os.remove(systemd_slemp)
    #     if os.path.exists(systemd_slemp_task):
    #         os.remove(systemd_slemp_task)

    #     doContentReplace(systemd_slemp_tpl, systemd_slemp)
    #     doContentReplace(systemd_slemp_task_tpl, systemd_slemp_task)

    #     slemp.execShell('systemctl enable slemp')
    #     slemp.execShell('systemctl enable slemp-task')
    #     slemp.execShell('systemctl daemon-reload')

    script = slemp.getRunDir() + '/scripts/init.d/slemp.tpl'
    script_bin = slemp.getRunDir() + '/scripts/init.d/slemp'
    doContentReplace(script, script_bin)
    slemp.execShell('chmod +x ' + script_bin)

    if not slemp.isAppleSystem() and not os.path.exists("/etc/rc.d/init.d"):
        slemp.execShell('mkdir -p /etc/rc.d/init.d')

    if not slemp.isAppleSystem() and not os.path.exists("/etc/init.d"):
        slemp.execShell('mkdir -p /etc/init.d')

    # initd
    if os.path.exists('/etc/rc.d/init.d'):
        initd_bin = '/etc/rc.d/init.d/slemp'
        if not os.path.exists(initd_bin):
            import shutil
            shutil.copyfile(script_bin, initd_bin)
            slemp.execShell('chmod +x ' + initd_bin)
        slemp.execShell('which chkconfig && chkconfig --add slemp')

    if os.path.exists('/etc/init.d'):
        initd_bin = '/etc/init.d/slemp'
        if not os.path.exists(initd_bin):
            import shutil
            shutil.copyfile(script_bin, initd_bin)
            slemp.execShell('chmod +x ' + initd_bin)
        slemp.execShell('which update-rc.d && update-rc.d -f slemp defaults')

    slemp.setHostAddr(slemp.getLocalIp())


def initInitTask():
    import cert_api
    api = cert_api.cert_api()
    api.createCertCron()


def initUserInfo():

    data = slemp.M('users').where('id=?', (1,)).getField('password')
    if data == '21232f297a57a5a743894a0e4a801fc3':
        pwd = slemp.getRandomString(8).lower()
        file_pw = slemp.getRunDir() + '/data/default.pl'
        slemp.writeFile(file_pw, pwd)
        slemp.M('users').where('id=?', (1,)).setField(
            'password', slemp.md5(pwd))
