#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin:/opt/homebrew/bin
export PATH

DIR=$(cd "$(dirname "$0")"; pwd)
curPath=$DIR
rootPath=$(dirname "$(dirname "$DIR")")
serverPath=$(dirname "$rootPath")
export rootPath
export serverPath

# cd ${rootPath}/plugins/mariadb && bash install.sh install 8.2
# cd ${rootPath} && source bin/activate && python3 plugins/mariadb/index.py try_slave_sync_bugfix {}
# cd ${rootPath} && source bin/activate && python3 plugins/mariadb/index.py do_full_sync  {"db":"xxx","sign":"","begin":1}
# cd ${rootPath} && source bin/activate && python3 plugins/mariadb/index.py sync_database_repair  {"db":"xxx","sign":""}
# cd ${rootPath} && source bin/activate && python3 plugins/mariadb/index.py init_slave_status
# cd ${rootPath} && source bin/activate && python3 plugins/mariadb/index.py install_pre_inspection


action=$1
type=$2

if id mysql &> /dev/null ;then 
    echo "mysql UID is `id -u mysql`"
    echo "mysql Shell is `grep "^mysql:" /etc/passwd |cut -d':' -f7 `"
else
    groupadd mysql
	useradd -g mysql -s /usr/sbin/nologin mysql
fi

if [ "${2}" == "" ];then
	echo 'Skrip instalasi tidak ditemukan...'
	exit 0
fi 

if [ ! -d $curPath/versions/$2 ];then
	echo 'Skrip instalasi 2 tidak ditemukan...'
	exit 0
fi

if [ "${action}" == "uninstall" ];then
	
	if [ -f /usr/lib/systemd/system/mariadb.service ] || [ -f /lib/systemd/system/mariadb.service ];then
		systemctl stop mariadb
		systemctl disable mariadb
		rm -rf /usr/lib/systemd/system/mariadb.service
		rm -rf /lib/systemd/system/mariadb.service
		systemctl daemon-reload
	fi
fi

sh -x $curPath/versions/$2/install.sh $1

if [ "${action}" == "install" ] && [ -d $serverPath/mariadb ];then
	#Inisialisasi 
	cd ${rootPath} && python3 ${rootPath}/plugins/mariadb/index.py start ${type}
	cd ${rootPath} && python3 ${rootPath}/plugins/mariadb/index.py initd_install ${type}
fi
