# coding: utf-8

import sys
import os
import json
import time
import re

sys.path.append(os.getcwd() + "/class/core")
import slemp
import db

# cmd = 'ls /usr/local/lib/ | grep python  | cut -d \\  -f 1 | awk \'END {print}\''
# info = slemp.execShell(cmd)
# p = "/usr/local/lib/" + info[0].strip() + "/site-packages"
# sys.path.append(p)

INIT_DIR = "/etc/rc.d/init.d"
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
        print("===============slemp cli tools=================")
        print("(1)      Restart panel service")
        print("(2)      Stop panel service")
        print("(3)      Launchpad service")
        print("(4)      Overload Panel Services")
        print("(5)      Modify panel ports")
        print("(10)     View panel default information")
        print("(11)     Change Panel Password")
        print("(12)     Modify Panel Username")
        print("(13)     Show Panel Error Log")
        print("(20)     Close BasicAuth authentication")
        print("(21)     Unbind the domain name")
        print("(100)    Enable PHP52 display")
        print("(101)    Turn off PHP52 display")
        print("(200)    Switching Linux System Software Sources")
        print("(201)    Simple speed test")
        print("(0)      Cancel")
        print(raw_tip)
        try:
            slemp_input = input("Please enter the order number：")
            if sys.version_info[0] == 3:
                slemp_input = int(slemp_input)
        except:
            slemp_input = 0

    nums = [1, 2, 3, 4, 5, 10, 11, 12, 13, 20, 21, 100, 101, 200, 201]
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
                in_port, 'SLEMP Panel [TOOLS modification]', 'port')
            slemp.writeFile('data/port.pl', in_port)
            os.system(INIT_CMD + " restart_panel")
            os.system(INIT_CMD + " default")
        else:
            print("|-The port range is between 0-65536")
        return
    elif slemp_input == 10:
        os.system(INIT_CMD + " default")
    elif slemp_input == 11:
        input_pwd = slemp_input_cmd("Please enter a new panel password：")
        if len(input_pwd.strip()) < 5:
            print("|-Error, the password length cannot be less than 5 characters")
            return
        set_panel_pwd(input_pwd.strip(), True)
    elif slemp_input == 12:
        input_user = slemp_input_cmd("Please enter a new panel username (>=5 digits)：")
        set_panel_username(input_user.strip())
    elif slemp_input == 13:
        os.system('tail -100 ' + slemp.getRunDir() + '/logs/error.log')
    elif slemp_input == 20:
        basic_auth = 'data/basic_auth.json'
        if os.path.exists(basic_auth):
            os.remove(basic_auth)
            os.system(INIT_CMD + " restart")
            print("|-Close basic_auth successfully")
    elif slemp_input == 21:
        bind_domain = 'data/bind_domain.pl'
        if os.path.exists(bind_domain):
            os.remove(bind_domain)
            os.system(INIT_CMD + " unbind_domain")
            print("|-Successfully unbind the domain name")
    elif slemp_input == 100:
        php_conf = 'plugins/php/info.json'
        if os.path.exists(php_conf):
            cont = slemp.readFile(php_conf)
            cont = re.sub("\"53\"", "\"52\",\"53\"", cont)
            cont = re.sub("\"5.3.29\"", "\"5.2.17\",\"5.3.29\"", cont)
            slemp.writeFile(php_conf, cont)
            print("|-Executing PHP52 shows success!")
    elif slemp_input == 101:
        php_conf = 'plugins/php/info.json'
        if os.path.exists(php_conf):
            cont = slemp.readFile(php_conf)
            cont = re.sub("\"52\",", "", cont)
            cont = re.sub("\"5.2.17\",", cont)
            slemp.writeFile(php_conf, cont)
            print("|-Execute PHP52 to hide success!")
    elif slemp_input == 200:
        os.system(INIT_CMD + " mirror")
    elif mw_input == 201:
        os.system('curl -Lso- bench.sh | bash')


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


def show_panel_pwd():
    import db
    sql = db.Sql()
    password = sql.table('users').where('id=?', (1,)).getField('password')

    file_pwd = ''
    if os.path.exists('data/default.pl'):
        file_pwd = slemp.readFile('data/default.pl').strip()

    if slemp.md5(file_pwd) == password:
        print('password: ' + file_pwd)
        return
    print("Password has been changed!")


def set_panel_username(username=None):
    import db
    sql = db.Sql()
    if username:
        if len(username) < 5:
            print("|-Error, username length cannot be less than 5 characters")
            return
        if username in ['admin', 'root']:
            print("|-Error, too simple a username cannot be used")
            return

        sql.table('users').where('id=?', (1,)).setField('username', username)
        print("|-New username: %s" % username)
        return

    username = sql.table('users').where('id=?', (1,)).getField('username')
    if username == 'admin':
        username = slemp.getRandomString(8).lower()
        sql.table('users').where('id=?', (1,)).setField('username', username)
    print('username: ' + username)


def getServerIp():
    version = sys.argv[2]
    ip = slemp.execShell(
        "curl --insecure -{} -sS --connect-timeout 5 -m 60 https://v6r.ipip.net/?format=text".format(version))
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
    elif method == 'password':
        show_panel_pwd()
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
