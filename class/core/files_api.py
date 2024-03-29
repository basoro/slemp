# coding: utf-8

import psutil
import time
import os
import sys
import slemp
import re
import json
import pwd
import shutil

from flask import request
from flask import send_file, send_from_directory
from flask import make_response
from flask import session


class files_api:

    rPath = None

    def __init__(self):
        self.rPath = slemp.getRootDir() + '/recycle_bin/'

    ##### ----- start ----- ###
    def getBodyApi(self):
        path = request.form.get('path', '')
        return self.getBody(path)

    def getLastBodyApi(self):
        path = request.form.get('path', '')
        line = request.form.get('line', '100')

        if not os.path.exists(path):
            return slemp.returnJson(False, 'File does not exist', (path,))

        try:
            data = slemp.getLastLine(path, int(line))
            return slemp.returnJson(True, 'OK', data)
        except Exception as ex:
            return slemp.returnJson(False, 'Could not read the file correctly!' + str(ex))

    def saveBodyApi(self):
        path = request.form.get('path', '')
        data = request.form.get('data', '')
        encoding = request.form.get('encoding', '')
        return self.saveBody(path, data, encoding)

    def downloadApi(self):
        filename = request.args.get('filename', '')
        if not os.path.exists(filename):
            return ''
        response = make_response(send_from_directory(
            os.path.dirname(filename), os.path.basename(filename), as_attachment=True))
        return response

    def zipApi(self):
        sfile = request.form.get('sfile', '')
        dfile = request.form.get('dfile', '')
        stype = request.form.get('type', '')
        path = request.form.get('path', '')
        return self.zip(sfile, dfile, stype, path)

    def unzipApi(self):
        sfile = request.form.get('sfile', '')
        dfile = request.form.get('dfile', '')
        stype = request.form.get('type', '')
        path = request.form.get('path', '')
        return self.unzip(sfile, dfile, stype, path)

    def mvFileApi(self):
        sfile = request.form.get('sfile', '')
        dfile = request.form.get('dfile', '')
        if not self.checkFileName(dfile):
            return slemp.returnJson(False, 'Filenames cannot contain special characters!')
        if not os.path.exists(sfile):
            return slemp.returnJson(False, 'The specified file does not exist!')

        if not self.checkDir(sfile):
            return slemp.returnJson(False, 'FILE_DANGER')

        import shutil
        try:
            shutil.move(sfile, dfile)
            msg = slemp.getInfo('Move or rename file [{1}] to [{2}] successfully!', (sfile, dfile,))
            slemp.writeLog('File management', msg)
            return slemp.returnJson(True, 'File moved or renamed successfully!')
        except:
            return slemp.returnJson(False, 'Failed to move or rename file!')

    def deleteApi(self):
        path = request.form.get('path', '')
        return self.delete(path)

    def fileAccessApi(self):
        filename = request.form.get('filename', '')
        data = self.getAccess(filename)
        return slemp.getJson(data)

    def setFileAccessApi(self):

        if slemp.isAppleSystem():
            return slemp.returnJson(True, 'The development machine does not set!')

        filename = request.form.get('filename', '')
        user = request.form.get('user', '')
        access = request.form.get('access', '755')
        sall = '-R'
        try:
            if not self.checkDir(filename):
                return slemp.returnJson(False, 'Please don\'t play tricks')

            if not os.path.exists(filename):
                return slemp.returnJson(False, 'The specified file does not exist!')

            os.system('chmod ' + sall + ' ' + access + " '" + filename + "'")
            os.system('chown ' + sall + ' ' + user +
                      ':' + user + " '" + filename + "'")
            msg = slemp.getInfo(
                'Set [{1}] permission to [{2}] owner to [{3}]', (filename, access, user,))
            slemp.writeLog('File management', msg)
            return slemp.returnJson(True, 'Successfully set!')
        except:
            return slemp.returnJson(False, 'Setup failed!')

    def getDirSizeApi(self):
        path = request.form.get('path', '')
        tmp = self.getDirSize(path)
        return slemp.returnJson(True, tmp[0].split()[0])

    def getDirApi(self):
        path = request.form.get('path', '')
        if not os.path.exists(path):
            path = slemp.getRootDir() + "/wwwroot"
        search = request.args.get('search', '').strip().lower()
        search_all = request.args.get('all', '').strip().lower()
        page = request.args.get('p', '1').strip().lower()
        row = request.args.get('showRow', '10')
        disk = request.form.get('disk', '')
        if disk == 'True':
            row = 1000

        # return self.getAllDir(path, int(page), int(row), "wp-inlcude")
        if search_all == 'yes' and search != '':
            return self.getAllDir(path, int(page), int(row), search)
        return self.getDir(path, int(page), int(row), search)

    def createFileApi(self):
        file = request.form.get('path', '')
        try:
            if not self.checkFileName(file):
                return slemp.returnJson(False, 'Filenames cannot contain special characters!')
            if os.path.exists(file):
                return slemp.returnJson(False, 'The specified file already exists!')
            _path = os.path.dirname(file)
            if not os.path.exists(_path):
                os.makedirs(_path)
            open(file, 'w+').close()
            self.setFileAccept(file)
            msg = slemp.getInfo('File [{1}] created successfully!', (file,))
            slemp.writeLog('File management', msg)
            return slemp.returnJson(True, 'File created successfully!')
        except Exception as e:
            return slemp.returnJson(True, 'File creation failed!')

    def createDirApi(self):
        path = request.form.get('path', '')
        try:
            if not self.checkFileName(path):
                return slemp.returnJson(False, 'Directory names cannot contain special characters!')
            if os.path.exists(path):
                return slemp.returnJson(False, 'The specified directory already exists!')
            os.makedirs(path)
            self.setFileAccept(path)
            msg = slemp.getInfo('Creating directory [{1}] succeeded!', (path,))
            slemp.writeLog('File management', msg)
            return slemp.returnJson(True, 'Directory created successfully!')
        except Exception as e:
            return slemp.returnJson(False, 'Directory creation failed!')

    def downloadFileApi(self):
        import db
        import time
        url = request.form.get('url', '')
        path = request.form.get('path', '')
        filename = request.form.get('filename', '')
        execstr = url + '|slemp|' + path + '/' + filename
        execstr = execstr.strip()
        slemp.M('tasks').add('name,type,status,addtime,execstr',
                          ('Download file [' + filename + ']', 'download', '-1', time.strftime('%Y-%m-%d %H:%M:%S'), execstr))

        # self.setFileAccept(path + '/' + filename)
        slemp.triggerTask()
        return slemp.returnJson(True, 'Added download task to queue!')

    def removeTaskRecursion(self, pid):
        cmd = "ps -ef|grep " + pid + \
            " | grep -v grep |sed -n '2,1p' | awk '{print $2}'"
        sub_pid = slemp.execShell(cmd)

        if sub_pid[0].strip() == '':
            return 'ok'

        self.removeTaskRecursion(sub_pid[0].strip())
        slemp.execShell('kill -9 ' + sub_pid[0].strip())
        return sub_pid[0].strip()

    def removeTaskApi(self):
        import system_api
        mid = request.form.get('id', '')
        try:
            name = slemp.M('tasks').where('id=?', (mid,)).getField('name')
            status = slemp.M('tasks').where('id=?', (mid,)).getField('status')
            slemp.M('tasks').delete(mid)
            if status == '-1':
                task_pid = slemp.execShell(
                    "ps aux | grep 'task.py' | grep -v grep |awk '{print $2}'")

                task_list = task_pid[0].strip().split("\n")
                for i in range(len(task_list)):
                    self.removeTaskRecursion(task_list[i])

                slemp.triggerTask()
                system_api.system_api().restartTask()
        except:
            system_api.system_api().restartTask()

        task_log = slemp.getRunDir() + "/tmp/panelTask.pl"
        if os.path.exists(task_log):
            os.remove(task_log)
        return slemp.returnJson(True, 'Task deleted!')

    def uploadFileApi(self):
        from werkzeug.utils import secure_filename
        from flask import request

        path = request.args.get('path', '')

        if not os.path.exists(path):
            os.makedirs(path)
        f = request.files['zunfile']
        filename = os.path.join(path, f.filename)

        s_path = path
        if os.path.exists(filename):
            s_path = filename
        p_stat = os.stat(s_path)

        # print(filename)
        f.save(filename)
        os.chown(filename, p_stat.st_uid, p_stat.st_gid)
        os.chmod(filename, p_stat.st_mode)

        msg = slemp.getInfo('Upload file [{1}] to [{2}] successfully!', (filename, path))
        slemp.writeLog('File management', msg)
        return slemp.returnMsg(True, 'Uploaded successfully!')

    def setMode(self, path):
        s_path = os.path.dirname(path)
        p_stat = os.stat(s_path)
        os.chown(path, p_stat.st_uid, p_stat.st_gid)
        os.chmod(path, p_stat.st_mode)

    def uploadSegmentApi(self):
        path = request.form.get('path', '')
        name = request.form.get('name', '')
        size = request.form.get('size')
        start = request.form.get('start')
        dir_mode = request.form.get('dir_mode', '')
        file_mode = request.form.get('file_mode', '')

        if not slemp.fileNameCheck(name):
            return slemp.returnJson(False, 'Filenames cannot contain special characters!')

        if path == '/':
            return slemp.returnJson(False, 'Cannot upload files directly to the system root directory!')

        if name.find('./') != -1 or path.find('./') != -1:
            return slemp.returnJson(False, 'Wrong parameter')

        if not os.path.exists(path):
            os.makedirs(path, 493)
            if not dir_mode != '' or not file_mode != '':
                slemp.setMode(path)

        save_path = os.path.join(
            path, name + '.' + str(int(size)) + '.upload.tmp')
        d_size = 0
        if os.path.exists(save_path):
            d_size = os.path.getsize(save_path)

        if d_size != int(start):
            return str(d_size)

        f = open(save_path, 'ab')
        b64_data = request.form.get('b64_data', '0')
        if b64_data == '1':
            import base64
            b64_data = base64.b64decode(args.b64_data)
            f.write(b64_data)
        else:
            upload_files = request.files.getlist("blob")
            for tmp_f in upload_files:
                f.write(tmp_f.read())

        f.close()
        f_size = os.path.getsize(save_path)
        if f_size != int(size):
            return str(f_size)

        new_name = os.path.join(path, name)
        if os.path.exists(new_name):
            if new_name.find('.user.ini') != -1:
                slemp.execShell("chattr -i " + new_name)
            try:
                os.remove(new_name)
            except:
                slemp.execShell("rm -f %s" % new_name)

        os.renames(save_path, new_name)

        if dir_mode != '' and dir_mode != '':
            mode_tmp1 = dir_mode.split(',')
            slemp.setMode(path, mode_tmp1[0])
            slemp.setOwn(path, mode_tmp1[1])
            mode_tmp2 = file_mode.split(',')
            slemp.setMode(new_name, mode_tmp2[0])
            slemp.setOwn(new_name, mode_tmp2[1])
        else:
            self.setMode(new_name)

        msg = slemp.getInfo('Upload file [{1}] to [{2}] successfully!', (new_name, path))
        slemp.writeLog('File management', msg)
        return slemp.returnMsg(True, 'Uploaded successfully!')

    def getRecycleBinApi(self):
        rPath = self.rPath
        if not os.path.exists(rPath):
            os.system('mkdir -p ' + rPath)
        data = {}
        data['dirs'] = []
        data['files'] = []
        data['status'] = os.path.exists('data/recycle_bin.pl')
        data['status_db'] = os.path.exists('data/recycle_bin_db.pl')
        for file in os.listdir(rPath):
            try:
                tmp = {}
                fname = rPath + file
                tmp1 = file.split('_slemp_')
                tmp2 = tmp1[len(tmp1) - 1].split('_t_')
                tmp['rname'] = file
                tmp['dname'] = file.replace('_slemp_', '/').split('_t_')[0]
                tmp['name'] = tmp2[0]
                tmp['time'] = int(float(tmp2[1]))
                if os.path.islink(fname):
                    filePath = os.readlink(fname)
                    link = ' -> ' + filePath
                    if os.path.exists(filePath):
                        tmp['size'] = os.path.getsize(filePath)
                    else:
                        tmp['size'] = 0
                else:
                    tmp['size'] = os.path.getsize(fname)
                if os.path.isdir(fname):
                    data['dirs'].append(tmp)
                else:
                    data['files'].append(tmp)
            except Exception as e:
                continue
        return slemp.returnJson(True, 'OK', data)

    def recycleBinApi(self):
        c = 'data/recycle_bin.pl'
        db = request.form.get('db', '')
        if db != '':
            c = 'data/recycle_bin_db.pl'
        if os.path.exists(c):
            os.remove(c)
            slemp.writeLog('File management', 'Trash is turned off!')
            return slemp.returnJson(True, 'Trash is turned off!')
        else:
            slemp.writeFile(c, 'True')
            slemp.writeLog('File management', 'Trash feature is turned on!')
            return slemp.returnJson(True, 'Trash feature is turned on!')

    def reRecycleBinApi(self):
        rPath = self.rPath
        path = request.form.get('path', '')
        dFile = path.replace('_slemp_', '/').split('_t_')[0]
        try:
            import shutil
            shutil.move(rPath + path, dFile)
            msg = slemp.getInfo('Moved file [{1}] to the recycle bin successfully!', (dFile,))
            slemp.writeLog('File management', msg)
            return slemp.returnJson(True, 'Recovery succeeded!')
        except Exception as e:
            msg = slemp.getInfo('Restoring [{1}] from recycle bin failed!', (dFile,))
            slemp.writeLog('File management', msg)
            return slemp.returnJson(False, 'Recovery failed!')

    def delRecycleBinApi(self):
        rPath = self.rPath
        path = request.form.get('path', '')
        empty = request.form.get('empty', '')
        dFile = path.split('_t_')[0]

        if not self.checkDir(path):
            return slemp.returnJson(False, 'Sensitive directory, please don\'t play tricks!')

        slemp.execShell('which chattr && chattr -R -i ' + rPath + path)
        if os.path.isdir(rPath + path):
            import shutil
            shutil.rmtree(rPath + path)
        else:
            os.remove(rPath + path)

        tfile = path.replace('_slemp_', '/').split('_t_')[0]
        msg = slemp.getInfo('{1} has been completely deleted from the recycle bin!', (tfile,))
        slemp.writeLog('File management', msg)
        return slemp.returnJson(True, msg)

    def getSpeedApi(self):
        data = slemp.getSpeed()
        return slemp.returnJson(True, 'Trash emptied!', data)

    def closeRecycleBinApi(self):
        rPath = self.rPath
        slemp.execShell('which chattr && chattr -R -i ' + rPath)
        rlist = os.listdir(rPath)
        i = 0
        l = len(rlist)
        for name in rlist:
            i += 1
            path = rPath + name
            slemp.writeSpeed(name, i, l)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        slemp.writeSpeed(None, 0, 0)
        slemp.writeLog('File management', 'Trash emptied!')
        return slemp.returnJson(True, 'Trash emptied!')

    def deleteDirApi(self):
        path = request.form.get('path', '')
        if not os.path.exists(path):
            return slemp.returnJson(False, 'The specified file does not exist!')

        if path.find('.user.ini'):
            os.system("which chattr && chattr -i '" + path + "'")
        try:
            if os.path.exists('data/recycle_bin.pl'):
                if self.mvRecycleBin(path):
                    return slemp.returnJson(True, 'File moved to trash!')
            slemp.execShell('rm -rf ' + path)
            slemp.writeLog('File management', 'File deleted successfully!', (path,))
            return slemp.returnJson(True, 'File deleted successfully!')
        except:
            return slemp.returnJson(False, 'Failed to delete file!')

    def closeLogsApi(self):
        logPath = slemp.getLogsDir()
        os.system('rm -f ' + logPath + '/*')
        os.system('kill -USR1 `cat ' + slemp.getServerDir() +
                  'openresty/nginx/logs/nginx.pid`')
        slemp.writeLog('File management', 'Website logs have been cleared!')
        tmp = self.getDirSize(logPath)
        return slemp.returnJson(True, tmp[0].split()[0])

    def setBatchDataApi(self):
        path = request.form.get('path', '')
        stype = request.form.get('type', '')
        access = request.form.get('access', '')
        user = request.form.get('user', '')
        data = request.form.get('data')
        if stype == '1' or stype == '2':
            session['selected'] = {
                'path': path,
                'type': stype,
                'access': access,
                'user': user,
                'data': data
            }
            return slemp.returnJson(True, 'The mark is successful, please click the paste all button in the target directory!')
        elif stype == '3':
            for key in json.loads(data):
                try:
                    filename = path + '/' + key
                    if not self.checkDir(filename):
                        return slemp.returnJson(False, 'FILE_DANGER')
                    os.system('chmod -R ' + access + " '" + filename + "'")
                    os.system('chown -R ' + user + ':' +
                              user + " '" + filename + "'")
                except:
                    continue
            slemp.writeLog('File management', 'Successfully set permissions in batches!')
            return slemp.returnJson(True, 'Successfully set permissions in batches!')
        else:
            import shutil
            isRecyle = os.path.exists('data/recycle_bin.pl')
            data = json.loads(data)
            l = len(data)
            i = 0
            for key in data:
                try:
                    filename = path + '/' + key
                    topath = filename
                    if not os.path.exists(filename):
                        continue

                    i += 1
                    slemp.writeSpeed(key, i, l)
                    if os.path.isdir(filename):
                        if not self.checkDir(filename):
                            return slemp.returnJson(False, 'Please don\'t play tricks!')
                        if isRecyle:
                            self.mvRecycleBin(topath)
                        else:
                            shutil.rmtree(filename)
                    else:
                        if key == '.user.ini':
                            os.system('which chattr && chattr -i ' + filename)
                        if isRecyle:
                            self.mvRecycleBin(topath)
                        else:
                            os.remove(filename)
                except:
                    continue
                slemp.writeSpeed(None, 0, 0)
            slemp.writeLog('File management', 'Bulk deletion succeeded!')
            return slemp.returnJson(True, 'Batch deletion succeeded!')

    def checkExistsFilesApi(self):
        dfile = request.form.get('dfile', '')
        filename = request.form.get('filename', '')
        data = []
        filesx = []
        if filename == '':
            filesx = json.loads(session['selected']['data'])
        else:
            filesx.append(filename)

        for fn in filesx:
            if fn == '.':
                continue
            filename = dfile + '/' + fn
            if os.path.exists(filename):
                tmp = {}
                stat = os.stat(filename)
                tmp['filename'] = fn
                tmp['size'] = os.path.getsize(filename)
                tmp['mtime'] = str(int(stat.st_mtime))
                data.append(tmp)
        return slemp.returnJson(True, 'ok', data)

    def batchPasteApi(self):
        path = request.form.get('path', '')
        stype = request.form.get('type', '')
        # filename = request.form.get('filename', '')
        import shutil
        if not self.checkDir(path):
            return slemp.returnJson(False, 'Please don\'t play tricks!')
        i = 0
        myfiles = json.loads(session['selected']['data'])
        l = len(myfiles)
        if stype == '1':
            for key in myfiles:
                i += 1
                slemp.writeSpeed(key, i, l)
                try:

                    sfile = session['selected'][
                        'path'] + '/' + key
                    dfile = path + '/' + key

                    if os.path.isdir(sfile):
                        shutil.copytree(sfile, dfile)
                    else:
                        shutil.copyfile(sfile, dfile)
                    stat = os.stat(sfile)
                    os.chown(dfile, stat.st_uid, stat.st_gid)
                except:
                    continue
            msg = slemp.getInfo('Batch copy from [{1}] to [{2}] succeeded',
                             (session['selected']['path'], path,))
            slemp.writeLog('File management', msg)
        else:
            for key in myfiles:
                try:
                    i += 1
                    slemp.writeSpeed(key, i, l)

                    sfile = session['selected'][
                        'path'] + '/' + key
                    dfile = path + '/' + key

                    shutil.move(sfile, dfile)
                except:
                    continue
            msg = slemp.getInfo('Batch move from [{1}] to [{2}] succeeded',
                             (session['selected']['path'], path,))
            slemp.writeLog('File management', msg)
        slemp.writeSpeed(None, 0, 0)
        errorCount = len(myfiles) - i
        del(session['selected'])
        msg = slemp.getInfo('Batch operation succeeded [{1}], failed [{2}]', (str(i), str(errorCount)))
        return slemp.returnJson(True, msg)

    def copyFileApi(self):
        sfile = request.form.get('sfile', '')
        dfile = request.form.get('dfile', '')

        if sfile == dfile:
            return slemp.returnJson(False, 'Source meets purpose!')

        if not os.path.exists(sfile):
            return slemp.returnJson(False, 'The specified file does not exist!')

        if os.path.isdir(sfile):
            return self.copyDir(sfile, dfile)

        try:
            import shutil
            shutil.copyfile(sfile, dfile)
            msg = slemp.getInfo('Copy file [{1}] to [{2}] successfully!', (sfile, dfile,))
            slemp.writeLog('File management', msg)
            stat = os.stat(sfile)
            os.chown(dfile, stat.st_uid, stat.st_gid)
            return slemp.returnJson(True, 'File copied successfully!')
        except:
            return slemp.returnJson(False, 'File copy failed!')

    ##### ----- end ----- ###

    def copyDir(self, sfile, dfile):

        if not os.path.exists(sfile):
            return slemp.returnJson(False, 'The specified directory does not exist!')

        if os.path.exists(dfile):
            return slemp.returnJson(False, 'The specified directory already exists!')
        import shutil
        try:
            shutil.copytree(sfile, dfile)
            stat = os.stat(sfile)
            os.chown(dfile, stat.st_uid, stat.st_gid)
            msg = slemp.getInfo('Copy directory [{1}] to [{2}] successfully!', (sfile, dfile))
            slemp.writeLog('File management', msg)
            return slemp.returnJson(True, 'Directory copied successfully!')
        except:
            return slemp.returnJson(False, 'Directory copy failed!')

    def checkDir(self, path):
        # path = str(path, encoding='utf-8')
        path = path.replace('//', '/')
        if path[-1:] == '/':
            path = path[:-1]

        nDirs = ('',
                 '/',
                 '/*',
                 '/www',
                 '/root',
                 '/boot',
                 '/bin',
                 '/etc',
                 '/home',
                 '/dev',
                 '/sbin',
                 '/var',
                 '/usr',
                 '/tmp',
                 '/sys',
                 '/proc',
                 '/media',
                 '/mnt',
                 '/opt',
                 '/lib',
                 '/srv',
                 '/selinux',
                 '/home/slemp/server',
                 slemp.getRootDir())

        return not path in nDirs

    def getDirSize(self, path):
        if slemp.isAppleSystem():
            tmp = slemp.execShell('du -sh ' + path)
        else:
            tmp = slemp.execShell('du -sbh ' + path)
        return tmp

    def checkFileName(self, filename):
        nots = ['\\', '&', '*', '|', ';']
        if filename.find('/') != -1:
            filename = filename.split('/')[-1]
        for n in nots:
            if n in filename:
                return False
        return True

    def setFileAccept(self, filename):
        auth = 'www:www'
        if slemp.getOs() == 'darwin':
            user = slemp.execShell(
                "who | sed -n '2, 1p' |awk '{print $1}'")[0].strip()
            auth = user + ':staff'

        os.system('chown -R ' + auth + ' ' + filename)
        os.system('chmod -R 755 ' + filename)

    def mvRecycleBin(self, path):
        rPath = self.rPath
        if not os.path.exists(rPath):
            os.system('mkdir -p ' + rPath)

        rFile = rPath + path.replace('/', '_slemp_') + '_t_' + str(time.time())
        try:
            import shutil
            shutil.move(path, rFile)
            slemp.writeLog('File management', slemp.getInfo(
                'Moved file [{1}] to the recycle bin successfully!', (path)))
            return True
        except:
            slemp.writeLog('File management', slemp.getInfo(
                'Failed to move file [{1}] to recycle bin!', (path)))
            return False

    def getBody(self, path):
        if not os.path.exists(path):
            return slemp.returnJson(False, 'File does not exist', (path,))

        if os.path.getsize(path) > 2097152:
            return slemp.returnJson(False, 'Files larger than 2MB cannot be edited online!')

        if os.path.isdir(path):
            return slemp.returnJson(False, 'This is not a file!')

        fp = open(path, 'rb')
        data = {}
        data['status'] = True
        if fp:
            srcBody = fp.read()
            fp.close()

            encoding_list = ['utf-8', 'GBK', 'BIG5']
            for el in encoding_list:
                try:
                    data['encoding'] = el
                    data['data'] = srcBody.decode(data['encoding'])
                    break
                except Exception as ex:
                    if el == 'BIG5':
                        return slemp.returnJson(False, 'The file encoding is not compatible, and the file cannot be read correctly!' + str(ex))
        else:
            return slemp.returnJson(False, 'File not opening normally!')

        return slemp.returnJson(True, 'OK', data)

    def saveBody(self, path, data, encoding='utf-8'):
        if not os.path.exists(path):
            return slemp.returnJson(False, 'File does not exist')
        try:
            if encoding == 'ascii':
                encoding = 'utf-8'

            data = data.encode(
                encoding, errors='ignore').decode(encoding)
            fp = open(path, 'w+', encoding=encoding)
            fp.write(data)
            fp.close()

            if path.find("web_conf") > 0:
                slemp.restartWeb()

            slemp.writeLog('File management', 'File saved successfully', (path,))
            return slemp.returnJson(True, 'File saved successfully')
        except Exception as ex:
            return slemp.returnJson(False, 'File save error: ' + str(ex))

    def zip(self, sfile, dfile, stype, path):
        if sfile.find(',') == -1:
            if not os.path.exists(path + '/' + sfile):
                return slemp.returnMsg(False, 'The specified file does not exist!')

        try:
            tmps = slemp.getRunDir() + '/tmp/panelExec.log'
            if stype == 'zip':
                slemp.execShell("cd '" + path + "' && zip '" + dfile +
                             "' -r '" + sfile + "' > " + tmps + " 2>&1")
            else:
                sfiles = ''
                for sfile in sfile.split(','):
                    if not sfile:
                        continue
                    sfiles += " '" + sfile + "'"
                slemp.execShell("cd '" + path + "' && tar -zcvf '" +
                             dfile + "' " + sfiles + " > " + tmps + " 2>&1")
            self.setFileAccept(dfile)
            slemp.writeLog("File management", 'File compressed successfully!', (sfile, dfile))
            return slemp.returnJson(True, 'File compressed successfully!')
        except:
            return slemp.returnJson(False, 'File compression failed!')

    def unzip(self, sfile, dfile, stype, path):

        if not os.path.exists(sfile):
            return slemp.returnMsg(False, 'The specified file does not exist!')

        try:
            tmps = slemp.getRunDir() + '/tmp/panelExec.log'
            if stype == 'zip':
                slemp.execShell("cd " + path + " && unzip -o -d '" + dfile +
                             "' '" + sfile + "' > " + tmps + " 2>&1 &")
            else:
                sfiles = ''
                for sfile in sfile.split(','):
                    if not sfile:
                        continue
                    sfiles += " '" + sfile + "'"
                slemp.execShell("cd " + path + " && tar -zxvf " + sfiles +
                             " -C " + dfile + " > " + tmps + " 2>&1 &")

            self.setFileAccept(dfile)
            slemp.writeLog("File management", 'The file was decompressed successfully!', (sfile, dfile))
            return slemp.returnJson(True, 'The file was decompressed successfully!')
        except:
            return slemp.returnJson(False, 'File decompression failed!')

    def delete(self, path):

        if not os.path.exists(path):
            return slemp.returnJson(False, 'The specified file does not exist!')

        if path.find('.user.ini') >= 0:
            slemp.execShell("which chattr && chattr -i '" + path + "'")

        try:
            if os.path.exists('data/recycle_bin.pl'):
                if self.mvRecycleBin(path):
                    return slemp.returnJson(True, 'File moved to trash!')
            os.remove(path)
            slemp.writeLog('File management', slemp.getInfo(
                'File [{1}] deleted successfully!', (path)))
            return slemp.returnJson(True, 'File deleted successfully!')
        except:
            return slemp.returnJson(False, 'Failed to delete file!')

    def getAccess(self, filename):
        data = {}
        try:
            stat = os.stat(filename)
            data['chmod'] = str(oct(stat.st_mode)[-3:])
            data['chown'] = pwd.getpwuid(stat.st_uid).pw_name
        except:
            data['chmod'] = 755
            data['chown'] = 'www'
        return data

    def getCount(self, path, search):
        i = 0
        for name in os.listdir(path):
            if search:
                if name.lower().find(search) == -1:
                    continue
            if name == '.':
                continue
            i += 1
        return i

    def getAllDir(self, path, page=1, page_size=10, search=None):
        # print("search:", search)
        data = {}
        dirnames = []
        filenames = []

        count = 0
        max_limit = 3000

        for d_list in os.walk(path):
            if count >= max_limit:
                break

            for d in d_list[1]:
                if count >= max_limit:
                    break
                if d.lower().find(search) != -1:
                    filename = d_list[0] + '/' + d
                    if not os.path.exists(filename):
                        continue
                    dirnames.append(self.__get_stats(filename, path))
                    count += 1

            for f in d_list[2]:
                if count >= max_limit:
                    break

                if f.lower().find(search) != -1:
                    filename = d_list[0] + '/' + f
                    if not os.path.exists(filename):
                        continue
                    filenames.append(self.__get_stats(filename, path))
                    count += 1

        data['DIR'] = sorted(dirnames)
        data['FILES'] = sorted(filenames)
        data['PATH'] = path.replace('//', '/')

        info = {}
        info['count'] = len(dirnames) + len(filenames)
        info['row'] = page_size
        info['p'] = page
        info['tojs'] = 'getFiles'
        pageObj = slemp.getPageObject(info, '1,2,3,4,5,6,7,8')
        data['PAGE'] = pageObj[0]

        return slemp.getJson(data)

    def getDir(self, path, page=1, page_size=10, search=None):
        data = {}
        dirnames = []
        filenames = []

        info = {}
        info['count'] = self.getCount(path, search)
        info['row'] = page_size
        info['p'] = page
        info['tojs'] = 'getFiles'
        pageObj = slemp.getPageObject(info, '1,2,3,4,5,6,7,8')
        data['PAGE'] = pageObj[0]

        i = 0
        n = 0
        for filename in os.listdir(path):
            if search:
                if filename.lower().find(search) == -1:
                    continue
            i += 1
            if n >= pageObj[1].ROW:
                break
            if i < pageObj[1].SHIFT:
                continue
            try:
                filePath = path + '/' + filename
                if not os.path.exists(filePath):
                    continue

                file_stats = self.__get_stats(filePath, path)
                if os.path.isdir(filePath):
                    dirnames.append(file_stats)
                else:
                    filenames.append(file_stats)
                n += 1
            except Exception as e:
                continue
        data['DIR'] = sorted(dirnames)
        data['FILES'] = sorted(filenames)
        data['PATH'] = path.replace('//', '/')

        return slemp.getJson(data)

    def execShellApi(self):
        shell = request.form.get('shell', '').strip()
        path = request.form.get('path', '').strip()
        disabled = ['vi', 'vim', 'top', 'passwd', 'su']
        tmp = shell.split(' ')
        if tmp[0] in disabled:
            return slemp.returnJson(False, 'Do not execute [{}]'.format(tmp[0]))
        shellStr = '''#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
cd %s
%s
''' % (path, shell)
        slemp.writeFile('/tmp/panelShell.sh', shellStr)
        slemp.execShell(
            'nohup bash /tmp/panelShell.sh > /tmp/panelShell.pl 2>&1 &')
        return slemp.returnJson(True, 'ok')

    def getExecShellMsgApi(self):
        fileName = '/tmp/panelShell.pl'
        if not os.path.exists(fileName):
            return ''
        status = not slemp.processExists('bash', None, '/tmp/panelShell.sh')
        return slemp.returnJson(status, slemp.getNumLines(fileName, 200))

    def __get_stats(self, filename, path=None):
        filename = filename.replace('//', '/')
        try:
            stat = os.stat(filename)
            accept = str(oct(stat.st_mode)[-3:])
            mtime = str(int(stat.st_mtime))
            user = ''
            try:
                user = str(pwd.getpwuid(stat.st_uid).pw_name)
            except:
                user = str(stat.st_uid)
            size = str(stat.st_size)
            link = ''
            if os.path.islink(filename):
                link = ' -> ' + os.readlink(filename)

            if path:
                tmp_path = (path + '/').replace('//', '/')
                filename = filename.replace(tmp_path, '', 1)

            return filename + ';' + size + ';' + mtime + ';' + accept + ';' + user + ';' + link
        except Exception as e:
            # print(e)
            return ';;;;;'
