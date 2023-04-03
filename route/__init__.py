# coding:utf-8

import sys
import io
import os
import time
import shutil
import uuid
import json
import traceback
import socket

# reload(sys)
#  sys.setdefaultencoding('utf-8')
import paramiko
from datetime import timedelta

from flask import Flask
from flask import render_template
from flask import make_response
from flask import Response
from flask import session
from flask import request
from flask import redirect
from flask import url_for
from flask import render_template_string, abort
from flask_caching import Cache
from flask_session import Session


from whitenoise import WhiteNoise

sys.path.append(os.getcwd() + "/class/core")

import db
import slemp
import config_api

app = Flask(__name__, template_folder='templates/default')
app.config.version = config_api.config_api().getVersion()

app.wsgi_app = WhiteNoise(
    app.wsgi_app, root="route/static/", prefix="static/", max_age=604800)

cache = Cache(config={'CACHE_TYPE': 'simple'})
cache.init_app(app, config={'CACHE_TYPE': 'simple'})

try:
    from flask_sqlalchemy import SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/slemp_session.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    app.config['SESSION_TYPE'] = 'sqlalchemy'
    app.config['SESSION_SQLALCHEMY'] = sdb
    app.config['SESSION_SQLALCHEMY_TABLE'] = 'session'
    sdb = SQLAlchemy(app)
    sdb.create_all()
except:
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = '/tmp/py_slemp_session_' + \
        str(sys.version_info[0])
    app.config['SESSION_FILE_THRESHOLD'] = 1024
    app.config['SESSION_FILE_MODE'] = 384
    slemp.execShell("pip install flask_sqlalchemy &")

app.secret_key = uuid.UUID(int=uuid.getnode()).hex[-12:]
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'SLEMP_:'
app.config['SESSION_COOKIE_NAME'] = "SLEMP_VER_1"
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=31)

if slemp.isAppleSystem():
    app.config['DEBUG'] = True

# Session(app)

basic_auth_conf = 'data/basic_auth.json'
app.config['BASIC_AUTH_OPEN'] = False
if os.path.exists(basic_auth_conf):
    try:
        ba_conf = json.loads(slemp.readFile(basic_auth_conf))
        # print(ba_conf)
        app.config['BASIC_AUTH_USERNAME'] = ba_conf['basic_user']
        app.config['BASIC_AUTH_PASSWORD'] = ba_conf['basic_pwd']
        app.config['BASIC_AUTH_OPEN'] = ba_conf['open']
        app.config['BASIC_AUTH_FORCE'] = True
    except Exception as e:
        print(e)

# socketio
from flask_socketio import SocketIO, emit, send
socketio = SocketIO()
socketio.init_app(app)

# sockets
from flask_sockets import Sockets
sockets = Sockets(app)

# from gevent.pywsgi import WSGIServer
# from geventwebsocket.handler import WebSocketHandler
# http_server = WSGIServer(('0.0.0.0', '7200'), app,
#                          handler_class=WebSocketHandler)
# http_server.serve_forever()

# debug macosx dev
if slemp.isDebugMode():
    app.debug = True
    app.config.version = app.config.version + str(time.time())

import common
common.init()


# ----------  error function start -----------------
def getErrorNum(key, limit=None):
    key = slemp.md5(key)
    num = cache.get(key)
    if not num:
        num = 0
    if not limit:
        return num
    if limit > num:
        return True
    return False


def setErrorNum(key, empty=False, expire=3600):
    key = slemp.md5(key)
    num = cache.get(key)
    if not num:
        num = 0
    else:
        if empty:
            cache.delete(key)
            return True
    cache.set(key, num + 1, expire)
    return True
# ----------  error function end -----------------


def funConvert(fun):
    block = fun.split('_')
    func = block[0]
    for x in range(len(block) - 1):
        suf = block[x + 1].title()
        func += suf
    return func


def sendAuthenticated():
    request_host = slemp.getHostAddr()
    result = Response(
        '', 401, {'WWW-Authenticate': 'Basic realm="%s"' % request_host.strip()})
    if not 'login' in session and not 'admin_auth' in session:
        session.clear()
    return result


@app.before_request
def requestCheck():
    if app.config['BASIC_AUTH_OPEN']:
        auth = request.authorization
        if request.path in ['/download', '/hook', '/down']:
            return

        if not auth:
            return sendAuthenticated()
        salt = '_md_salt'
        if slemp.md5(auth.username.strip() + salt) != app.config['BASIC_AUTH_USERNAME'] \
                or slemp.md5(auth.password.strip() + salt) != app.config['BASIC_AUTH_PASSWORD']:
            return sendAuthenticated()

    domain_check = slemp.checkDomainPanel()
    if domain_check:
        return domain_check


def isLogined():
    if 'login' in session and 'username' in session and session['login'] == True:
        userInfo = slemp.M('users').where(
            "id=?", (1,)).field('id,username,password').find()
        # print(userInfo)
        if userInfo['username'] != session['username']:
            return False

        now_time = int(time.time())

        if 'overdue' in session and now_time > session['overdue']:
            session['overdue'] = int(time.time()) + 7 * 24 * 60 * 60
            return False

        if 'tmp_login_expire' in session and now_time > int(session['tmp_login_expire']):
            session.clear()
            return False

        return True

    # if os.path.exists('data/api_login.txt'):
    #     content = slemp.readFile('data/api_login.txt')
    #     session['login'] = True
    #     session['username'] = content
    #     os.remove('data/api_login.txt')
    return False


def publicObject(toObject, func, action=None, get=None):
    name = funConvert(func) + 'Api'
    try:
        if hasattr(toObject, name):
            efunc = 'toObject.' + name + '()'
            data = eval(efunc)
            return data
        data = {'msg': '404,not find api[' + name + ']', "status": False}
        return slemp.getJson(data)
    except Exception as e:
        if slemp.isDebugMode():
            print(traceback.print_exc())
        data = {'msg': 'Access exception:' + str(e) + '!', "status": False}
        return slemp.getJson(data)


# @app.route("/debug")
# def debug():
#     print(sys.version_info)
#     print(session)
#     os = slemp.getOs()
#     print(os)
#     return slemp.getLocalIp()

@app.route("/.well-known/acme-challenge/<val>")
def wellknow(val=None):
    f = slemp.getRunDir() + "/tmp/.well-known/acme-challenge/" + val
    if os.path.exists(f):
        return slemp.readFile(f)
    return ''


@app.route("/hook", methods=['POST', 'GET'])
def webhook():
    input_args = {
        'access_key': request.args.get('access_key', '').strip(),
        'params': request.args.get('params', '').strip()
    }

    if request.method == 'POST':
        input_args = {
            'access_key': request.form.get('access_key', '').strip(),
            'params': request.form.get('params', '').strip()
        }

    wh_install_path = slemp.getServerDir() + '/webhook'
    if not os.path.exists(wh_install_path):
        return slemp.returnJson(False, 'Please install the WebHook plugin first!')

    sys.path.append('plugins/webhook')
    import index
    return index.runShellArgs(input_args)


@app.route('/close')
def close():
    if not os.path.exists('data/close.pl'):
        return redirect('/')
    data = {}
    data['cmd'] = 'rm -rf ' + slemp.getRunDir() + '/data/close.pl'
    return render_template('close.html', data=data)


@app.route("/code")
def code():
    import vilidate
    vie = vilidate.vieCode()
    codeImage = vie.GetCodeImage(80, 4)
    # try:
    #     from cStringIO import StringIO
    # except:
    #     from StringIO import StringIO

    out = io.BytesIO()
    codeImage[0].save(out, "png")

    # print(codeImage[1])

    session['code'] = slemp.md5(''.join(codeImage[1]).lower())

    img = Response(out.getvalue(), headers={'Content-Type': 'image/png'})
    return make_response(img)


@app.route("/check_login", methods=['POST'])
def checkLogin():
    if isLogined():
        return "true"
    return "false"


@app.route("/do_login", methods=['POST'])
def doLogin():
    login_cache_count = 5
    login_cache_limit = cache.get('login_cache_limit')

    filename = 'data/close.pl'
    if os.path.exists(filename):
        return slemp.returnJson(False, 'Panel is closed!')

    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    code = request.form.get('code', '').strip()
    # print(session)
    if 'code' in session:
        if session['code'] != slemp.md5(code):
            if login_cache_limit == None:
                login_cache_limit = 1
            else:
                login_cache_limit = int(login_cache_limit) + 1

            if login_cache_limit >= login_cache_count:
                slemp.writeFile(filename, 'True')
                return slemp.returnJson(False, 'Panel is closed!')

            cache.set('login_cache_limit', login_cache_limit, timeout=10000)
            login_cache_limit = cache.get('login_cache_limit')
            code_msg = slemp.getInfo("The verification code is wrong, you can try [{1}] more times!", (str(
                login_cache_count - login_cache_limit)))
            slemp.writeLog('User login', code_msg)
            return slemp.returnJson(False, code_msg)

    userInfo = slemp.M('users').where(
        "id=?", (1,)).field('id,username,password').find()

    # print(userInfo)
    # print(password)
    password = slemp.md5(password)
    # print('md5-pass', password)

    if userInfo['username'] != username or userInfo['password'] != password:
        msg = "<a style='color: red'>Password error</a>, account: {1}, password: {2}, login IP: {3}", ((
            '****', '******', request.remote_addr))

        if login_cache_limit == None:
            login_cache_limit = 1
        else:
            login_cache_limit = int(login_cache_limit) + 1

        if login_cache_limit >= login_cache_count:
            slemp.writeFile(filename, 'True')
            return slemp.returnJson(False, 'Panel is closed!')

        cache.set('login_cache_limit', login_cache_limit, timeout=10000)
        login_cache_limit = cache.get('login_cache_limit')
        slemp.writeLog('User login', slemp.getInfo(msg))
        return slemp.returnJson(False, slemp.getInfo("Username or password is wrong, you can try [{1}] more times!", (str(login_cache_count - login_cache_limit))))

    cache.delete('login_cache_limit')
    session['login'] = True
    session['username'] = userInfo['username']
    session['overdue'] = int(time.time()) + 7 * 24 * 60 * 60
    # session['overdue'] = int(time.time()) + 7

    # slemp.writeFile('data/api_login.txt', userInfo['username'])
    return slemp.returnJson(True, 'Login successful, jumping...')


@app.errorhandler(404)
def page_unauthorized(error):
    return render_template_string('404 not found', error_info=error), 404


def get_admin_safe():
    path = 'data/admin_path.pl'
    if os.path.exists(path):
        cont = slemp.readFile(path)
        cont = cont.strip().strip('/')
        return (True, cont)
    return (False, '')


def admin_safe_path(path, req, data, pageFile):
    if path != req and not isLogined():
        if data['status_code'] == '0':
            return render_template('path.html')
        else:
            return Response(status=int(data['status_code']))

    if not isLogined():
        return render_template('login.html', data=data)

    if not req in pageFile:
        return redirect('/')

    return render_template(req + '.html', data=data)


def login_temp_user(token):
    if len(token) != 48:
        return 'Wrong parameter!'

    skey = slemp.getClientIp() + '_temp_login'
    if not getErrorNum(skey, 10):
        return '10 consecutive authentication failures, ban for 1 hour'

    stime = int(time.time())
    data = slemp.M('temp_login').where('state=? and expire>?',
                                    (0, stime)).field('id,token,salt,expire,addtime').find()
    if not data:
        setErrorNum(skey)
        return 'Verification failed!'

    if stime > int(data['expire']):
        setErrorNum(skey)
        return "Expired"

    r_token = slemp.md5(token + data['salt'])
    if r_token != data['token']:
        setErrorNum(skey)
        return 'Verification failed!'

    userInfo = slemp.M('users').where(
        "id=?", (1,)).field('id,username').find()
    session['login'] = True
    session['username'] = userInfo['username']
    session['tmp_login'] = True
    session['tmp_login_id'] = str(data['id'])
    session['tmp_login_expire'] = int(data['expire'])
    session['uid'] = data['id']

    login_addr = slemp.getClientIp() + ":" + str(request.environ.get('REMOTE_PORT'))
    slemp.writeLog('User login', "Successful login, account: {1}, login IP: {2}",
                (userInfo['username'], login_addr))
    slemp.M('temp_login').where('id=?', (data['id'],)).update(
        {"login_time": stime, 'state': 1, 'login_addr': login_addr})

    # print(session)
    return redirect('/')


@app.route('/api/<reqClass>/<reqAction>', methods=['POST', 'GET'])
def api(reqClass=None, reqAction=None, reqData=None):
    comReturn = common.local()
    if comReturn:
        return comReturn

    import config_api
    isOk, data = config_api.config_api().checkPanelToken()
    if not isOk:
        return slemp.returnJson(False, 'API is not enabled')

    request_time = request.form.get('request_time', '')
    request_token = request.form.get('request_token', '')
    request_ip = request.remote_addr
    request_ip = request_ip.replace('::ffff:', '')

    # print(request_time, request_token)
    if not slemp.inArray(data['limit_addr'], request_ip):
        return slemp.returnJson(False, 'IP verification failed, your access IP is [' + request_ip + ']')

    local_token = slemp.deCrypt(data['token'], data['token_crypt'])
    token_md5 = slemp.md5(str(request_time) + slemp.md5(local_token))

    if not (token_md5 == request_token):
        return slemp.returnJson(False, 'Wrong key')

    if reqClass == None:
        return slemp.returnJson(False, 'Please specify the request method class')

    if reqAction == None:
        return slemp.returnJson(False, 'Please specify the request method')

    classFile = ('config_api', 'crontab_api', 'files_api', 'firewall_api',
                 'plugins_api', 'system_api', 'site_api', 'task_api')
    className = reqClass + '_api'
    if not className in classFile:
        return slemp.returnJson(False, 'external api request error')

    eval_str = "__import__('" + className + "')." + className + '()'
    newInstance = eval(eval_str)

    try:
        return publicObject(newInstance, reqAction)
    except Exception as e:
        return slemp.getTracebackInfo()


@app.route('/<reqClass>/<reqAction>', methods=['POST', 'GET'])
@app.route('/<reqClass>/', methods=['POST', 'GET'])
@app.route('/<reqClass>', methods=['POST', 'GET'])
@app.route('/', methods=['POST', 'GET'])
def index(reqClass=None, reqAction=None, reqData=None):

    comReturn = common.local()
    if comReturn:
        return comReturn

    if reqAction == None:
        import config_api
        data = config_api.config_api().get()

        if reqClass == None:
            reqClass = 'index'

        pageFile = ('config', 'control', 'crontab', 'files', 'firewall',
                    'index', 'plugins', 'login', 'system', 'site', 'cert', 'ssl', 'task', 'soft')

        if reqClass == 'login':
            token = request.args.get('tmp_token', '').strip()
            if token != '':
                return login_temp_user(token)

        ainfo = get_admin_safe()

        if reqClass == 'login':

            signout = request.args.get('signout', '')
            if signout == 'True':
                session.clear()
                session['login'] = False
                session['overdue'] = 0

            if ainfo[0]:
                return admin_safe_path(ainfo[1], reqClass, data, pageFile)

            return render_template('login.html', data=data)

        if ainfo[0]:
            return admin_safe_path(ainfo[1], reqClass, data, pageFile)

        if not reqClass in pageFile:
            return redirect('/')

        if not isLogined():
            return redirect('/login')

        return render_template(reqClass + '.html', data=data)

    if not isLogined():
        return 'error request!'

    classFile = ('config_api', 'crontab_api', 'files_api', 'firewall_api',
                 'plugins_api', 'system_api', 'site_api', 'task_api')
    className = reqClass + '_api'
    if not className in classFile:
        return "api error request"

    eval_str = "__import__('" + className + "')." + className + '()'
    newInstance = eval(eval_str)

    return publicObject(newInstance, reqAction)


##################### ssh  start ###########################
shell = None
shell_client = None


@socketio.on('webssh_websocketio')
def webssh_websocketio(data):
    if not isLogined():
        emit('server_response', {'data': 'Session lost, please log in to the panel again!\r\n'})
        return

    global shell_client
    if not shell_client:
        import ssh_terminal
        shell_client = ssh_terminal.ssh_terminal()

    shell_client.run(request.sid, data)
    return


@socketio.on('webssh')
def webssh(msg):
    global shell
    if not isLogined():
        emit('server_response', {'data': 'Session lost, please log in to the panel again!\r\n'})
        return None

    if not shell:
        shell = slemp.connectSsh()

    if shell.exit_status_ready():
        shell = slemp.connectSsh()

    if shell:
        shell.send(msg)
        try:
            time.sleep(0.005)
            recv = shell.recv(4096)
            emit('server_response', {'data': recv.decode("utf-8")})
        except Exception as ex:
            emit('server_response', {'data': str(ex)})

##################### ssh  end ###########################
