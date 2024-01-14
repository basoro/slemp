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

    def getBodyApi(self):
        path = request.form.get('path', '')
        return self.getBody(path)

    def getLastBodyApi(self):
        path = request.form.get('path', '')
        line = request.form.get('line', '100')

        if not os.path.exists(path):
            return slemp.returnJson(False, 'File tidak ada', (path,))

        try:
            data = slemp.getLastLine(path, int(line))
            return slemp.returnJson(True, 'OK', data)
        except Exception as ex:
            return slemp.returnJson(False, u'Tidak dapat membaca file dengan benar!' + str(ex))

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
            return slemp.returnJson(False, 'Nama file tidak boleh berisi karakter khusus!')
        if not os.path.exists(sfile):
            return slemp.returnJson(False, 'File yang ditentukan tidak ada!')

        if not self.checkDir(sfile):
            return slemp.returnJson(False, 'Eittsss... Jangan coba-coba..!!')

        import shutil
        try:
            shutil.move(sfile, dfile)
            msg = slemp.getInfo('Pindahkan file atau direktori [{1}] ke [{2}] berhasil!', (sfile, dfile,))
            slemp.writeLog('Manajemen file', msg)
            return slemp.returnJson(True, 'Pemindahan file atau direktori berhasil!')
        except:
            return slemp.returnJson(False, 'Gagal memindahkan file atau direktori!')

    def deleteApi(self):
        path = request.form.get('path', '')
        return self.delete(path)

    def fileAccessApi(self):
        filename = request.form.get('filename', '')
        data = self.getAccess(filename)
        return slemp.getJson(data)

    def setFileAccessApi(self):

        if slemp.isAppleSystem():
            return slemp.returnJson(True, 'Tidak support untuk MacOS!')

        filename = request.form.get('filename', '')
        user = request.form.get('user', '')
        access = request.form.get('access', '755')
        sall = '-R'
        try:
            if not self.checkDir(filename):
                return slemp.returnJson(False, 'Eittss.. Jangan coba-coba..!!')

            if not os.path.exists(filename):
                return slemp.returnJson(False, 'File yang ditentukan tidak ada!')

            os.system('chmod ' + sall + ' ' + access + " '" + filename + "'")
            os.system('chown ' + sall + ' ' + user +
                      ':' + user + " '" + filename + "'")
            msg = slemp.getInfo(
                'Setel izin [{1}] ke [{2}] pemilik ke [{3}]', (filename, access, user,))
            slemp.writeLog('Manajemen file', msg)
            return slemp.returnJson(True, 'Pengaturan berhasil!')
        except:
            return slemp.returnJson(False, 'Gagal!')

    def getDirSizeApi(self):
        path = request.form.get('path', '')
        tmp = self.getDirSize(path)
        return slemp.returnJson(True, tmp[0].split()[0])

    def getDirApi(self):
        path = request.form.get('path', '')
        if not os.path.exists(path):
            path = slemp.getRootDir() + "/wwwroot"
        search = request.args.get('search', '').strip().lower()
        page = request.args.get('p', '1').strip().lower()
        row = request.args.get('showRow', '10')
        disk = request.form.get('disk', '')
        if disk == 'True':
            row = 1000

        return self.getDir(path, int(page), int(row), search)

    def createFileApi(self):
        file = request.form.get('path', '')
        try:
            if not self.checkFileName(file):
                return slemp.returnJson(False, 'Nama file tidak boleh berisi karakter khusus!')
            if os.path.exists(file):
                return slemp.returnJson(False, 'File yang ditentukan sudah ada!')
            _path = os.path.dirname(file)
            if not os.path.exists(_path):
                os.makedirs(_path)
            open(file, 'w+').close()
            self.setFileAccept(file)
            msg = slemp.getInfo('Buat file [{1}] berhasil!', (file,))
            slemp.writeLog('Manajemen file', msg)
            return slemp.returnJson(True, 'File berhasil dibuat!')
        except Exception as e:
            return slemp.returnJson(True, 'File gagal dibuat!')

    def createDirApi(self):
        path = request.form.get('path', '')
        try:
            if not self.checkFileName(path):
                return slemp.returnJson(False, 'Nama direktori tidak boleh berisi karakter khusus!')
            if os.path.exists(path):
                return slemp.returnJson(False, 'Direktori yang ditentukan sudah ada!')
            os.makedirs(path)
            self.setFileAccept(path)
            msg = slemp.getInfo('Buat direktori [{1}] berhasil!', (path,))
            slemp.writeLog('Manajemen file', msg)
            return slemp.returnJson(True, 'Direktori berhasil dibuat!')
        except Exception as e:
            return slemp.returnJson(False, 'Direktori gagal dibuat!')

    def downloadFileApi(self):
        import db
        import time
        url = request.form.get('url', '')
        path = request.form.get('path', '')
        filename = request.form.get('filename', '')
        execstr = url + '|slemp|' + path + '/' + filename
        execstr = execstr.strip()
        slemp.M('tasks').add('name,type,status,addtime,execstr',
                          ('Unduh berkas [' + filename + ']', 'download', '-1', time.strftime('%Y-%m-%d %H:%M:%S'), execstr))

        slemp.triggerTask()
        return slemp.returnJson(True, 'Menambahkan unduhan ke antrian!')

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
        return slemp.returnJson(True, 'Task dihapus!')

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
        f.save(filename)
        os.chown(filename, p_stat.st_uid, p_stat.st_gid)
        os.chmod(filename, p_stat.st_mode)

        msg = slemp.getInfo('Mengunggah file [{1}] ke [{2}] berhasil!', (filename, path))
        slemp.writeLog('Manajemen file', msg)
        return slemp.returnMsg(True, 'Berhasil diunggah!')

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
            slemp.writeLog('Manajemen file', 'Tempat sampah dimatikan!')
            return slemp.returnJson(True, 'Tempat sampah dimatikan!')
        else:
            slemp.writeFile(c, 'True')
            slemp.writeLog('Manajemen file', 'Tempat sampah dihidupkan!')
            return slemp.returnJson(True, 'Tempat sampah dihidupkan!')

    def reRecycleBinApi(self):
        rPath = self.rPath
        path = request.form.get('path', '')
        dFile = path.replace('_slemp_', '/').split('_t_')[0]
        try:
            import shutil
            shutil.move(rPath + path, dFile)
            msg = slemp.getInfo('Berhasil memindahkan file [{1}] ke recycle bin!', (dFile,))
            slemp.writeLog('Manajemen file', msg)
            return slemp.returnJson(True, 'Pemulihan berhasil!')
        except Exception as e:
            msg = slemp.getInfo('Gagal memulihkan [{1}] dari recycle bin!', (dFile,))
            slemp.writeLog('Manajemen file', msg)
            return slemp.returnJson(False, 'Pemulihan gagal!')

    def delRecycleBinApi(self):
        rPath = self.rPath
        path = request.form.get('path', '')
        empty = request.form.get('empty', '')
        dFile = path.split('_t_')[0]

        if not self.checkDir(path):
            return slemp.returnJson(False, 'Direktori sensitif, tolong jangan main-main!')

        os.system('which chattr && chattr -R -i ' + rPath + path)
        if os.path.isdir(rPath + path):
            import shutil
            shutil.rmtree(rPath + path)
        else:
            os.remove(rPath + path)

        tfile = path.replace('_slemp_', '/').split('_t_')[0]
        msg = slemp.getInfo('{1} benar-benar dihapus dari sampah!', (tfile,))
        slemp.writeLog('Manajemen file', msg)
        return slemp.returnJson(True, msg)

    def getSpeedApi(self):
        data = slemp.getSpeed()
        return slemp.returnJson(True, 'Sampah dikosongkan!', data)

    def closeRecycleBinApi(self):
        rPath = self.rPath
        os.system('which chattr && chattr -R -i ' + rPath)
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
        slemp.writeLog('Manajemen file', 'Sampah dikosongkan!')
        return slemp.returnJson(True, 'Sampah dikosongkan!')

    def deleteDirApi(self):
        path = request.form.get('path', '')
        if not os.path.exists(path):
            return slemp.returnJson(False, 'File yang ditentukan tidak ada!')

        if path.find('.user.ini'):
            os.system("which chattr && chattr -i '" + path + "'")
        try:
            if os.path.exists('data/recycle_bin.pl'):
                if self.mvRecycleBin(path):
                    return slemp.returnJson(True, 'Memindahkan file ke recycle bin!')
            slemp.execShell('rm -rf ' + path)
            slemp.writeLog('Manajemen file', 'Hapus file berhasil!', (path,))
            return slemp.returnJson(True, 'Hapus file berhasil!')
        except:
            return slemp.returnJson(False, 'Gagal menghapus file!')

    def closeLogsApi(self):
        logPath = slemp.getLogsDir()
        os.system('rm -f ' + logPath + '/*')
        os.system('kill -USR1 `cat ' + slemp.getServerDir() +
                  'openresty/nginx/logs/nginx.pid`')
        slemp.writeLog('Manajemen file', 'Log situs telah dihapus!')
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
            return slemp.returnJson(True, 'Penandaan berhasil, silakan klik tombol Paste All di direktori target!')
        elif stype == '3':
            for key in json.loads(data):
                try:
                    filename = path + '/' + key
                    if not self.checkDir(filename):
                        return slemp.returnJson(False, 'Eittss... Jangan coba-coba...!!')
                    os.system('chmod -R ' + access + " '" + filename + "'")
                    os.system('chown -R ' + user + ':' +
                              user + " '" + filename + "'")
                except:
                    continue
            slemp.writeLog('Manajemen file', 'Berhasil mengatur izin dalam batch!')
            return slemp.returnJson(True, 'Berhasil mengatur izin dalam batch!')
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
                            return slemp.returnJson(False, 'Eittss... jangan coba-coba...!')
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
            slemp.writeLog('Manajemen file', 'Batch dihapus dengan sukses!')
            return slemp.returnJson(True, 'Penghapusan batch berhasil!')

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
        import shutil
        if not self.checkDir(path):
            return slemp.returnJson(False, 'Eittss... Jangan coba-coba...!')
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
            msg = slemp.getInfo('Salinan batch dari [{1}] ke [{2}] berhasil',
                             (session['selected']['path'], path,))
            slemp.writeLog('Manajemen file', msg)
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
            msg = slemp.getInfo('Pemindahan batch dari [{1}] ke [{2}] berhasil',
                             (session['selected']['path'], path,))
            slemp.writeLog('Manajemen file', msg)
        slemp.writeSpeed(None, 0, 0)
        errorCount = len(myfiles) - i
        del(session['selected'])
        msg = slemp.getInfo('Operasi batch berhasil [{1}], gagal [{2}]', (str(i), str(errorCount)))
        return slemp.returnJson(True, msg)

    def copyFileApi(self):
        sfile = request.form.get('sfile', '')
        dfile = request.form.get('dfile', '')

        if sfile == dfile:
            return slemp.returnJson(False, 'Sumber dan tujuan!')

        if not os.path.exists(sfile):
            return slemp.returnJson(False, 'File yang ditentukan tidak ada!')

        if os.path.isdir(sfile):
            return self.copyDir(sfile, dfile)

        try:
            import shutil
            shutil.copyfile(sfile, dfile)
            msg = slemp.getInfo('Salin file [{1}] ke [{2}] berhasil!', (sfile, dfile,))
            slemp.writeLog('Manajemen file', msg)
            stat = os.stat(sfile)
            os.chown(dfile, stat.st_uid, stat.st_gid)
            return slemp.returnJson(True, 'File berhasil disalin!')
        except:
            return slemp.returnJson(False, 'Penyalinan file gagal!')

    def copyDir(self, sfile, dfile):

        if not os.path.exists(sfile):
            return slemp.returnJson(False, 'Direktori yang ditentukan tidak ada!')

        if os.path.exists(dfile):
            return slemp.returnJson(False, 'Direktori yang ditentukan sudah ada!')
        import shutil
        try:
            shutil.copytree(sfile, dfile)
            stat = os.stat(sfile)
            os.chown(dfile, stat.st_uid, stat.st_gid)
            msg = slemp.getInfo('Salin direktori [{1}] ke [{2}] berhasil!', (sfile, dfile))
            slemp.writeLog('Manajemen file', msg)
            return slemp.returnJson(True, 'Copy direktori berhasil!')
        except:
            return slemp.returnJson(False, 'Salinan direktori gagal!')

    def checkDir(self, path):
        path = path.replace('//', '/')
        if path[-1:] == '/':
            path = path[:-1]

        nDirs = ('',
                 '/',
                 '/*',
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
        if slemp.getOs() == 'darwin':
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
            slemp.writeLog('Manajemen file', slemp.getInfo(
                'Pindahkan file [{1}] ke recycle bin berhasil!', (path)))
            return True
        except:
            slemp.writeLog('Manajemen file', slemp.getInfo(
                'Gagal memindahkan file [{1}] ke recycle bin!', (path)))
            return False

    def getBody(self, path):
        if not os.path.exists(path):
            return slemp.returnJson(False, 'File tidak ada', (path,))

        if os.path.getsize(path) > 2097152:
            return slemp.returnJson(False, u'File yang lebih besar dari 2MB tidak dapat diedit secara online!')

        fp = open(path, 'rb')
        data = {}
        data['status'] = True
        try:
            if fp:
                from chardet.universaldetector import UniversalDetector
                detector = UniversalDetector()
                srcBody = b""
                for line in fp.readlines():
                    detector.feed(line)
                    srcBody += line
                detector.close()
                char = detector.result
                data['encoding'] = char['encoding']
                if char['encoding'] == 'GB2312' or not char['encoding'] or char[
                        'encoding'] == 'TIS-620' or char['encoding'] == 'ISO-8859-9':
                    data['encoding'] = 'GBK'
                if char['encoding'] == 'ascii' or char[
                        'encoding'] == 'ISO-8859-1':
                    data['encoding'] = 'utf-8'
                if char['encoding'] == 'Big5':
                    data['encoding'] = 'BIG5'
                if not char['encoding'] in ['GBK', 'utf-8', 'BIG5']:
                    data['encoding'] = 'utf-8'
                try:
                    if sys.version_info[0] == 2:
                        data['data'] = srcBody.decode(
                            data['encoding']).encode('utf-8', errors='ignore')
                    else:
                        data['data'] = srcBody.decode(data['encoding'])
                except:
                    data['encoding'] = char['encoding']
                    if sys.version_info[0] == 2:
                        data['data'] = srcBody.decode(
                            data['encoding']).encode('utf-8', errors='ignore')
                    else:
                        data['data'] = srcBody.decode(data['encoding'])
            else:
                if sys.version_info[0] == 2:
                    data['data'] = srcBody.decode('utf-8').encode('utf-8')
                else:
                    data['data'] = srcBody.decode('utf-8')
                data['encoding'] = u'utf-8'

            return slemp.returnJson(True, 'OK', data)
        except Exception as ex:
            return slemp.returnJson(False, u'Pengkodean file tidak kompatibel, file tidak dapat dibaca dengan benar!' + str(ex))

    def saveBody(self, path, data, encoding='utf-8'):
        if not os.path.exists(path):
            return slemp.returnJson(False, 'File tidak ada')
        try:
            if encoding == 'ascii':
                encoding = 'utf-8'
            if sys.version_info[0] == 2:
                data = data.encode(encoding, errors='ignore')
                fp = open(path, 'w+')
            else:
                data = data.encode(
                    encoding, errors='ignore').decode(encoding)
                fp = open(path, 'w+', encoding=encoding)
            fp.write(data)
            fp.close()

            if path.find("web_conf") > 0:
                slemp.restartWeb()

            slemp.writeLog('Manajemen file', 'File berhasil disimpan', (path,))
            return slemp.returnJson(True, 'File berhasil disimpan')
        except Exception as ex:
            return slemp.returnJson(False, 'File gagal disimpan:' + str(ex))

    def zip(self, sfile, dfile, stype, path):
        if sfile.find(',') == -1:
            if not os.path.exists(path + '/' + sfile):
                return slemp.returnMsg(False, 'File yang ditentukan tidak ada!')

        try:
            tmps = slemp.getRunDir() + '/tmp/panelExec.log'
            if stype == 'zip':
                os.system("cd '" + path + "' && zip '" + dfile +
                          "' -r '" + sfile + "' > " + tmps + " 2>&1")
            else:
                sfiles = ''
                for sfile in sfile.split(','):
                    if not sfile:
                        continue
                    sfiles += " '" + sfile + "'"
                os.system("cd '" + path + "' && tar -zcvf '" +
                          dfile + "' " + sfiles + " > " + tmps + " 2>&1")
            self.setFileAccept(dfile)
            slemp.writeLog("Manajemen file", 'Kompresi file berhasil!', (sfile, dfile))
            return slemp.returnJson(True, 'Kompresi file berhasil!')
        except:
            return slemp.returnJson(False, 'Kompresi file gagal!')

    def unzip(self, sfile, dfile, stype, path):

        if not os.path.exists(sfile):
            return slemp.returnMsg(False, 'File yang ditentukan tidak ada!')

        try:
            tmps = slemp.getRunDir() + '/tmp/panelExec.log'
            if stype == 'zip':
                os.system("cd " + path + " && unzip -d '" + dfile +
                          "' '" + sfile + "' > " + tmps + " 2>&1 &")
            else:
                sfiles = ''
                for sfile in sfile.split(','):
                    if not sfile:
                        continue
                    sfiles += " '" + sfile + "'"
                os.system("cd " + path + " && tar -zxvf " + sfiles +
                          " -C " + dfile + " > " + tmps + " 2>&1 &")
            self.setFileAccept(dfile)
            slemp.writeLog("Manajemen file", 'File berhasil didekompresi!', (sfile, dfile))
            return slemp.returnJson(True, 'File berhasil didekompresi!')
        except:
            return slemp.returnJson(False, 'Dekompresi file gagal!')

    def delete(self, path):

        if not os.path.exists(path):
            return slemp.returnJson(False, 'File yang ditentukan tidak ada!')

        if path.find('.user.ini') >= 0:
            os.system("which chattr && chattr -i '" + path + "'")

        try:
            if os.path.exists('data/recycle_bin.pl'):
                if self.mvRecycleBin(path):
                    return slemp.returnJson(True, 'Memindahkan file ke recycle bin!')
            os.remove(path)
            slemp.writeLog('Manajemen file', slemp.getInfo(
                'Hapus file [{1}] berhasil!', (path)))
            return slemp.returnJson(True, 'Hapus file berhasil!')
        except:
            return slemp.returnJson(False, 'Gagal menghapus file!')

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
            i += 1
        return i

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
                link = ''
                if os.path.islink(filePath):
                    filePath = os.readlink(filePath)
                    link = ' -> ' + filePath
                    if not os.path.exists(filePath):
                        filePath = path + '/' + filePath
                    if not os.path.exists(filePath):
                        continue

                stat = os.stat(filePath)
                accept = str(oct(stat.st_mode)[-3:])
                mtime = str(int(stat.st_mtime))
                user = ''
                try:
                    user = pwd.getpwuid(stat.st_uid).pw_name
                except Exception as ee:
                    user = str(stat.st_uid)

                size = str(stat.st_size)
                if os.path.isdir(filePath):
                    dirnames.append(filename + ';' + size + ';' +
                                    mtime + ';' + accept + ';' + user + ';' + link)
                else:
                    filenames.append(filename + ';' + size + ';' +
                                     mtime + ';' + accept + ';' + user + ';' + link)
                n += 1
            except Exception as e:
                continue
        data['DIR'] = sorted(dirnames)
        data['FILES'] = sorted(filenames)
        data['PATH'] = path.replace('//', '/')

        return slemp.getJson(data)
