# coding: utf-8

import psutil
import time
import os
import slemp
import re
import json

import sys
# reload(sys)
# sys.setdefaultencoding('utf8')

import threading
import multiprocessing

from flask import render_template
from flask import request


class pa_thread(threading.Thread):

    def __init__(self, func, args, name=''):
        threading.Thread.__init__(self)
        self.name = name
        self.func = func
        self.args = args
        self.result = self.func(*self.args)

    def getResult(self):
        try:
            return self.result
        except Exception:
            return None


class plugins_api:
    __tasks = None
    __plugin_dir = 'plugins'
    __type = 'data/json/type.json'
    __index = 'data/json/index.json'
    setupPath = None

    def __init__(self):
        self.setupPath = 'server'
        self.__plugin_dir = slemp.getRunDir() + '/plugins'
        self.__type = slemp.getRunDir() + '/data/json/type.json'
        self.__index = slemp.getRunDir() + '/data/json/index.json'
        self.__versionCache = {}

    ##### ----- start ----- ###
    def listApi(self):
        sType = request.args.get('type', '0')
        sPage = request.args.get('p', '1')
        sPageSize = request.args.get('limit', '100')

        if not slemp.isNumber(sPage):
            sPage = 1

        if not slemp.isNumber(sType):
            sType = 0

        if not slemp.isNumber(sPageSize):
            sPageSize = 100

        # print sPage
        search = request.args.get('search', '').lower()
        data = self.getPluginList(sType, search, int(sPage), int(sPageSize))
        return slemp.getJson(data)

    def menuGetAbsPath(self, tag, path):
        if path[0:1] == '/':
            return path
        else:
            return slemp.getPluginDir() + '/' + tag + '/' + path

    def menuApi(self):
        import config_api
        data = config_api.config_api().get()
        tag = request.args.get('tag', '')
        menu_file = 'data/hook_menu.json'
        content = ''
        if os.path.exists(menu_file):
            t = slemp.readFile(menu_file)
            tlist = json.loads(t)
            for menu_data in tlist:
                if tag == menu_data['name'] and 'path' in menu_data:
                    tpath = self.menuGetAbsPath(tag, menu_data['path'])
                    content = slemp.readFile(tpath)
        data['plugin_content'] = content
        return render_template('plugin_menu.html', data=data)

    def fileApi(self):
        name = request.args.get('name', '')
        if name.strip() == '':
            return ''

        f = request.args.get('f', '')

        if f.strip() == '':
            return ''

        file = slemp.getPluginDir() + '/' + name + '/' + f
        if not os.path.exists(file):
            return ''

        suffix = slemp.getPathSuffix(file)
        if suffix == '.css':
            content = slemp.readFile(file)
            from flask import Response
            from flask import make_response
            v = Response(content, headers={
                         'Content-Type': 'text/css; charset="utf-8"'})
            return make_response(v)
        content = open(file, 'rb').read()
        return content

    def indexListApi(self):
        data = self.getIndexList()
        return slemp.getJson(data)

    def indexSortApi(self):
        sort = request.form.get('ssort', '')
        if sort.strip() == '':
            return slemp.returnJson(False, 'Sort data cannot be empty!')
        data = self.setIndexSort(sort)
        if data:
            return slemp.returnJson(True, 'Success!')
        return slemp.returnJson(False, 'Fail!')

    def initApi(self):

        plugin_names = {
            'openresty': '1.21.4.2',
            'php': '73',
            'swap': '1.1',
            'mysql': '5.7',
            'phpmyadmin': '4.4.15',
        }

        pn_dir = slemp.getPluginDir()
        pn_server_dir = slemp.getServerDir()
        pn_list = []
        for pn in plugin_names:
            info = {}
            pn_json = pn_dir + '/' + pn + '/info.json'
            pn_server = pn_server_dir + '/' + pn
            if not os.path.exists(pn_server):

                tmp = slemp.readFile(pn_json)
                tmp = json.loads(tmp)

                info['title'] = tmp['title']
                info['name'] = tmp['name']
                info['versions'] = tmp['versions']
                info['default_ver'] = plugin_names[pn]
                pn_list.append(info)
            else:
                return slemp.returnJson(False, 'ok')

        return slemp.returnJson(True, 'ok', pn_list)

    def initInstallApi(self):
        pn_list = request.form.get('list', '')
        try:
            pn_list = json.loads(pn_list)

            for pn in pn_list:
                name = pn['name']
                version = pn['version']
                infoJsonPos = self.__plugin_dir + '/' + name + '/' + 'info.json'
                pluginInfo = json.loads(slemp.readFile(infoJsonPos))
                self.hookInstall(pluginInfo)
                execstr = 'cd ' + slemp.getPluginDir() + '/' + name + ' && bash ' + \
                    pluginInfo['shell'] + ' install ' + version

                taskAdd = ('Install [' + name + '-' + version + ']',
                           'execshell', '0', time.strftime('%Y-%m-%d %H:%M:%S'), execstr)

                slemp.M('tasks').add('name,type,status,addtime, execstr', taskAdd)
            php_dir = slemp.getServerDir() + '/php'
            if not os.path.exists(php_dir):
                os.makedirs(php_dir)
            slemp.triggerTask()
            return slemp.returnJson(True, 'Added successfully')
        except Exception as e:
            return slemp.returnJson(False, slemp.getTracebackInfo())

    def installApi(self):
        rundir = slemp.getRunDir()
        name = request.form.get('name', '')
        version = request.form.get('version', '')

        mmsg = 'Install'
        if hasattr(request.form, 'upgrade'):
            mtype = 'update'
            mmsg = 'upgrade'

        if name.strip() == '':
            return slemp.returnJson(False, 'Missing plugin name!', ())

        if version.strip() == '':
            return slemp.returnJson(False, 'Missing version information!', ())

        infoJsonPos = self.__plugin_dir + '/' + name + '/' + 'info.json'
        # print infoJsonPos

        if not os.path.exists(infoJsonPos):
            return slemp.returnJson(False, 'Config file does not exist!', ())

        pluginInfo = json.loads(slemp.readFile(infoJsonPos))
        self.hookInstall(pluginInfo)

        execstr = 'cd ' + slemp.getPluginDir() + '/' + name + ' && bash ' + \
            pluginInfo['shell'] + ' install ' + version

        if slemp.isAppleSystem():
            print(execstr)

        taskAdd = (mmsg + '[' + name + '-' + version + ']',
                   'execshell', '0', time.strftime('%Y-%m-%d %H:%M:%S'), execstr)

        slemp.M('tasks').add('name,type,status,addtime, execstr', taskAdd)

        slemp.triggerTask()
        return slemp.returnJson(True, 'Added installation task to queue!')

    def updateApi(self):
        name = request.form.get('name', '').strip()
        version = request.form.get('version', '').strip()
        target = request.form.get('target', '').strip()

        if not re.match(r'^[a-zA-Z0-9_\-]+$', name):
            return slemp.returnJson(False, 'Nama plugin tidak valid!')

        if not re.match(r'^\d{2,3}$', version):
            return slemp.returnJson(False, 'Versi plugin tidak valid!')

        if not re.match(r'^\d+\.\d+\.\d+$', target):
            return slemp.returnJson(False, 'Versi target tidak valid!')

        infoJsonPos = self.__plugin_dir + '/' + name + '/info.json'
        if not os.path.exists(infoJsonPos):
            return slemp.returnJson(False, 'Config file does not exist!')

        pluginInfo = json.loads(slemp.readFile(infoJsonPos))
        updateInfo = self.getUpdateInfo(pluginInfo, version)
        if not updateInfo or updateInfo.get('version') != target:
            return slemp.returnJson(False, 'Versi update tidak tersedia untuk plugin ini!')

        tmpInfo = pluginInfo.copy()
        tmpInfo['versions'] = version
        pInfo = self.getPluginInfo(tmpInfo)

        if not pInfo['setup']:
            return slemp.returnJson(False, 'Plugin belum terpasang!')

        if pInfo['task'] != '1':
            return slemp.returnJson(False, 'Masih ada tugas yang berjalan untuk plugin ini!')

        installed = pInfo['installed_version'] or self.getInstalledVersion(
            pInfo['path'])
        if not installed:
            return slemp.returnJson(False, 'Versi terpasang tidak dapat dideteksi!')

        needsUpdate = self.versionLess(installed, target)
        if updateInfo.get('patch') and not pInfo['update_patched']:
            needsUpdate = True
        if not needsUpdate:
            return slemp.returnJson(False, 'Plugin sudah menggunakan versi terbaru!')

        shell = pluginInfo.get('shell', 'install.sh')
        execstr = 'cd ' + slemp.getPluginDir() + '/' + name + ' && bash ' + \
            shell + ' update ' + version + ' ' + target

        taskAdd = ('Update[' + name + '-' + version + ']',
                   'execshell', '0', time.strftime('%Y-%m-%d %H:%M:%S'), execstr)

        slemp.M('tasks').add('name,type,status,addtime, execstr', taskAdd)
        slemp.triggerTask()
        return slemp.returnJson(True, 'Tugas update ditambahkan ke antrean!')

    def hookInstallFile(self, hook_name, info):
        hookPath = slemp.getPanelDataDir() + "/hook_" + hook_name + ".json"
        data = []
        if os.path.exists(hookPath):
            t = slemp.readFile(hookPath)
            data = json.loads(t)

        isNeedAdd = True
        for x in range(len(data)):
            if data[x]['title'] == info['title'] and data[x]['name'] == info['name']:
                isNeedAdd = False

        if isNeedAdd:
            data.append(info)
        slemp.writeFile(hookPath, json.dumps(data))

    def hookUninstallFile(self, hook_name, info):
        hookPath = slemp.getPanelDataDir() + "/hook_" + hook_name + ".json"
        data = []
        if os.path.exists(hookPath):
            t = slemp.readFile(hookPath)
            data = json.loads(t)

        for idx in range(len(data)):
            if data[idx]['name'] == info['name']:
                data.remove(data[idx])
                break
        slemp.writeFile(hookPath, json.dumps(data))

    def hookInstall(self, info):
        valid_hook = ['backup', 'database']
        valid_list_hook = ['menu', 'global_static', 'site_cb']
        if 'hook' in info:
            hooks = info['hook']
            for h in hooks:
                hooks_type = type(h)
                if hooks_type == dict:
                    tag = h['tag']
                    if tag in valid_list_hook:
                        self.hookInstallFile(tag, h[tag])
                elif hooks_type == str:
                    for x in hooks:
                        if x in valid_hook:
                            self.hookInstallFile(x, info)
                            return True
        return False

    def hookUninstall(self, info):
        valid_hook = ['backup', 'database']
        valid_list_hook = ['menu', 'global_static', 'site_cb']
        if 'hook' in info:
            hooks = info['hook']
            for h in hooks:
                hooks_type = type(h)
                if hooks_type == dict:
                    tag = h['tag']
                    if tag in valid_list_hook:
                        self.hookUninstallFile(tag, h[tag])
                elif hooks_type == str:
                    for x in hooks:
                        if x in valid_hook:
                            self.hookUninstallFile(x, info)
                            return True
        return False

    def uninstallOldApi(self):
        rundir = slemp.getRunDir()
        name = request.form.get('name', '')
        version = request.form.get('version', '')
        if name.strip() == '':
            return slemp.returnJson(False, "Missing plugin name!", ())

        if version.strip() == '':
            return slemp.returnJson(False, "Missing version information!", ())

        infoJsonPos = self.__plugin_dir + '/' + name + '/' + 'info.json'

        if not os.path.exists(infoJsonPos):
            return slemp.returnJson(False, "Config file does not exist!", ())

        pluginInfo = json.loads(slemp.readFile(infoJsonPos))
        execstr = "cd " + slemp.getPluginDir() + "/" + \
            name + " && /bin/bash " + pluginInfo["shell"] \
            + " uninstall " + version

        taskAdd = (None, 'Uninstall [' + name + '-' + version + ']',
                   'execshell', '0', time.strftime('%Y-%m-%d %H:%M:%S'), execstr)

        slemp.M('tasks').add('id,name,type,status,addtime, execstr', taskAdd)
        return slemp.returnJson(True, 'Added uninstall task to queue!')

    def uninstallApi(self):
        rundir = slemp.getRunDir()
        name = request.form.get('name', '')
        version = request.form.get('version', '')
        if name.strip() == '':
            return slemp.returnJson(False, "Missing plugin name!", ())

        if version.strip() == '':
            return slemp.returnJson(False, "Missing version information!", ())

        infoJsonPos = self.__plugin_dir + '/' + name + '/' + 'info.json'

        if not os.path.exists(infoJsonPos):
            return slemp.returnJson(False, "Config file does not exist!", ())

        pluginInfo = json.loads(slemp.readFile(infoJsonPos))
        self.hookUninstall(pluginInfo)
        execstr = "cd " + slemp.getPluginDir() + "/" + \
            name + " && /bin/bash " + pluginInfo["shell"] \
            + " uninstall " + version

        data = slemp.execShell(execstr)
        if slemp.isDebugMode():
            print(execstr)
            print(data[0], data[1])
        self.removeIndex(name, version)
        return slemp.returnJson(True, 'Uninstallation performed successfully!')
        # if data[1] == '':
        #     return slemp.returnJson(True, 'Uninstalled successfully!')
        # else:
        #     return slemp.returnJson(False, 'Uninstall error message!' + data[1])

    def checkApi(self):
        name = request.form.get('name', '')
        if name.strip() == '':
            return slemp.returnJson(False, "Missing plugin name!", ())

        infoJsonPos = self.__plugin_dir + '/' + name + '/' + 'info.json'
        if not os.path.exists(infoJsonPos):
            return slemp.returnJson(False, "Config file does not exist!", ())
        return slemp.returnJson(True, "Plugin exists!", ())

    def setIndexApi(self):
        name = request.form.get('name', '')
        status = request.form.get('status', '0')
        version = request.form.get('version', '')
        if status == '1':
            return self.addIndex(name, version)
        return self.removeIndex(name, version)

    def settingApi(self):
        name = request.args.get('name', '')
        html = self.__plugin_dir + '/' + name + '/index.html'
        return slemp.readFile(html)

    def runApi(self):
        name = request.form.get('name', '')
        func = request.form.get('func', '')
        version = request.form.get('version', '')
        args = request.form.get('args', '')
        script = request.form.get('script', 'index')

        data = self.run(name, func, version, args, script)
        
        # Clean stderr of standard warnings (SSL warnings, deprecation notices, etc.)
        stderr_clean = ''
        if data[1] != '':
            stderr_lines = data[1].strip().split('\n')
            clean_lines = []
            for line in stderr_lines:
                if not line:
                    continue
                line_lower = line.lower()
                if 'warning' in line_lower or 'deprecation' in line_lower:
                    continue
                clean_lines.append(line)
            stderr_clean = '\n'.join(clean_lines).strip()

        if stderr_clean == '':
            r = slemp.returnJson(True, "OK", data[0].strip())
        else:
            r = slemp.returnJson(False, stderr_clean)
        return r

    def callbackApi(self):
        name = request.form.get('name', '')
        func = request.form.get('func', '')
        args = request.form.get('args', '')
        script = request.form.get('script', 'index')

        data = self.callback(name, func, args, script)
        if data[0]:
            return slemp.returnJson(True, "OK", data[1])
        return slemp.returnJson(False, data[1])

    ##### ----- end ----- ###

    def processExists(self, pname, exe=None):
        try:
            if not self.pids:
                self.pids = psutil.pids()
            for pid in self.pids:
                try:
                    p = psutil.Process(pid)
                    if p.name() == pname:
                        if not exe:
                            return True
                        else:
                            if p.exe() == exe:
                                return True
                except:
                    pass
            return False
        except:
            return True

    def checkSetupTask(self, sName, sVer, sCoexist):
        if not self.__tasks:
            self.__tasks = slemp.M('tasks').where(
                "status!=?", ('1',)).field('status,name').select()
        isTask = '1'
        taskLabel = ''
        for task in self.__tasks:
            tmpt = slemp.getStrBetween('[', ']', task['name'])
            if not tmpt:
                continue
            task_sign = tmpt.split('-')
            task_len = len(task_sign)

            task_name = task_sign[0].lower()
            task_ver = task_sign[1]
            if task_len > 2:
                nameArr = task_sign[0:task_len - 1]
                task_name = '-'.join(nameArr).lower()
                task_ver = task_sign[task_len - 1]
            if sCoexist:
                if task_name == sName and task_ver == sVer:
                    isTask = task['status']
                    taskLabel = task['name'].split('[')[0].strip()
            else:
                if task_name == sName:
                    isTask = task['status']
                    taskLabel = task['name'].split('[')[0].strip()
        return (isTask, taskLabel)

    def checkStatus(self, info):
        if not info['setup']:
            return False

        data = self.run(info['name'], 'status', info['setup_version'])
        if data[0] == 'start':
            return True
        return False

    def checkStatusProcess(self, info, i, return_dict):
        if not info['setup']:
            return_dict[i] = False
            return

        data = self.run(info['name'], 'status', info['setup_version'])
        if data[0] == 'start':
            return_dict[i] = True
        else:
            return_dict[i] = False

    def checkStatusThreads(self, info, i):
        if not info['setup']:
            return False
        data = self.run(info['name'], 'status', info['setup_version'])
        if data[0] == 'start':
            return True
        else:
            return False

    def checkStatusThreadsCallback(self, info, i):
        if not info['setup']:
            return False

        try:
            data = self.callback(info['name'], 'status', info['setup_version'])
        except Exception as e:
            data = self.callback(info['name'], 'status')

        # data = self.run(info['name'], 'status', info['setup_version'])
        if data[0] == 'start':
            return True
        else:
            return False

    def checkStatusMThreads(self, plugins_info):
        try:
            threads = []
            ntmp_list = range(len(plugins_info))
            for i in ntmp_list:
                t = pa_thread(self.checkStatusThreads,
                              (plugins_info[i], i))
                threads.append(t)

            for i in ntmp_list:
                threads[i].start()
            for i in ntmp_list:
                threads[i].join()

            for i in ntmp_list:
                t = threads[i].getResult()
                plugins_info[i]['status'] = t
        except Exception as e:
            print('checkStatusMThreads:', str(e))

        return plugins_info

    def checkStatusMProcess(self, plugins_info):
        manager = multiprocessing.Manager()
        return_dict = manager.dict()
        jobs = []
        for i in range(len(plugins_info)):
            p = multiprocessing.Process(
                target=self.checkStatusProcess, args=(plugins_info[i], i, return_dict))
            jobs.append(p)
            p.start()

        for proc in jobs:
            proc.join()

        returnData = return_dict.values()
        for i in ntmp_list:
            plugins_info[i]['status'] = returnData[i]

        return plugins_info

    def checkDisplayIndex(self, name, version):
        if not os.path.exists(self.__index):
            slemp.writeFile(self.__index, '[]')

        indexList = json.loads(slemp.readFile(self.__index))
        if type(version) == list:
            for index in range(len(version)):
                vname = name + '-' + version[index]
                if vname in indexList:
                    return True
        else:
            vname = name + '-' + version
            if vname in indexList:
                return True
        return False

    def getVersion(self, path):
        version_f = path + '/version.pl'
        if os.path.exists(version_f):
            return slemp.readFile(version_f).strip()
        return ''

    def getInstalledVersion(self, path):
        if path in self.__versionCache:
            return self.__versionCache[path]

        version = ''
        version_f = path + '/version.pl'
        if os.path.exists(version_f):
            v = slemp.readFile(version_f).strip()
            if re.match(r'^\d+\.\d+\.\d+$', v):
                version = v

        if version == '':
            php_bin = path + '/bin/php'
            if os.path.exists(php_bin):
                try:
                    data = slemp.execShell(
                        php_bin + " -r 'echo PHP_VERSION;'", timeout=5)
                    found = re.findall(r'\b\d+\.\d+\.\d+\b', data[0])
                    if found:
                        version = found[-1]
                except Exception:
                    pass

        self.__versionCache[path] = version
        return version

    def versionLess(self, current, latest):
        try:
            c = [int(x) for x in current.split('.')]
            l = [int(x) for x in latest.split('.')]
            length = max(len(c), len(l))
            c += [0] * (length - len(c))
            l += [0] * (length - len(l))
            return c < l
        except Exception:
            return False

    def getUpdateInfo(self, info, version):
        updates = info.get('updates', {})
        if not isinstance(updates, dict) or not isinstance(version, str):
            return {}
        item = updates.get(version, {})
        if isinstance(item, dict) and item.get('version'):
            return item
        return {}

    def getSecurityUpdates(self):
        result = []
        infoPath = self.__plugin_dir + '/php/info.json'
        if not os.path.exists(infoPath):
            return result

        try:
            info = json.loads(slemp.readFile(infoPath))
        except Exception:
            return result

        updates = info.get('updates', {})
        if not isinstance(updates, dict):
            return result

        for branch in sorted(updates.keys()):
            updateInfo = updates[branch]
            if not isinstance(updateInfo, dict) or not updateInfo.get('version'):
                continue

            tmpInfo = info.copy()
            tmpInfo['versions'] = branch
            pInfo = self.getPluginInfo(tmpInfo)

            if not pInfo['setup'] or not pInfo['installed_version']:
                continue

            if not pInfo['update_available']:
                continue

            result.append({
                'name': info.get('name', 'php'),
                'branch': branch,
                'title': info.get('title', 'PHP') + '-' + branch,
                'installed': pInfo['installed_version'],
                'target': updateInfo['version'],
                'security': updateInfo.get('security', ''),
                'changelog': updateInfo.get('changelog', []),
                'patch': updateInfo.get('patch', ''),
                'eol': updateInfo.get('eol', False),
            })

        eolOnly = info.get('eol_only', [])
        if isinstance(eolOnly, list):
            for branch in eolOnly:
                if not isinstance(branch, str):
                    continue
                tmpInfo = info.copy()
                tmpInfo['versions'] = branch
                pInfo = self.getPluginInfo(tmpInfo)
                if not pInfo['setup'] or not pInfo['installed_version']:
                    continue
                result.append({
                    'name': info.get('name', 'php'),
                    'branch': branch,
                    'title': info.get('title', 'PHP') + '-' + branch,
                    'installed': pInfo['installed_version'],
                    'target': '',
                    'security': 'PHP2Shell: CVE-2026-109618, CVE-2026-109619',
                    'changelog': [],
                    'patch': '',
                    'eol': True,
                })

        return result

    def getPluginInfo(self, info):
        checks = ''
        path = ''
        coexist = False

        if info["checks"][0:1] == '/':
            checks = info["checks"]
        else:
            checks = slemp.getRootDir() + '/' + info['checks']

        if 'path' in info:
            path = info['path']

        if path[0:1] != '/':
            path = slemp.getRootDir() + '/' + path

        if 'coexist' in info and info['coexist']:
            coexist = True

        pInfo = {
            "id": 10000,
            "pid": info['pid'],
            "type": 1000,
            "name": info['name'],
            "title": info['title'],
            "ps": info['ps'],
            "dependnet": "",
            "mutex": "",
            "icon": "",
            "path": path,
            "install_checks": checks,
            "uninsatll_checks": checks,
            "coexist": coexist,
            "versions": info['versions'],
            # "updates": info['updates'],
            "display": False,
            "setup": False,
            "setup_version": "",
            "installed_version": "",
            "latest_version": "",
            "update_available": False,
            "update_target": "",
            "update_security": "",
            "update_changelog": [],
            "update_patch": "",
            "update_patched": False,
            "task_label": "",
            "status": False,
            "install_pre_inspection": False,
            "uninstall_pre_inspection": False,
        }

        if 'icon' in info:
            pInfo['icon'] = info['icon']

        if checks.find('VERSION') > -1:
            pInfo['install_checks'] = checks.replace(
                'VERSION', info['versions'])

        if path.find('VERSION') > -1:
            pInfo['path'] = path.replace(
                'VERSION', info['versions'])

        pInfo['task'], pInfo['task_label'] = self.checkSetupTask(
            pInfo['name'], info['versions'], coexist)
        pInfo['display'] = self.checkDisplayIndex(
            info['name'], pInfo['versions'])

        pInfo['setup'] = os.path.exists(pInfo['install_checks'])

        if coexist and pInfo['setup']:
            pInfo['setup_version'] = info['versions']
        else:
            pInfo['setup_version'] = self.getVersion(pInfo['install_checks'])

        if coexist and pInfo['setup']:
            pInfo['installed_version'] = self.getInstalledVersion(
                pInfo['path'])

        updateInfo = self.getUpdateInfo(info, info['versions'])
        if updateInfo and pInfo['setup']:
            pInfo['latest_version'] = updateInfo['version']
            pInfo['update_security'] = updateInfo.get('security', '')
            pInfo['update_changelog'] = updateInfo.get('changelog', [])
            pInfo['update_patch'] = updateInfo.get('patch', '')
            if pInfo['update_patch']:
                pInfo['update_patched'] = os.path.exists(
                    pInfo['path'] + '/.php2shell_patched')

            if pInfo['installed_version']:
                needsUpdate = self.versionLess(
                    pInfo['installed_version'], updateInfo['version'])
                if pInfo['update_patch'] and not pInfo['update_patched']:
                    needsUpdate = True
                if needsUpdate:
                    pInfo['update_available'] = True
                    pInfo['update_target'] = updateInfo['version']
        # pluginInfo['status'] = self.checkStatus(pluginInfo)

        if 'install_pre_inspection' in info:
            pInfo['install_pre_inspection'] = info['install_pre_inspection']
        if 'uninstall_pre_inspection' in info:
            pInfo['uninstall_pre_inspection'] = info[
                'uninstall_pre_inspection']

        pInfo['status'] = False
        return pInfo

    def makeCoexist(self, data):
        plugins_info = []
        for index in range(len(data['versions'])):
            tmp = data.copy()
            tmp['title'] = tmp['title'] + \
                '-' + data['versions'][index]
            tmp['versions'] = data['versions'][index]
            pg = self.getPluginInfo(tmp)
            plugins_info.append(pg)

        return plugins_info

    def makeList(self, data, sType='0'):
        plugins_info = []

        if (data['pid'] == sType):
            if type(data['versions']) == list and 'coexist' in data and data['coexist']:
                tmp_data = self.makeCoexist(data)
                for index in range(len(tmp_data)):
                    plugins_info.append(tmp_data[index])
            else:
                pg = self.getPluginInfo(data)
                plugins_info.append(pg)
            return plugins_info

        if sType == '0':
            if type(data['versions']) == list and 'coexist' in data and data['coexist']:
                tmp_data = self.makeCoexist(data)
                for index in range(len(tmp_data)):
                    plugins_info.append(tmp_data[index])
            else:
                pg = self.getPluginInfo(data)
                plugins_info.append(pg)

        if sType == '-1':
            if type(data['versions']) == list and 'coexist' in data and data['coexist']:
                tmp_data = self.makeCoexist(data)
                for index in range(len(tmp_data)):
                    if tmp_data[index]['setup']:
                        plugins_info.append(tmp_data[index])
            else:
                pg = self.getPluginInfo(data)
                if pg['setup']:
                    plugins_info.append(pg)

        # print plugins_info, data
        return plugins_info

    def getAllList(self, sType='0'):
        plugins_info = []
        for dirinfo in os.listdir(self.__plugin_dir):
            if dirinfo[0:1] == '.':
                continue
            path = self.__plugin_dir + '/' + dirinfo
            json_file = path + '/info.json'
            if os.path.exists(json_file):
                try:
                    data = json.loads(slemp.readFile(json_file))
                    tmp_data = self.makeList(data, sType)
                    for index in range(len(tmp_data)):
                        plugins_info.append(tmp_data[index])
                except Exception as e:
                    print(e)
        return plugins_info

    def searchKey(self, info, kw):
        try:
            if info['title'].lower().find(kw) > -1:
                return True
            if info['ps'].lower().find(kw) > -1:
                return True
            if info['name'].lower().find(kw) > -1:
                return True
        except Exception as e:
            return False

    def getAllListPage(self, sType='0', kw='', page=1, pageSize=10):
        plugins_info = []
        for dirinfo in os.listdir(self.__plugin_dir):
            if dirinfo[0:1] == '.':
                continue
            path = self.__plugin_dir + '/' + dirinfo
            if os.path.isdir(path):
                json_file = path + '/info.json'
                if os.path.exists(json_file):
                    try:
                        data = json.loads(slemp.readFile(json_file))
                        if kw != '' and not self.searchKey(data, kw):
                            continue
                        tmp_data = self.makeList(data, sType)
                        for index in range(len(tmp_data)):
                            plugins_info.append(tmp_data[index])
                    except Exception as e:
                        print(slemp.getTracebackInfo())

        if pageSize > 0:
            start = (page - 1) * pageSize
            end = start + pageSize
            _plugins_info = plugins_info[start:end]
        else:
            _plugins_info = plugins_info

        _plugins_info = self.checkStatusMThreads(_plugins_info)
        return (_plugins_info, len(plugins_info))

    def makeListThread(self, data, sType='0'):
        plugins_info = []

        if (data['pid'] == sType):
            if type(data['versions']) == list and data.has_key('coexist') and data['coexist']:
                tmp_data = self.makeCoexist(data)
                for index in range(len(tmp_data)):
                    plugins_info.append(tmp_data[index])
            else:
                pg = self.getPluginInfo(data)
                plugins_info.append(pg)
            return plugins_info

        if sType == '0':
            if type(data['versions']) == list and data.has_key('coexist') and data['coexist']:
                tmp_data = self.makeCoexist(data)
                for index in range(len(tmp_data)):
                    plugins_info.append(tmp_data[index])
            else:
                pg = self.getPluginInfo(data)
                plugins_info.append(pg)

        # print plugins_info, data
        return plugins_info

    def getAllListThread(self, sType='0'):
        plugins_info = []
        tmp_list = []
        threads = []
        for dirinfo in os.listdir(self.__plugin_dir):
            if dirinfo[0:1] == '.':
                continue
            path = self.__plugin_dir + '/' + dirinfo
            if os.path.isdir(path):
                json_file = path + '/info.json'
                if os.path.exists(json_file):
                    data = json.loads(slemp.readFile(json_file))
                    if sType == '0':
                        tmp_list.append(data)

                    if (data['pid'] == sType):
                        tmp_list.append(data)

        ntmp_list = range(len(tmp_list))
        for i in ntmp_list:
            t = pa_thread(self.makeListThread, (tmp_list[i], sType))
            threads.append(t)
        for i in ntmp_list:
            threads[i].start()
        for i in ntmp_list:
            threads[i].join()

        for i in ntmp_list:
            t = threads[i].getResult()
            for index in range(len(t)):
                plugins_info.append(t[index])

        return plugins_info

    def makeListProcess(self, data, sType, i, return_dict):
        plugins_info = []

        if (data['pid'] == sType):
            if type(data['versions']) == list and data.has_key('coexist') and data['coexist']:
                tmp_data = self.makeCoexist(data)
                for index in range(len(tmp_data)):
                    plugins_info.append(tmp_data[index])
            else:
                pg = self.getPluginInfo(data)
                plugins_info.append(pg)
            # return plugins_info

        if sType == '0':
            if type(data['versions']) == list and data.has_key('coexist') and data['coexist']:
                tmp_data = self.makeCoexist(data)
                for index in range(len(tmp_data)):
                    plugins_info.append(tmp_data[index])
            else:
                pg = self.getPluginInfo(data)
                plugins_info.append(pg)

        return_dict[i] = plugins_info
        # return plugins_info

    def getAllListProcess(self, sType='0'):
        plugins_info = []
        tmp_list = []
        manager = multiprocessing.Manager()
        return_dict = manager.dict()
        jobs = []
        for dirinfo in os.listdir(self.__plugin_dir):
            if dirinfo[0:1] == '.':
                continue
            path = self.__plugin_dir + '/' + dirinfo
            if os.path.isdir(path):
                json_file = path + '/info.json'
                if os.path.exists(json_file):
                    data = json.loads(slemp.readFile(json_file))
                    if sType == '0':
                        tmp_list.append(data)

                    if (data['pid'] == sType):
                        tmp_list.append(data)

        ntmp_list = range(len(tmp_list))
        for i in ntmp_list:
            p = multiprocessing.Process(
                target=self.makeListProcess, args=(tmp_list[i], sType, i, return_dict))
            jobs.append(p)
            p.start()

        for proc in jobs:
            proc.join()

        returnData = return_dict.values()
        for i in ntmp_list:
            for index in range(len(returnData[i])):
                plugins_info.append(returnData[i][index])

        return plugins_info

    def getPluginList(self, sType, kw='', sPage=1, sPageSize=10):
        # print sType, sPage, sPageSize

        ret = {}
        ret['type'] = json.loads(slemp.readFile(self.__type))
        # plugins_info = self.getAllListThread(sType)
        # plugins_info = self.getAllListProcess(sType)
        data = self.getAllListPage(sType, kw, sPage, sPageSize)
        ret['data'] = data[0]

        if sPageSize == 0:
            ret['php_security'] = self.getSecurityUpdates()

        if sPageSize > 0:
            args = {}
            args['count'] = data[1]
            args['p'] = sPage
            args['tojs'] = 'getSList'
            args['row'] = sPageSize

            ret['list'] = slemp.getPage(args)
        return ret

    def getIndexList(self):
        if not os.path.exists(self.__index):
            slemp.writeFile(self.__index, '[]')

        indexList = json.loads(slemp.readFile(self.__index))
        plist = []
        for i in indexList:
            tmp = i.split('-')
            tmp_len = len(tmp)
            plugin_name = tmp[0]
            plugin_ver = tmp[1]
            if tmp_len > 2:
                tmpArr = tmp[0:tmp_len - 1]
                plugin_name = '-'.join(tmpArr)
                plugin_ver = tmp[tmp_len - 1]

            json_file = self.__plugin_dir + '/' + plugin_name + '/info.json'
            if os.path.exists(json_file):
                content = slemp.readFile(json_file)
                try:
                    data = json.loads(content)
                    data = self.makeList(data)
                    for index in range(len(data)):
                        if data[index]['versions'] == plugin_ver or plugin_ver in data[index]['versions']:
                            data[index]['display'] = True
                            plist.append(data[index])
                            continue
                except Exception as e:
                    print('getIndexList:', e)

        # plist = self.checkStatusMProcess(plist)
        plist = self.checkStatusMThreads(plist)
        return plist

    def setIndexSort(self, sort):
        data = sort.split('|')
        slemp.writeFile(self.__index, json.dumps(data))
        return True

    def addIndex(self, name, version):
        if not os.path.exists(self.__index):
            slemp.writeFile(self.__index, '[]')

        indexList = json.loads(slemp.readFile(self.__index))
        vname = name + '-' + version

        if vname in indexList:
            return slemp.returnJson(False, 'Please do not add repeatedly!')
        if len(indexList) > 12:
            return slemp.returnJson(False, 'The home page can only display up to 12 software!')

        indexList.append(vname)
        slemp.writeFile(self.__index, json.dumps(indexList))
        return slemp.returnJson(True, 'Added successfully!')

    def removeIndex(self, name, version):
        if not os.path.exists(self.__index):
            slemp.writeFile(self.__index, '[]')

        indexList = json.loads(slemp.readFile(self.__index))
        vname = name + '-' + version
        if not vname in indexList:
            return slemp.returnJson(True, 'Successfully deleted!')
        indexList.remove(vname)
        slemp.writeFile(self.__index, json.dumps(indexList))
        return slemp.returnJson(True, 'Successfully deleted!')

    def run(self, name, func, version='', args='', script='index'):

        path = self.__plugin_dir + '/' + name + '/' + script + '.py'
        if not os.path.exists(path):
            path = self.__plugin_dir + '/' + name + '/' + name + '.py'

        py = sys.executable + ' -W ignore ' + path

        if args == '':
            py_cmd = py + ' ' + func + ' ' + version
        else:
            py_cmd = py + ' ' + func + ' ' + version + ' ' + args

        if not os.path.exists(path):
            return ('', '')
        data = slemp.execShell(py_cmd)

        if slemp.isDebugMode():
            print('run', py_cmd)
            print(data)
        # print os.path.exists(py_cmd)

        return (data[0].strip(), data[1].strip())

    def callback(self, name, func, args='', script='index'):
        package = self.__plugin_dir + '/' + name
        if not os.path.exists(package):
            return (False, "Plugin does not exist!")

        sys.path.append(package)
        eval_str = "__import__('" + script + "')." + func + '(' + args + ')'
        newRet = eval(eval_str)
        if slemp.isDebugMode():
            print('callback', eval_str)

        return (True, newRet)
