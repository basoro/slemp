# coding: utf-8

import sys
import os
import json
import time

sys.path.append(os.getcwd() + "/class/core")
import slemp
import db

def set_panel_pwd(password, ncli=False):
    import db
    sql = db.Sql()
    result = sql.table('users').where('id=?', (1,)).setField(
        'password', slemp.md5(password))
    username = sql.table('users').where('id=?', (1,)).getField('username')
    if ncli:
        print("|-用户名: " + username)
        print("|-新密码: " + password)
    else:
        print(username)


def set_panel_username(username=None):
    import db
    sql = db.Sql()
    if username:
        if len(username) < 5:
            print("Error, username cannot be less than 5 characters long")
            return
        if username in ['admin', 'root']:
            print("Error, too simple username cannot be used")
            return

        sql.table('users').where('id=?', (1,)).setField('username', username)
        print("New user name: %s" % username)
        return

    username = sql.table('users').where('id=?', (1,)).getField('username')
    if username == 'admin':
        username = slemp.getRandomString(8).lower()
        sql.table('users').where('id=?', (1,)).setField('username', username)
    print('username: ' + username)


def getServerIp():
    version = sys.argv[2]
    ip = slemp.execShell(
        "curl -{} -sS --connect-timeout 5 -m 60 https://v6r.ipip.net/?format=text".format(version))
    print(ip[0])


if __name__ == "__main__":
    type = sys.argv[1]
    if type == 'panel':
        set_panel_pwd(sys.argv[2])
    elif type == 'username':
        if len(sys.argv) > 2:
            set_panel_username(sys.argv[2])
        else:
            set_panel_username()
    elif type == 'getServerIp':
        getServerIp()
    else:
        print('ERROR: Parameter error')
