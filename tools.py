# coding: utf-8

import sys
import os
import json
import time

sys.path.append(os.getcwd() + "/class/core")
import slemp
import db

INIT_DIR = "/etc/init.d"
if slemp.isAppleSystem():
    INIT_DIR = slemp.getRunDir() + "/scripts/init.d"

INIT_CMD = INIT_DIR + "/slemp"


def slemp_input_cmd(msg):
    if sys.version_info[0] == 2:
        in_val = raw_input(msg)
    else:
        in_val = input(msg)
    return in_val


def slempcli(slemp_input=0):
    raw_tip = "======================================================"
    if not slemp_input:
        print("===============SLEMP-Panel cli tools=================")
        print("(1) Restart panel service")
        print("(2) Stop panel service")
        print("(3) Launchpad service")
        print("(4) Reload panel service")
        print("(5) Modify panel ports")
        print("(10) View panel default information")
        print("(11) Modify panel password")
        print("(12) Modify panel username")
        print("(13) Display panel error log")
        print("(0) Cancel")
        print(raw_tip)
        try:
            slemp_input = input("Please enter the command number：")
            if sys.version_info[0] == 3:
                slemp_input = int(slemp_input)
        except:
            slemp_input = 0

    nums = [1, 2, 3, 4, 5, 10, 11, 12, 13]
    if not slemp_input in nums:
        print(raw_tip)
        print("Cancelled!")
        exit()

    if slemp_input == 1:
        os.system(INIT_CMD + " restart")
    elif slemp_input == 2:
        os.system(INIT_CMD + " stop")
    elif slemp_input == 3:
        os.system(INIT_CMD + " start")
    elif slemp_input == 4:
        os.system(INIT_CMD + " reload")
    elif slemp_input == 5:
        in_port = slemp_input_cmd("Please enter a new panel port：")
        in_port_int = int(in_port.strip())
        if in_port_int < 65536 and in_port_int > 0:
            import firewall_api
            firewall_api.firewall_api().addAcceptPortArgs(
                in_port, 'WEB panel [TOOLS modification]', 'port')
            slemp.writeFile('data/port.pl', in_port)
        else:
            print("|-The port range is between 0-65536")
        return
    elif slemp_input == 10:
        os.system(INIT_CMD + " default")
    elif slemp_input == 11:
        input_pwd = slemp_input_cmd("Please enter a new panel password：")
        if len(input_pwd.strip()) < 5:
            print("|-Error, password length cannot be less than 5 characters")
            return
        set_panel_pwd(input_pwd.strip(), True)
    elif slemp_input == 12:
        input_user = slemp_input_cmd("Please enter a new panel username (>3 digits)：")
        set_panel_username(input_user.strip())
    elif slemp_input == 13:
        os.system('tail -100 ' + slemp.getRunDir() + '/logs/error.log')

def set_panel_pwd(password, ncli=False):
    import db
    sql = db.Sql()
    result = sql.table('users').where('id=?', (1,)).setField(
        'password', slemp.md5(password))
    username = sql.table('users').where('id=?', (1,)).getField('username')
    if ncli:
        print("|-Username: " + username)
        print("|-Password: " + password)
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
    method = sys.argv[1]
    if method == 'panel':
        set_panel_pwd(sys.argv[2])
    elif method == 'username':
        if len(sys.argv) > 2:
            set_panel_username(sys.argv[2])
        else:
            set_panel_username()
    elif method == 'getServerIp':
        getServerIp()
    elif method == "cli":
        clinum = 0
        try:
            if len(sys.argv) > 2:
                clinum = int(sys.argv[2]) if sys.argv[2][:6] else sys.argv[2]
        except:
            clinum = sys.argv[2]
        slempcli(clinum)
    else:
        print('ERROR: Parameter error')
