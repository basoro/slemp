# coding: utf-8

import psutil
import time
import os
import slemp
import re
import json

import sys

import threading
import multiprocessing


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

    def listApi(self):
        sType = request.args.get('type', '0')
        sPage = request.args.get('p', '1')

        if not slemp.isNumber(sPage):
            sPage = 1

        if not slemp.isNumber(sType):
            sType = 0

        data = self.getPluginList(sType, int(sPage))
        return slemp.getJson(data)

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

        c = open(file, 'rb').read()
        return c

    def indexListApi(self):
        data = self.getIndexList()
        return slemp.getJson(data)

    def indexSortApi(self):
        sort = request.form.get('ssort', '')
        if sort.strip() == '':
            return slemp.returnJson(False, 'Sortir data tidak boleh kosong!')
        data = self.setIndexSort(sort)
        if data:
            return slemp.returnJson(True, 'Sukses!')
        return slemp.returnJson(False, 'Gagal!')

    def installApi(self):
        rundir = slemp.getRunDir()
        name = request.form.get('name', '')
        version = request.form.get('version', '')

        mmsg = 'Instal'
        if hasattr(request.form, 'upgrade'):
            mtype = 'update'
            mmsg = 'upgrade'

        if name.strip() == '':
            return slemp.returnJson(False, 'Nama plugin tidak ada!', ())

        if version.strip() == '':
            return slemp.returnJson(False, 'Informasi versi tidak ada!', ())

        infoJsonPos = self.__plugin_dir + '/' + name + '/' + 'info.json'
        # print infoJsonPos

        if not os.path.exists(infoJsonPos):
            return slemp.returnJson(False, 'File konfigurasi tidak ada!', ())

        pluginInfo = json.loads(slemp.readFile(infoJsonPos))

        execstr = "cd " + os.getcwd() + "/plugins/" + \
            name + " && /bin/bash " + pluginInfo["shell"] \
            + " install " + version

        if slemp.isAppleSystem():
            print(execstr)

        taskAdd = (None, mmsg + '[' + name + '-' + version + ']',
                   'execshell', '0', time.strftime('%Y-%m-%d %H:%M:%S'), execstr)

        slemp.M('tasks').add('id,name,type,status,addtime, execstr', taskAdd)

        slemp.triggerTask()
        return slemp.returnJson(True, 'Penginstallan ditambahkan ke antrian!')

    def uninstallOldApi(self):
        rundir = slemp.getRunDir()
        name = request.form.get('name', '')
        version = request.form.get('version', '')
        if name.strip() == '':
            return slemp.returnJson(False, "Nama plugin tidak ada!", ())

        if version.strip() == '':
            return slemp.returnJson(False, "Informasi versi tidak ada!", ())

        infoJsonPos = self.__plugin_dir + '/' + name + '/' + 'info.json'

        if not os.path.exists(infoJsonPos):
            return slemp.returnJson(False, "File konfigurasi tidak ada!", ())

        pluginInfo = json.loads(slemp.readFile(infoJsonPos))

        execstr = "cd " + os.getcwd() + "/plugins/" + \
            name + " && /bin/bash " + pluginInfo["shell"] \
            + " uninstall " + version

        taskAdd = (None, '卸载[' + name + '-' + version + ']',
                   'execshell', '0', time.strftime('%Y-%m-%d %H:%M:%S'), execstr)

        slemp.M('tasks').add('id,name,type,status,addtime, execstr', taskAdd)
        return slemp.returnJson(True, 'Penghapusan tugas ditambahkan ke antrian!')

    def uninstallApi(self):
        rundir = slemp.getRunDir()
        name = request.form.get('name', '')
        version = request.form.get('version', '')
        if name.strip() == '':
            return slemp.returnJson(False, "Nama plugin tidak ada!", ())

        if version.strip() == '':
            return slemp.returnJson(False, "Informasi versi tidak ada!", ())

        infoJsonPos = self.__plugin_dir + '/' + name + '/' + 'info.json'

        if not os.path.exists(infoJsonPos):
            return slemp.returnJson(False, "File konfigurasi tidak ada!", ())

        pluginInfo = json.loads(slemp.readFile(infoJsonPos))

        execstr = "cd " + os.getcwd() + "/plugins/" + \
            name + " && /bin/bash " + pluginInfo["shell"] \
            + " uninstall " + version

        data = slemp.execShell(execstr)
        if slemp.isAppleSystem():
            print(execstr)
            print(data[0], data[1])
        self.removeIndex(name, version)
        return slemp.returnJson(True, 'Penghapusan instalasi berhasil dijalankan!')

    def checkApi(self):
        name = request.form.get('name', '')
        if name.strip() == '':
            return slemp.returnJson(False, "Nama plugin tidak ada!", ())

        infoJsonPos = self.__plugin_dir + '/' + name + '/' + 'info.json'
        if not os.path.exists(infoJsonPos):
            return slemp.returnJson(False, "File konfigurasi tidak ada!", ())
        return slemp.returnJson(True, "Plugin ada!", ())

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
        if data[1] == '':
            r = slemp.returnJson(True, "OK", data[0].strip())
        else:
            r = slemp.returnJson(False, data[1].strip())
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

    def updateZipApi(self):
        tmp_path = slemp.getRootDir() + '/temp'
        if not os.path.exists(tmp_path):
            os.makedirs(tmp_path)
        slemp.execShell("rm -rf " + tmp_path + '/*')

        tmp_file = tmp_path + '/plugin_tmp.zip'
        from werkzeug.utils import secure_filename
        from flask import request
        f = request.files['plugin_zip']
        if f.filename[-4:] != '.zip':
            return slemp.returnJson(False, 'Hanya file zip yang didukung!')
        f.save(tmp_file)
        slemp.execShell('cd ' + tmp_path + ' && unzip ' + tmp_file)
        os.remove(tmp_file)

        p_info = tmp_path + '/info.json'
        if not os.path.exists(p_info):
            d_path = None
            for df in os.walk(tmp_path):
                if len(df[2]) < 3:
                    continue
                if not 'info.json' in df[2]:
                    continue
                if not 'install.sh' in df[2]:
                    continue
                if not os.path.exists(df[0] + '/info.json'):
                    continue
                d_path = df[0]
            if d_path:
                tmp_path = d_path
                p_info = tmp_path + '/info.json'
        try:
            data = json.loads(slemp.readFile(p_info))
            data['size'] = slemp.getPathSize(tmp_path)
            if not 'author' in data:
                data['author'] = 'Tidak dikenal'
            if not 'home' in data:
                data['home'] = 'https://github.com/basoro/slemp'
            plugin_path = slemp.getPluginDir() + data['name'] + '/info.json'
            data['old_version'] = '0'
            data['tmp_path'] = tmp_path
            if os.path.exists(plugin_path):
                try:
                    old_info = json.loads(slemp.ReadFile(plugin_path))
                    data['old_version'] = old_info['versions']
                except:
                    pass
        except:
            slemp.execShell("rm -rf " + tmp_path)
            return slemp.returnJson(False, 'Informasi plugin tidak ditemukan dalam paket terkompresi, silakan periksa paket plugin!')
        protectPlist = ('openresty', 'mysql', 'php', 'swap')
        if data['name'] in protectPlist:
            return slemp.returnJson(False, '[' + data['name'] + '], plugin penting tidak dapat dimodifikasi!')
        return slemp.getJson(data)

    def inputZipApi(self):
        plugin_name = request.form.get('plugin_name', '')
        tmp_path = request.form.get('tmp_path', '')

        if not os.path.exists(tmp_path):
            return slemp.returnJson(False, 'File sementara tidak ada, silakan unggah lagi!')
        plugin_path = slemp.getPluginDir() + '/' + plugin_name
        if not os.path.exists(plugin_path):
            print(slemp.execShell('mkdir -p ' + plugin_path))
        slemp.execShell("\cp -rf " + tmp_path + '/* ' + plugin_path + '/')
        slemp.execShell('chmod -R 755 ' + plugin_path)
        p_info = slemp.readFile(plugin_path + '/info.json')
        if p_info:
            slemp.writeLog('Manajemen perangkat lunak', 'Instal plugin pihak ketiga [%s]' %
                        json.loads(p_info)['title'])
            return slemp.returnJson(True, 'Instalasi berhasil!')
        slemp.execShell("rm -rf " + plugin_path)
        return slemp.returnJson(False, 'Instalasi gagal!')

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
            else:
                if task_name == sName:
                    isTask = task['status']
        return isTask

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
            "path": path,
            "install_checks": checks,
            "uninsatll_checks": checks,
            "coexist": coexist,
            "versions": info['versions'],
            # "updates": info['updates'],
            "display": False,
            "setup": False,
            "setup_version": "",
            "status": False,
            "install_pre_inspection": False,
            "uninstall_pre_inspection": False,
        }

        if checks.find('VERSION') > -1:
            pInfo['install_checks'] = checks.replace(
                'VERSION', info['versions'])

        if path.find('VERSION') > -1:
            pInfo['path'] = path.replace(
                'VERSION', info['versions'])

        pInfo['task'] = self.checkSetupTask(
            pInfo['name'], info['versions'], coexist)
        pInfo['display'] = self.checkDisplayIndex(
            info['name'], pInfo['versions'])

        pInfo['setup'] = os.path.exists(pInfo['install_checks'])

        if coexist and pInfo['setup']:
            pInfo['setup_version'] = info['versions']
        else:
            pInfo['setup_version'] = self.getVersion(pInfo['install_checks'])
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

    def getAllListPage(self, sType='0', page=1, pageSize=50):
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
                        tmp_data = self.makeList(data, sType)
                        for index in range(len(tmp_data)):
                            plugins_info.append(tmp_data[index])
                    except Exception as e:
                        print(e)

        start = (page - 1) * pageSize
        end = start + pageSize
        _plugins_info = plugins_info[start:end]

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

    def getPluginList(self, sType, sPage=1, sPageSize=50):
        # print sType, sPage, sPageSize

        ret = {}
        ret['type'] = json.loads(slemp.readFile(self.__type))
        # plugins_info = self.getAllListThread(sType)
        # plugins_info = self.getAllListProcess(sType)
        data = self.getAllListPage(sType, sPage, sPageSize)
        ret['data'] = data[0]

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
            return slemp.returnJson(False, 'Tolong jangan tambahkan!')
        if len(indexList) > 12:
            return slemp.returnJson(False, 'Beranda hanya dapat menampilkan hingga 12 perangkat lunak!')

        indexList.append(vname)
        slemp.writeFile(self.__index, json.dumps(indexList))
        return slemp.returnJson(True, 'Berhasil ditambahkan!')

    def removeIndex(self, name, version):
        if not os.path.exists(self.__index):
            slemp.writeFile(self.__index, '[]')

        indexList = json.loads(slemp.readFile(self.__index))
        vname = name + '-' + version
        if not vname in indexList:
            return slemp.returnJson(True, 'Berhasil dihapus!')
        indexList.remove(vname)
        slemp.writeFile(self.__index, json.dumps(indexList))
        return slemp.returnJson(True, 'Berhasil dihapus!')

    def run(self, name, func, version='', args='', script='index'):
        path = self.__plugin_dir + \
            '/' + name + '/' + script + '.py'
        py = 'python3 ' + path

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
            return (False, "Plugin tidak ada!")

        sys.path.append(package)
        eval_str = "__import__('" + script + "')." + func + '(' + args + ')'
        newRet = eval(eval_str)
        if slemp.isDebugMode():
            print('callback', eval_str)

        return (True, newRet)
