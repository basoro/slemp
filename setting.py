# coding:utf-8

import time
import sys
import random
import os
chdir = os.getcwd()
sys.path.append(chdir + '/class/core')

import slemp

import system_api
cpu_info = system_api.system_api().getCpuInfo()
workers = cpu_info[1]


log_dir = os.getcwd() + '/logs'
if not os.path.exists(log_dir):
    os.mkdir(log_dir)

# default port
slemp_port = "7200"
if os.path.exists("data/port.pl"):
    slemp_port = slemp.readFile('data/port.pl')
    slemp_port.strip()
else:
    import firewall_api
    import common
    common.initDB()
    slemp_port = str(random.randint(10000, 65530))
    firewall_api.firewall_api().addAcceptPortArgs(slemp_port, 'WEB panel', 'port')
    slemp.writeFile('data/port.pl', slemp_port)

bind = []
if os.path.exists('data/ipv6.pl'):
    bind.append('[0:0:0:0:0:0:0:0]:%s' % slemp_port)
else:
    bind.append('0.0.0.0:%s' % slemp_port)

if workers > 2:
    workers = 2

threads = workers * 1
backlog = 512
reload = False
daemon = True
worker_class = 'geventwebsocket.gunicorn.workers.GeventWebSocketWorker'
timeout = 7200
keepalive = 60
preload_app = True
capture_output = True
access_log_format = '%(t)s %(p)s %(h)s "%(r)s" %(s)s %(L)s %(b)s %(f)s" "%(a)s"'
loglevel = 'info'
errorlog = log_dir + '/error.log'
accesslog = log_dir + '/access.log'
pidfile = log_dir + '/slemp.pid'
if os.path.exists(os.getcwd() + '/data/ssl.pl'):
    certfile = 'ssl/certificate.pem'
    keyfile = 'ssl/privateKey.pem'
