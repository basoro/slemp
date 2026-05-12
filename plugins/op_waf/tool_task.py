# coding:utf-8

import sys
import io
import os
import time
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + "/class/core")
import slemp
import crontab_api
MwCrontab = crontab_api.crontab_api()


app_debug = False
if slemp.isAppleSystem():
    app_debug = True


def getPluginName():
    return 'op_waf'


def getPluginDir():
    return slemp.getPluginDir() + '/' + getPluginName()


def getServerDir():
    return slemp.getServerDir() + '/' + getPluginName()


def getTaskConf():
    conf = getServerDir() + "/task_config.json"
    return conf


def getConfigData():
    conf = getTaskConf()
    if os.path.exists(conf):
        return json.loads(slemp.readFile(getTaskConf()))
    return {
        "task_id": -1,
        "period": "day-n",
        "where1": "7",
        "hour": "0",
        "minute": "15",
    }


def createBgTask():
    removeBgTask()
    createBgTaskByName(getPluginName())


def createBgTaskByName(name):
    cfg = getConfigData()

    _name = "[JANGAN DIHAPUS] Tugas Latar Belakang Firewall WAF"
    res = slemp.M("crontab").field("id, name").where("name=?", (_name,)).find()
    if res:
        return True

    if "task_id" in cfg.keys() and cfg["task_id"] > 0:
        res = slemp.M("crontab").field("id, name").where(
            "id=?", (cfg["task_id"],)).find()
        if res and res["id"] == cfg["task_id"]:
            print("Tugas terjadwal sudah ada!")
            return True

    mw_dir = slemp.getRunDir()
    cmd = '''
mw_dir=%s
rname=%s
plugin_path=%s
script_path=%s
logs_file=$plugin_path/${rname}.log
''' % (mw_dir, name, getServerDir(), getPluginDir())
    cmd += 'echo "★【`date +"%Y-%m-%d %H:%M:%S"`】 STSRT★" >> $logs_file' + "\n"
    cmd += 'echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>" >> $logs_file' + "\n"

    cmd += 'echo "cd $mw_dir && source bin/activate && python3 $script_path/tool_task.py run >> $logs_file 2>&1"' + "\n"
    cmd += 'cd $mw_dir && source bin/activate && python3 $script_path/tool_task.py run >> $logs_file 2>&1' + "\n"


    cmd += 'echo "【`date +"%Y-%m-%d %H:%M:%S"`】 END★" >> $logs_file' + "\n"
    cmd += 'echo "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<" >> $logs_file' + "\n"

    params = {
        'name': _name,
        'type': cfg['period'],
        'week': "",
        'where1': cfg['where1'],
        'hour': cfg['hour'],
        'minute': cfg['minute'],
        'save': "",
        'backup_to': "",
        'stype': "toShell",
        'sname': '',
        'sbody': cmd,
        'urladdress': '',
    }

    task_id = MwCrontab.add(params)
    if task_id > 0:
        cfg["task_id"] = task_id        
        slemp.writeFile(getTaskConf(), json.dumps(cfg))


def removeBgTask():
    cfg = getConfigData()
    for x in range(len(cfg)):
        if "task_id" in cfg.keys() and cfg["task_id"] > 0:
            res = slemp.M("crontab").field("id, name").where(
                "id=?", (cfg["task_id"],)).find()
            if res and res["id"] == cfg["task_id"]:
                data = MwCrontab.delete(cfg["task_id"])
                if data['status']:
                    cfg["task_id"] = -1
                    slemp.writeFile(getTaskConf(), json.dumps(cfg))
                    return True
    return False


def getCpuUsed():
    path = getServerDir() + "/cpu.info"
    if slemp.isAppleSystem():
        import psutil
        used = psutil.cpu_percent(interval=1)
        slemp.writeFile(path, str(int(used)))
    else:
        cmd = "top -bn 1 | fgrep 'Cpu(s)' | awk '{print 100 -$8}' | awk -F . '{print $1}'"
        data = slemp.execShell(cmd)
        slemp.writeFile(path, str(int(data[0].strip())))


def pSqliteDb(dbname='logs'):
    db_dir = getServerDir() + '/logs/'
    conn = slemp.M(dbname).dbPos(db_dir, "waf")

    conn.execute("PRAGMA synchronous = 0")
    conn.execute("PRAGMA cache_size = 8000")
    conn.execute("PRAGMA page_size = 32768")
    conn.execute("PRAGMA journal_mode = wal")
    conn.execute("PRAGMA journal_size_limit = 1073741824")
    return conn

def run():
    now_t = int(time.time())
    logs_conn = pSqliteDb('logs')
    del_hot_log = "delete from logs where time<{}".format(now_t)
    print(del_hot_log)
    r = logs_conn.execute(del_hot_log)
    return 'ok'


if __name__ == "__main__":
    if len(sys.argv) > 1:
        action = sys.argv[1]
        if action == "remove":
            removeBgTask()
        elif action == "add":
            createBgTask()
        elif action == "run":
            run()
