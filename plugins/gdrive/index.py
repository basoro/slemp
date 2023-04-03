# coding:utf-8

from __future__ import print_function

import sys
import io
import os
import json
import time
import re
import string
import subprocess

import os.path
import google.oauth2.credentials
import google_auth_oauthlib.flow

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import MediaIoBaseDownload

sys.path.append(os.getcwd() + "/class/core")
import slemp
import db

def getPluginName():
    return 'gdrive'

def create_auth_url():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
                slemp.getServerDir() + '/gdrive/credentials.json',
                scopes=['https://www.googleapis.com/auth/drive.file'])
    flow.redirect_uri = 'http://localhost:8080/'
    auth_url, state = flow.authorization_url(
        access_type='offline',
        prompt='consent',
        include_granted_scopes='false')
    if os.path.exists('/tmp/auth_url'):
        tmp_exec ="rm -f "+'/tmp/auth_url'
        slemp.execShell(tmp_exec)
    slemp.writeFile("/tmp/auth_url",str(auth_url))
    return auth_url

def start():
    from urllib.parse import urlparse, parse_qs
    import os
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    conf_tpl = slemp.getServerDir() + '/gdrive/authorization.pl'
    url = slemp.readFile(conf_tpl)
    parse_result = urlparse(url)
    dict_result = parse_qs(parse_result.query)

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            slemp.getServerDir() + '/gdrive/credentials.json',
            scopes=['https://www.googleapis.com/auth/drive.file'],
            state=url.split('state=')[1].split('&code=')[0])
    flow.redirect_uri = 'http://localhost:8080/'
    flow.fetch_token(authorization_response=url)
    credentials = flow.credentials

    credentials_data = {}
    credentials_data['credentials'] = {
        'token': credentials.token,
        'id_token': credentials.id_token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes}
    with open(slemp.getServerDir() + '/gdrive/token.json', 'w') as token:
        json.dump(credentials_data,token)
    return 'ok'

def status():
    with open(slemp.getServerDir() + '/gdrive/credentials.json', 'rb') as credential:
        data_cred = json.load(credential)['installed']
    with open(slemp.getServerDir() + '/gdrive/token.json', 'rb') as token:
        data_token = json.load(token)['credentials']
    if data_cred['client_secret'] == data_token['client_secret']:
        return 'start'
    if data_cred['client_secret'] != data_token['client_secret']:
        return 'stop'

def stop():
    cmd_cp = 'cp -rf ' + slemp.getServerDir() + '/panel/plugins/gdrive/token.json ' + slemp.getServerDir() + '/gdrive/token.json'
    slemp.execShell(cmd_cp)
    return 'ok'


def restart():
    stop()
    start()
    return 'ok'


def reload():
    stop()
    start()
    return 'ok'


def getConf():
    return slemp.getServerDir() + '/gdrive/authorization.pl'

def upload():
    if os.path.exists(slemp.getServerDir() + '/gdrive/token.json'):
        with open(slemp.getServerDir() + '/gdrive/token.json', 'rb') as token:
            tmp_data = json.load(token)['credentials']
            creds = google.oauth2.credentials.Credentials(
                tmp_data['token'],
                tmp_data['refresh_token'],
                tmp_data['id_token'],
                tmp_data['token_uri'],
                tmp_data['client_id'],
                tmp_data['client_secret'],
                tmp_data['scopes'])
    service = build('drive', 'v3', credentials=creds)
    results = service.files().list(
    pageSize=10, fields="nextPageToken, files(id, name)").execute()
    results.get('files', [])

    file_metadata = {'name': 'photo.jpg'}
    media = MediaFileUpload('photo.jpg',mimetype='image/jpeg')
    file = service.files().create(body=file_metadata, media_body=media,fields='id').execute()

    return True

def backupSite(name, count):

    sql = db.Sql()
    path = sql.table('sites').where('name=?', (name,)).getField('path')
    startTime = time.time()
    if not path:
        endDate = time.strftime('%Y/%m/%d %X', time.localtime())
        log = "Website [" + name + "] does not exist!"
        print("★[" + endDate + "] " + log)
        print(
            "----------------------------------------------------------------------------")
        return

    backup_path = slemp.getRootDir() + '/backup/site'
    if not os.path.exists(backup_path):
        slemp.execShell("mkdir -p " + backup_path)

    nama_file = "web_" + name + "_" + time.strftime('%Y%m%d_%H%M%S', time.localtime()) + '.tar.gz'
    filename = backup_path + "/" + nama_file
    #slemp.execShell("cd " + os.path.dirname(path) + " && tar zcvf '" + filename + "' '" + os.path.basename(path) + "' > /dev/null")
    slemp.execShell("cd " + os.path.dirname(path) + " && tar zcvf '" + filename + "' '" + os.path.basename(path) + "' > /dev/null")

    endDate = time.strftime('%Y/%m/%d %X', time.localtime())

    print(filename)
    if not os.path.exists(filename):
        log = "Website [" + name + "] backup failed!"
        print("★[" + endDate + "] " + log)
        print(
            "----------------------------------------------------------------------------")
        return

    outTime = time.time() - startTime
    pid = sql.table('sites').where('name=?', (name,)).getField('id')
    sql.table('backup').add('type,name,pid,filename,addtime,size', ('0', os.path.basename(
        filename), pid, filename, endDate, os.path.getsize(filename)))
    log = "Website [" + name + "] backup was successful, time [" + str(round(outTime, 2)) + "] second"
    slemp.writeLog('Scheduled Tasks', log)
    print("★[" + endDate + "] " + log)
    print("|---Keep the latest [" + count + "] backup")
    print("|---File name:" + filename)

    backups = sql.table('backup').where(
        'type=? and pid=?', ('0', pid)).field('id,filename').select()

    num = len(backups) - int(count)
    if num > 0:
        for backup in backups:
            slemp.execShell("rm -f " + backup['filename'])
            sql.table('backup').where('id=?', (backup['id'],)).delete()
            num -= 1
            print("|---Expired backup files have been cleaned up：" + backup['filename'])
            if num < 1:
                break

    if os.path.exists(slemp.getServerDir() + '/gdrive/token.json'):
        with open(slemp.getServerDir() + '/gdrive/token.json', 'rb') as token:
            tmp_data = json.load(token)['credentials']
            creds = google.oauth2.credentials.Credentials(
                tmp_data['token'],
                tmp_data['refresh_token'],
                tmp_data['id_token'],
                tmp_data['token_uri'],
                tmp_data['client_id'],
                tmp_data['client_secret'],
                tmp_data['scopes'])
    service = build('drive', 'v3', credentials=creds)

    file_metadata = {'name': nama_file}
    media = MediaFileUpload(filename, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media,fields='id').execute()
    print("|---Sukses")

    return True

def backupDatabase(name, count):
    db_path = slemp.getServerDir() + '/mysql'
    db_name = 'mysql'
    name = slemp.M('databases').dbPos(db_path, 'mysql').where(
        'name=?', (name,)).getField('name')
    startTime = time.time()
    if not name:
        endDate = time.strftime('%Y/%m/%d %X', time.localtime())
        log = "Database [" + name + "] does not exist!"
        print("★[" + endDate + "] " + log)
        print(
            "----------------------------------------------------------------------------")
        return

    backup_path = slemp.getRootDir() + '/backup/database'
    if not os.path.exists(backup_path):
        slemp.execShell("mkdir -p " + backup_path)

    nama_file = "db_" + name + "_" + time.strftime('%Y%m%d_%H%M%S', time.localtime()) + ".sql.gz"
    filename = backup_path + "/" + nama_file

    import re
    mysql_root = slemp.M('config').dbPos(db_path, db_name).where(
        "id=?", (1,)).getField('mysql_root')

    mycnf = slemp.readFile(db_path + '/etc/my.cnf')
    rep = "\[mysqldump\]\nuser=root"
    sea = "[mysqldump]\n"
    subStr = sea + "user=root\npassword=" + mysql_root + "\n"
    mycnf = mycnf.replace(sea, subStr)
    if len(mycnf) > 100:
        slemp.writeFile(db_path + '/etc/my.cnf', mycnf)

    slemp.execShell(db_path + "/bin/mysqldump --opt --default-character-set=utf8 " +
                 name + " | gzip > " + filename)

    if not os.path.exists(filename):
        endDate = time.strftime('%Y/%m/%d %X', time.localtime())
        log = "Database [" + name + "] backup failed!"
        print("★[" + endDate + "] " + log)
        print(
            "----------------------------------------------------------------------------")
        return

    mycnf = slemp.readFile(db_path + '/etc/my.cnf')
    mycnf = mycnf.replace(subStr, sea)
    if len(mycnf) > 100:
        slemp.writeFile(db_path + '/etc/my.cnf', mycnf)

    endDate = time.strftime('%Y/%m/%d %X', time.localtime())
    outTime = time.time() - startTime
    pid = slemp.M('databases').dbPos(db_path, db_name).where(
        'name=?', (name,)).getField('id')

    slemp.M('backup').add('type,name,pid,filename,addtime,size', (1, os.path.basename(
        filename), pid, filename, endDate, os.path.getsize(filename)))
    log = "Database [" + name + "] backup was successful, time [" + str(round(outTime, 2)) + "] second"
    slemp.writeLog('Scheduled Tasks', log)
    print("★[" + endDate + "] " + log)
    print("|---Keep the latest [" + count + "] backup")
    print("|---File name:" + filename)

    backups = slemp.M('backup').where(
        'type=? and pid=?', ('1', pid)).field('id,filename').select()

    num = len(backups) - int(count)
    if num > 0:
        for backup in backups:
            slemp.execShell("rm -f " + backup['filename'])
            slemp.M('backup').where('id=?', (backup['id'],)).delete()
            num -= 1
            print("|---Expired backup files have been cleaned up：" + backup['filename'])
            if num < 1:
                break

    if os.path.exists(slemp.getServerDir() + '/gdrive/token.json'):
        with open(slemp.getServerDir() + '/gdrive/token.json', 'rb') as token:
            tmp_data = json.load(token)['credentials']
            creds = google.oauth2.credentials.Credentials(
                tmp_data['token'],
                tmp_data['refresh_token'],
                tmp_data['id_token'],
                tmp_data['token_uri'],
                tmp_data['client_id'],
                tmp_data['client_secret'],
                tmp_data['scopes'])
    service = build('drive', 'v3', credentials=creds)

    file_metadata = {'name': nama_file}
    media = MediaFileUpload(filename, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media,fields='id').execute()
    print("|---Sukses")

    return True

def backupSiteAll(save):
    sites = slemp.M('sites').field('name').select()
    for site in sites:
        backupSite(site['name'], save)

def backupDatabaseAll(save):
    db_path = slemp.getServerDir() + '/mysql'
    db_name = 'mysql'
    databases = slemp.M('databases').dbPos(
        db_path, db_name).field('name').select()
    for database in databases:
        backupDatabase(database['name'], save)

def upload_file(self,get=None,data_type=None):
    if os.path.exists(slemp.getServerDir() + '/gdrive/token.json'):
        with open(slemp.getServerDir() + '/gdrive/token.json', 'rb') as token:
            tmp_data = json.load(token)['credentials']
            creds = google.oauth2.credentials.Credentials(
                tmp_data['token'],
                tmp_data['refresh_token'],
                tmp_data['id_token'],
                tmp_data['token_uri'],
                tmp_data['client_id'],
                tmp_data['client_secret'],
                tmp_data['scopes'])

    if isinstance(get,str):
        filename = get
        get = getObject
        get.filepath = self.build_object_name(data_type,filename)
        get.path = ''
        get.filename = filename
    filename = self._get_filename(get.filename)
    parents = self._create_folder_cycle(get.filepath)
    drive_service = build('drive', 'v3', credentials=creds)
    file_metadata = {'name': filename, 'parents': [parents]}
    media = MediaFileUpload(get.filename, resumable=True)
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print('Upload Success ,File ID: %s' % file.get('id'))
    return True

def build_object_name(self, data_type,file_name):
    prefix_dict = {
        "site": "web",
        "database": "db",
        "path": "path",
    }
    file_regx = prefix_dict.get(data_type) + "_(.+)_20\d+_\d+\."
    sub_search = re.search(file_regx.lower(), file_name)
    sub_path_name = ""
    if sub_search:
        sub_path_name = sub_search.groups()[0]
        sub_path_name += '/'
    object_name = 'backup/{}/{}'.format(data_type,sub_path_name)

    if object_name[:1] == "/":
        object_name = object_name[1:]
    return object_name

def _get_filename(self,filename):
    l = filename.split("/")
    return l[-1]

def _create_folder_cycle(self,filepath):
    l = filepath.split("/")
    fid_list = []
    for i in l:
        if not i:
            continue
        fid = self.__get_folder_id(i)
        if fid:
            fid_list.append(fid)
            continue
        if not fid_list:
            fid_list.append("")
        fid_list.append(self.create_folder(i,fid_list[-1]))
    return fid_list[-1]

def _create_folder_cycle(self,filepath):
    l = filepath.split("/")
    fid_list = []
    for i in l:
        if not i:
            continue
        fid = self.__get_folder_id(i)
        if fid:
            fid_list.append(fid)
            continue
        if not fid_list:
            fid_list.append("")
        fid_list.append(self.create_folder(i,fid_list[-1]))
    return fid_list[-1]

def __get_folder_id(self, floder_name):
    service = build('drive', 'v3', credentials=self.__creds)
    results = service.files().list(pageSize=10, q="name='{}' and mimeType='application/vnd.google-apps.folder'".format(floder_name),fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])
    if not items:
        return []
    else:
        for item in items:
            return item["id"]

def create_folder(self,folder_name,parents=""):
    print("folder_name: {}\nparents: {}".format(folder_name,parents))
    service = build('drive', 'v3', credentials=self.__creds)
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parents:
        file_metadata['parents'] = [parents]
    folder = service.files().create(body=file_metadata,fields='id').execute()
    print('Create Folder ID: %s' % folder.get('id'))
    return folder.get('id')

if __name__ == "__main__":
    func = sys.argv[1]
    if func == 'site':
        if sys.argv[2] == 'ALL':
            print(backupSiteAll(sys.argv[3]))
        else:
            print(backupSite(sys.argv[2], sys.argv[3]))
    elif func == 'database':
        if sys.argv[2] == 'ALL':
            print(backupDatabaseAll(sys.argv[3]))
        else:
            print(backupDatabase(sys.argv[2], sys.argv[3]))
    elif func == 'status':
        print(status())
    elif func == 'start':
        print(start())
    elif func == 'stop':
        print(stop())
    elif func == 'restart':
        print(restart())
    elif func == 'reload':
        print(reload())
    elif func == 'conf':
        print(getConf())
    elif func == 'auth_url':
        print(create_auth_url())
    elif func == 'set_auth_url':
        print(set_auth_url())
    elif func == 'upload':
        print(upload())
    else:
        print('error')
