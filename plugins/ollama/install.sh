#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin:/opt/homebrew/bin
export PATH

DIR=$(cd "$(dirname "$0")"; pwd)
curPath=$DIR
rootPath=$(dirname "$(dirname "$DIR")")
serverPath=$(dirname "$rootPath")
export rootPath
export serverPath

if [ -f ${rootPath}/bin/activate ];then
	source ${rootPath}/bin/activate
fi

action=$1
type=$2

if [ "${2}" == "" ];then
	echo 'Skrip instalasi tidak ditemukan...'
	exit 0
fi

if [ ! -d $curPath/versions/$2 ];then
	echo 'Skrip instalasi tidak ditemukan...'
	exit 0
fi

if [ "${action}" == "uninstall" ];then
	if [ -f /usr/lib/systemd/system/ollama.service ] || [ -f /lib/systemd/system/ollama.service ];then
		systemctl stop ollama
		systemctl disable ollama
		rm -rf /usr/lib/systemd/system/ollama.service
		rm -rf /lib/systemd/system/ollama.service
		systemctl daemon-reload
	fi
fi

sh $curPath/versions/$2/install.sh $1

if [ "${action}" == "install" ] && [ -d $serverPath/ollama ];then
	cd ${rootPath} && python3 ${rootPath}/plugins/ollama/index.py start
	cd ${rootPath} && python3 ${rootPath}/plugins/ollama/index.py initd_install
fi
