# coding:utf-8

import sys
import os
import time
import re
import json
import subprocess

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + "/class/core")
import slemp


app_debug = False
if slemp.isAppleSystem():
    app_debug = True


def getPluginName():
    return 'ollama'


def getPluginDir():
    return slemp.getPluginDir() + '/' + getPluginName()


def getSPluginDir():
    return slemp.getPluginDir() + '/' + getPluginName()


def getServerDir():
    return slemp.getServerDir() + '/' + getPluginName()


def getInitDFile():
    if app_debug:
        return '/tmp/' + getPluginName()
    return '/etc/init.d/' + getPluginName()


def getArgs():
    args = sys.argv[2:]
    tmp = {}
    args_len = len(args)

    # Handle URL-encoded string like 'port=8080'
    if args_len == 1:
        arg = args[0].strip()
        if arg.find('=') != -1:
            # URL-encoded format: port=8080
            parts = arg.split('&')
            for part in parts:
                kv = part.split('=', 1)
                if len(kv) == 2:
                    tmp[kv[0]] = kv[1]
            return tmp
        elif arg.startswith('{'):
            # JSON format
            try:
                return json.loads(arg)
            except:
                pass

    # Handle CLI-style arguments
    if args_len == 1:
        t = args[0].strip('{').strip('}')
        if t.strip() == '':
            tmp = []
        else:
            t = t.split(':', 1)
            if len(t) >= 2:
                tmp[t[0]] = t[1]
    elif args_len > 1:
        for i in range(len(args)):
            t = args[i].split(':', 1)
            if len(t) >= 2:
                tmp[t[0]] = t[1]
    return tmp


def checkArgs(data, ck=[]):
    for i in range(len(ck)):
        if not ck[i] in data:
            return (False, slemp.returnJson(False, 'Parameter: (' + ck[i] + ') tidak ditemukan!'))
    return (True, slemp.returnJson(True, 'ok'))


def contentReplace(content):
    service_path = slemp.getServerDir()
    content = content.replace('{$ROOT_PATH}', slemp.getRootDir())
    content = content.replace('{$SERVER_PATH}', service_path)
    return content


def status():
    cmd = "ps -ef|grep " + getPluginName() + " |grep -v grep | grep -v python | awk '{print $2}'"
    data = slemp.execShell(cmd)
    if data[0] == '':
        return 'stop'
    return 'start'


def initDreplace():
    initd_path = getServerDir() + '/init.d'
    if not os.path.exists(initd_path):
        os.mkdir(initd_path)

    file_bin = initd_path + '/' + getPluginName()
    if not os.path.exists(file_bin):
        tpl = getPluginDir() + '/init.d/' + getPluginName() + '.tpl'
        if not os.path.exists(tpl):
            return file_bin
        content = slemp.readFile(tpl)
        content = contentReplace(content)
        slemp.writeFile(file_bin, content)
        slemp.execShell('chmod +x ' + file_bin)

    # systemd
    system_dir = slemp.systemdCfgDir()
    service = system_dir + '/' + getPluginName() + '.service'
    if os.path.exists(system_dir) and not os.path.exists(service):
        tpl = getPluginDir() + '/init.d/' + getPluginName() + '.service.tpl'
        if os.path.exists(tpl):
            content = slemp.readFile(tpl)
            content = contentReplace(content)
            slemp.writeFile(service, content)
            slemp.execShell('systemctl daemon-reload')

    return file_bin


def start():
    return appOp('start')


def stop():
    return appOp('stop')


def restart():
    return appOp('restart')


def reload():
    return appOp('reload')


def appOp(method):
    init_file = initDreplace()
    if not slemp.isAppleSystem():
        cmd = 'systemctl {} {}'.format(method, getPluginName())
        data = slemp.execShell(cmd)
        if data[1] == '':
            return 'ok'
        return 'fail'

    data = slemp.execShell(init_file + ' ' + method)
    if data[1] == '':
        return 'ok'
    return data[0]


def initdStatus():
    if slemp.isAppleSystem():
        return 'ok'

    shell_cmd = 'systemctl status ' + getPluginName() + ' | grep loaded | grep "enabled;"'
    data = slemp.execShell(shell_cmd)
    if data[0] == '':
        return 'fail'
    return 'ok'


def initdInstall():
    if slemp.isAppleSystem():
        return 'ok'

    slemp.execShell('systemctl enable ' + getPluginName())
    return 'ok'


def initdUninstall():
    if slemp.isAppleSystem():
        return 'ok'

    slemp.execShell('systemctl disable ' + getPluginName())
    return 'ok'


def getTotalStatistics():
    st = status()
    data = {}

    is_install = os.path.exists(getServerDir() + '/version.pl')

    if st == 'start' and is_install:
        data['status'] = True
        data['ver'] = slemp.readFile(getServerDir() + '/version.pl').strip()
        return slemp.returnJson(True, 'ok', data)
    else:
        data['status'] = False
        return slemp.returnJson(False, 'fail', data)


# ==================== OpenWebUI Functions ====================

def getOpenWebUIConfig():
    """Membaca konfigurasi OpenWebUI dari file config.json"""
    config_path = getServerDir() + '/config.json'
    if os.path.exists(config_path):
        try:
            data = slemp.readFile(config_path)
            return json.loads(data)
        except:
            pass
    return {
        'port': 8080
    }


def setOpenWebUIConfig(config):
    """Menyimpan konfigurasi OpenWebUI ke file config.json"""
    config_path = getServerDir() + '/config.json'
    try:
        slemp.writeFile(config_path, json.dumps(config))
        return True
    except:
        return False


def initOpenWebUIConfig():
    """Inisialisasi konfigurasi default OpenWebUI"""
    config_path = getServerDir() + '/config.json'
    if not os.path.exists(config_path):
        default_config = {
            'port': 8080
        }
        setOpenWebUIConfig(default_config)
    return getOpenWebUIConfig()


def getOpenWebUIPort():
    """Mendapatkan port OpenWebUI dari konfigurasi"""
    config = getOpenWebUIConfig()
    return config.get('port', 8080)


def getOpenWebUIServerRoot():
    return slemp.getServerDir()


def getOpenWebUIPanelRoot():
    return os.path.dirname(slemp.getPluginDir())


def getOpenWebUIVenvDir():
    return getServerDir() + '/openwebui'


def getOpenWebUIVenvPython():
    return getOpenWebUIVenvDir() + '/bin/python'


def getOpenWebUIVenvCli():
    return getOpenWebUIVenvDir() + '/bin/open-webui'


def getOpenWebUIInstallStateFile():
    return getServerDir() + '/openwebui_install.json'


def getOpenWebUIInstallLogFile():
    return getServerDir() + '/openwebui_install.log'


def checkPythonVersion():
    """Memeriksa apakah Python version >= 3.11"""
    version = sys.version_info
    return version.major >= 3 and version.minor >= 11


def useOpenWebUIVenv():
    return not checkPythonVersion()


def findPython311():
    python_bins = [
        '/usr/bin/python3.11',
        '/usr/local/bin/python3.11',
        '/opt/homebrew/bin/python3.11'
    ]
    for python_bin in python_bins:
        if os.path.exists(python_bin):
            return python_bin

    result = slemp.execShell('command -v python3.11')
    if result[0].strip() != '':
        return result[0].strip()
    return ''


def getOpenWebUIInstallCommands():
    if useOpenWebUIVenv():
        return [
            'cd ' + getOpenWebUIPanelRoot(),
            'python3.11 -m venv ../ollama/openwebui',
            'source ../ollama/openwebui/bin/activate',
            'pip install -U open-webui'
        ]
    return ['pip install -U open-webui']


def getOpenWebUIStartCommands(port):
    if useOpenWebUIVenv():
        return [
            'cd ' + getOpenWebUIPanelRoot(),
            'source ../ollama/openwebui/bin/activate',
            'open-webui serve --port ' + str(port)
        ]
    return ['open-webui serve --port ' + str(port)]


def tailOpenWebUILog(line_count=20):
    log_file = getOpenWebUIInstallLogFile()
    if not os.path.exists(log_file):
        return ''

    content = slemp.readFile(log_file)
    lines = content.splitlines()
    return '\n'.join(lines[-line_count:])


def writeOpenWebUIInstallState(status, percent, msg, pid=0):
    data = {
        'status': status,
        'percent': percent,
        'msg': msg,
        'pid': pid,
        'env_mode': 'venv' if useOpenWebUIVenv() else 'system',
        'log_file': getOpenWebUIInstallLogFile(),
        'update_time': int(time.time())
    }
    if not os.path.exists(getServerDir()):
        os.makedirs(getServerDir())
    slemp.writeFile(getOpenWebUIInstallStateFile(), json.dumps(data))
    return data


def readOpenWebUIInstallState():
    state_file = getOpenWebUIInstallStateFile()
    if not os.path.exists(state_file):
        return {
            'status': 'idle',
            'percent': 0,
            'msg': 'Belum ada proses instalasi OpenWebUI.',
            'env_mode': 'venv' if useOpenWebUIVenv() else 'system',
            'log_file': getOpenWebUIInstallLogFile(),
            'update_time': int(time.time())
        }

    try:
        data = json.loads(slemp.readFile(state_file))
    except Exception:
        data = {
            'status': 'failed',
            'percent': 0,
            'msg': 'Status instalasi OpenWebUI tidak dapat dibaca.'
        }

    data['log'] = tailOpenWebUILog()
    return data


def appendOpenWebUIInstallLog(message):
    log_file = getOpenWebUIInstallLogFile()
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    with open(log_file, 'a') as fp:
        fp.write(message + '\n')


def resetOpenWebUIInstallLog():
    log_file = getOpenWebUIInstallLogFile()
    if os.path.exists(log_file):
        os.remove(log_file)


def runOpenWebUIInstallCommand(command, progress, message):
    writeOpenWebUIInstallState('running', progress, message)
    appendOpenWebUIInstallLog('$ ' + ' '.join(command))

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break
        if line:
            appendOpenWebUIInstallLog(line.rstrip())

    code = process.wait()
    if code != 0:
        raise Exception('Perintah gagal dijalankan: ' + ' '.join(command))


def checkOpenWebUIPipInstalled():
    """Memeriksa apakah OpenWebUI terinstal via pip"""
    result = slemp.execShell('"{}" -m pip show open-webui'.format(sys.executable))
    if result[1] != '' and 'not found' in result[1].lower():
        return False
    return result[0] != ''


def checkOpenWebUIInstalled():
    if useOpenWebUIVenv():
        return os.path.exists(getOpenWebUIVenvCli())
    return checkOpenWebUIPipInstalled()


def openwebuiInstallProgress():
    state = readOpenWebUIInstallState()
    return slemp.returnJson(state.get('status') != 'failed', state.get('msg', 'ok'), state)


def openwebuiInstallWorker():
    try:
        resetOpenWebUIInstallLog()
        writeOpenWebUIInstallState('running', 5, 'Memeriksa lingkungan OpenWebUI...')
        appendOpenWebUIInstallLog('Memulai instalasi OpenWebUI...')

        if checkOpenWebUIInstalled():
            appendOpenWebUIInstallLog('OpenWebUI sudah tersedia, proses instalasi dilewati.')
            writeOpenWebUIInstallState('success', 100, 'OpenWebUI sudah terinstal.')
            return 'ok'

        if useOpenWebUIVenv():
            python311 = findPython311()
            if python311 == '':
                writeOpenWebUIInstallState('failed', 0, 'python3.11 tidak ditemukan untuk membuat virtualenv OpenWebUI.')
                appendOpenWebUIInstallLog('python3.11 tidak ditemukan.')
                return 'fail'

            if not os.path.exists(getServerDir()):
                os.makedirs(getServerDir())

            if not os.path.exists(getOpenWebUIVenvDir()):
                runOpenWebUIInstallCommand(
                    [python311, '-m', 'venv', getOpenWebUIVenvDir()],
                    25,
                    'Membuat virtualenv OpenWebUI di server/ollama/openwebui...'
                )
            else:
                writeOpenWebUIInstallState('running', 25, 'Virtualenv OpenWebUI sudah ada, lanjut instalasi paket...')
                appendOpenWebUIInstallLog('Virtualenv sudah ada di ' + getOpenWebUIVenvDir())

            runOpenWebUIInstallCommand(
                [getOpenWebUIVenvPython(), '-m', 'pip', 'install', '-U', 'open-webui'],
                70,
                'Menginstal paket OpenWebUI ke virtualenv server/ollama/openwebui...'
            )
        else:
            runOpenWebUIInstallCommand(
                [sys.executable, '-m', 'pip', 'install', '-U', 'open-webui'],
                70,
                'Menginstal paket OpenWebUI ke Python sistem...'
            )

        writeOpenWebUIInstallState('running', 90, 'Memverifikasi hasil instalasi OpenWebUI...')
        appendOpenWebUIInstallLog('Memverifikasi instalasi OpenWebUI...')

        if not checkOpenWebUIInstalled():
            writeOpenWebUIInstallState('failed', 90, 'OpenWebUI gagal diverifikasi setelah instalasi.')
            appendOpenWebUIInstallLog('Verifikasi gagal: binary OpenWebUI tidak ditemukan.')
            return 'fail'

        if useOpenWebUIVenv():
            writeOpenWebUIInstallState('success', 100, 'OpenWebUI berhasil diinstal pada virtualenv server/ollama/openwebui.')
            appendOpenWebUIInstallLog('Instalasi selesai pada virtualenv server/ollama/openwebui.')
        else:
            writeOpenWebUIInstallState('success', 100, 'OpenWebUI berhasil diinstal pada Python sistem.')
            appendOpenWebUIInstallLog('Instalasi selesai pada Python sistem.')
        return 'ok'
    except Exception as e:
        appendOpenWebUIInstallLog('ERROR: ' + str(e))
        writeOpenWebUIInstallState('failed', 0, 'Gagal menginstal OpenWebUI: ' + str(e))
        return 'fail'


def checkOpenWebUIPipRunning():
    """Memeriksa apakah OpenWebUI sedang berjalan via pip"""
    result = slemp.execShell('ps -ef|grep "open-webui serve" |grep -v grep')
    return result[0] != ''


def openwebuiStatus():
    """Mendapatkan status OpenWebUI"""
    initOpenWebUIConfig()
    port = getOpenWebUIPort()
    result_data = {
        'port': port,
        'env_mode': 'venv' if useOpenWebUIVenv() else 'system',
        'install_cmds': getOpenWebUIInstallCommands(),
        'start_cmds': getOpenWebUIStartCommands(port)
    }

    if useOpenWebUIVenv() and findPython311() == '' and not checkOpenWebUIInstalled():
        result_data['status'] = 'python_not_supported'
        return slemp.returnJson(False, 'Python panel belum mendukung OpenWebUI. Siapkan python3.11 untuk virtualenv.', result_data)

    if checkOpenWebUIInstalled():
        if checkOpenWebUIPipRunning():
            result_data['status'] = 'running'
            return slemp.returnJson(True, 'OpenWebUI sedang berjalan', result_data)
        else:
            result_data['status'] = 'stopped'
            return slemp.returnJson(False, 'OpenWebUI belum dijalankan', result_data)
    else:
        result_data['status'] = 'not_installed'
        return slemp.returnJson(False, 'OpenWebUI belum diinstal', result_data)


def openwebuiInstall():
    """Menginstal OpenWebUI via pip"""
    if checkOpenWebUIInstalled():
        if useOpenWebUIVenv():
            return slemp.returnJson(True, 'OpenWebUI sudah terinstal pada virtualenv server/ollama/openwebui.', {
                'status': 'installed',
                'env_mode': 'venv'
            })
        return slemp.returnJson(True, 'OpenWebUI sudah terinstal pada Python sistem.', {
            'status': 'installed',
            'env_mode': 'system'
        })

    if useOpenWebUIVenv():
        python311 = findPython311()
        if python311 == '':
            return slemp.returnJson(False, 'python3.11 tidak ditemukan. Gunakan perintah manual yang ditampilkan di panel.', {
                'status': 'python_not_supported',
                'install_cmds': getOpenWebUIInstallCommands(),
                'env_mode': 'venv'
            })

    writeOpenWebUIInstallState('running', 1, 'Menyiapkan proses instalasi OpenWebUI...')
    install_cmd = 'nohup "{}" "{}" openwebui_install_worker > /dev/null 2>&1 & echo $!'.format(
        sys.executable, os.path.realpath(__file__))
    result = slemp.execShell(install_cmd)
    pid = 0
    try:
        pid = int(result[0].strip().split('\n')[-1])
    except Exception:
        pid = 0
    writeOpenWebUIInstallState('running', 3, 'Proses instalasi OpenWebUI dimulai...', pid)
    return slemp.returnJson(True, 'Instalasi OpenWebUI dimulai.', {
        'status': 'running',
        'pid': pid,
        'installing': True,
        'env_mode': 'venv' if useOpenWebUIVenv() else 'system'
    })


def openwebuiStart():
    """Memulai OpenWebUI"""
    initOpenWebUIConfig()
    port = getOpenWebUIPort()

    if not checkOpenWebUIInstalled():
        return slemp.returnJson(False, 'OpenWebUI belum terinstal')

    if checkOpenWebUIPipRunning():
        return slemp.returnJson(True, 'OpenWebUI sudah berjalan', {'status': 'running'})

    if useOpenWebUIVenv():
        cmd = 'cd "{}" && nohup "{}" serve --port {} > /tmp/openwebui.log 2>&1 &'.format(
            getOpenWebUIServerRoot(), getOpenWebUIVenvCli(), port)
    else:
        cmd = 'nohup open-webui serve --port {} > /tmp/openwebui.log 2>&1 &'.format(port)
    slemp.execShell(cmd)

    time.sleep(3)

    if checkOpenWebUIPipRunning():
        return slemp.returnJson(True, 'OpenWebUI berhasil dimulai. Akses di http://localhost:' + str(port), {'status': 'running', 'port': port})

    return slemp.returnJson(False, 'Gagal memulai OpenWebUI. Cek log di /tmp/openwebui.log', {'status': 'failed'})


def openwebuiStop():
    """Menghentikan OpenWebUI"""
    if not checkOpenWebUIPipInstalled():
        return slemp.returnJson(False, 'OpenWebUI belum terinstal')

    if not checkOpenWebUIPipRunning():
        return slemp.returnJson(True, 'OpenWebUI tidak sedang berjalan', {'status': 'stopped'})

    # Kill process
    slemp.execShell('pkill -f "open-webui serve"')

    return slemp.returnJson(True, 'OpenWebUI berhasil dihentikan', {'status': 'stopped'})


def openwebuiRestart():
    """Merestart OpenWebUI"""
    initOpenWebUIConfig()
    port = getOpenWebUIPort()

    if not checkOpenWebUIInstalled():
        return slemp.returnJson(False, 'OpenWebUI belum terinstal')

    # Stop
    if checkOpenWebUIPipRunning():
        slemp.execShell('pkill -f "open-webui serve"')

    time.sleep(1)

    if useOpenWebUIVenv():
        cmd = 'cd "{}" && nohup "{}" serve --port {} > /tmp/openwebui.log 2>&1 &'.format(
            getOpenWebUIServerRoot(), getOpenWebUIVenvCli(), port)
    else:
        cmd = 'nohup open-webui serve --port {} > /tmp/openwebui.log 2>&1 &'.format(port)
    slemp.execShell(cmd)

    time.sleep(3)

    if checkOpenWebUIPipRunning():
        return slemp.returnJson(True, 'OpenWebUI berhasil direstart', {'status': 'running', 'port': port})

    return slemp.returnJson(False, 'Gagal merestart OpenWebUI. Cek log di /tmp/openwebui.log', {'status': 'failed'})


def openwebuiUninstall():
    """Menghapus OpenWebUI"""
    if not checkOpenWebUIInstalled():
        return slemp.returnJson(False, 'OpenWebUI belum terinstal')

    # Stop jika sedang berjalan
    if checkOpenWebUIPipRunning():
        slemp.execShell('pkill -f "open-webui serve"')

    if useOpenWebUIVenv():
        slemp.execShell('rm -rf "{}"'.format(getOpenWebUIVenvDir()))
        if os.path.exists(getOpenWebUIVenvDir()):
            return slemp.returnJson(False, 'Gagal menghapus virtualenv OpenWebUI')
    else:
        result = slemp.execShell('"{}" -m pip uninstall open-webui -y'.format(sys.executable))
        if result[1] != '' and 'error' in result[1].lower():
            return slemp.returnJson(False, 'Gagal menghapus OpenWebUI: ' + result[1])

    return slemp.returnJson(True, 'OpenWebUI berhasil dihapus', {'status': 'uninstalled'})


def openwebuiPort():
    """Mendapatkan port OpenWebUI dari konfigurasi"""
    initOpenWebUIConfig()
    port = getOpenWebUIPort()
    return slemp.returnJson(True, 'ok', {'port': port})


def openwebuiSetPort():
    """Mengatur port OpenWebUI"""
    args = getArgs()

    if 'port' not in args:
        return slemp.returnJson(False, 'Parameter port tidak ditemukan')

    try:
        new_port = int(args['port'])
    except:
        return slemp.returnJson(False, 'Port harus berupa angka')

    if new_port < 1 or new_port > 65535:
        return slemp.returnJson(False, 'Port harus antara 1 dan 65535')

    config = getOpenWebUIConfig()
    config['port'] = new_port

    if setOpenWebUIConfig(config):
        return slemp.returnJson(True, 'Port berhasil diubah ke ' + str(new_port), {'port': new_port})

    return slemp.returnJson(False, 'Gagal menyimpan konfigurasi port')


def openwebuiGetConfig():
    """Mendapatkan semua konfigurasi OpenWebUI"""
    initOpenWebUIConfig()
    config = getOpenWebUIConfig()
    return slemp.returnJson(True, 'ok', config)


if __name__ == "__main__":
    func = sys.argv[1]

    if func == 'status':
        print(status())
    elif func == 'start':
        print(start())
    elif func == 'stop':
        print(stop())
    elif func == 'restart':
        print(restart())
    elif func == 'reload':
        print(reload())
    elif func == 'initd_status':
        print(initdStatus())
    elif func == 'initd_install':
        print(initdInstall())
    elif func == 'initd_uninstall':
        print(initdUninstall())
    elif func == 'get_total_statistics':
        print(getTotalStatistics())
    elif func == 'openwebui_status':
        print(openwebuiStatus())
    elif func == 'openwebui_install':
        print(openwebuiInstall())
    elif func == 'openwebui_install_worker':
        print(openwebuiInstallWorker())
    elif func == 'openwebui_install_progress':
        print(openwebuiInstallProgress())
    elif func == 'openwebui_start':
        print(openwebuiStart())
    elif func == 'openwebui_stop':
        print(openwebuiStop())
    elif func == 'openwebui_restart':
        print(openwebuiRestart())
    elif func == 'openwebui_uninstall':
        print(openwebuiUninstall())
    elif func == 'openwebui_port':
        print(openwebuiPort())
    elif func == 'openwebui_set_port':
        print(openwebuiSetPort())
    elif func == 'openwebui_get_config':
        print(openwebuiGetConfig())
    else:
        print('error')
