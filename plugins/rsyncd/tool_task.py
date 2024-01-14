# coding:utf-8

import sys
import io
import os
import time
import json

sys.path.append(os.getcwd() + "/class/core")
import slemp


app_debug = False
if slemp.isAppleSystem():
    app_debug = True


def getPluginName():
    return 'rsyncd'


def getPluginDir():
    return slemp.getPluginDir() + '/' + getPluginName()


def getServerDir():
    return slemp.getServerDir() + '/' + getPluginName()


def getTaskConf():
    conf = getServerDir() + "/task_config.json"
    return conf


def getConfigData():
    try:
        return json.loads(slemp.readFile(getTaskConf()))
    except:
        pass
    return []


def getConfigTpl():
    tpl = {
        "name": "",
        "task_id": -1,
    }
    return tpl


def createBgTask(data):
    removeBgTask()
    for d in data:
        if d['realtime'] == "false":
            createBgTaskByName(d['name'], d)


def createBgTaskByName(name, args):
    cfg = getConfigTpl()
    _name = "[勿删]同步插件定时任务[" + name + "]"
    res = slemp.M("crontab").field("id, name").where("name=?", (_name,)).find()
    if res:
        return True

    if "task_id" in cfg.keys() and cfg["task_id"] > 0:
        res = slemp.M("crontab").field("id, name").where(
            "id=?", (cfg["task_id"],)).find()
        if res and res["id"] == cfg["task_id"]:
            print("计划任务已经存在!")
            return True
    import crontab_api
    api = crontab_api.crontab_api()

    period = args['period']
    _hour = ''
    _minute = ''
    _where1 = ''
    _type_day = "day"
    if period == 'day':
        _type_day = 'day'
        _hour = args['hour']
        _minute = args['minute']
    elif period == 'minute-n':
        _type_day = 'minute-n'
        _where1 = args['minute-n']
        _minute = ''

    cmd = '''
rname=%s
plugin_path=%s
logs_file=$plugin_path/send/${rname}/run.log
''' % (name, getServerDir())
    cmd += 'echo "★【`date +"%Y-%m-%d %H:%M:%S"`】 STSRT" >> $logs_file' + "\n"
    cmd += 'echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>" >> $logs_file' + "\n"
    cmd += 'bash $plugin_path/send/${rname}/cmd >> $logs_file 2>&1' + "\n"
    cmd += 'echo "【`date +"%Y-%m-%d %H:%M:%S"`】 END★" >> $logs_file' + "\n"
    cmd += 'echo "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<" >> $logs_file' + "\n"

    params = {
        'name': _name,
        'type': _type_day,
        'week': "",
        'where1': _where1,
        'hour': _hour,
        'minute': _minute,
        'save': "",
        'backup_to': "",
        'stype': "toShell",
        'sname': '',
        'sbody': cmd,
        'urladdress': '',
    }

    task_id = api.add(params)
    if task_id > 0:
        cfg["task_id"] = task_id
        cfg["name"] = name

        _dd = getConfigData()
        _dd.append(cfg)
        slemp.writeFile(getTaskConf(), json.dumps(_dd))


def removeBgTask():
    cfg_list = getConfigData()
    for x in range(len(cfg_list)):
        cfg = cfg_list[x]
        if "task_id" in cfg.keys() and cfg["task_id"] > 0:
            res = slemp.M("crontab").field("id, name").where(
                "id=?", (cfg["task_id"],)).find()
            if res and res["id"] == cfg["task_id"]:
                import crontab_api
                api = crontab_api.crontab_api()
                data = api.delete(cfg["task_id"])
                if data[0]:
                    cfg["task_id"] = -1
                    cfg_list[x] = cfg
                    slemp.writeFile(getTaskConf(), '[]')
                    return True
    return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        action = sys.argv[1]
        if action == "remove":
            removeBgTask()
        elif action == "add":
            createBgTask()
