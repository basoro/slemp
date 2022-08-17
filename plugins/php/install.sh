#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

curPath=`pwd`
rootPath=$(dirname "$curPath")
rootPath=$(dirname "$rootPath")
serverPath=$(dirname "$rootPath")

install_tmp=${rootPath}/tmp/slemp_install.pl

if id www &> /dev/null ;then
    echo "www UID is `id -u www`"
    echo "www Shell is `grep "^www:" /etc/passwd |cut -d':' -f7 `"
else
    groupadd www
	# useradd -g www -s /sbin/nologin www
	useradd -g www -s /bin/bash www
fi

action=$1
type=$2

if [ "${2}" == "" ];then
	echo 'Missing installation script...' > $install_tmp
	exit 0
fi

if [ ! -d $curPath/versions/$2 ];then
	echo 'Missing install script 2...' > $install_tmp
	exit 0
fi

if [ "${action}" == "uninstall" ];then

	if [ -f /usr/lib/systemd/system/php${type}.service ] || [ -f /lib/systemd/system/php${type}.service ] ;then
		systemctl stop php${type}
		systemctl disable php${type}
		rm -rf /usr/lib/systemd/system/php${type}.service
		rm -rf /lib/systemd/system/php${type}.service
		systemctl daemon-reload
	fi
fi

cd ${curPath} && sh -x $curPath/versions/$2/install.sh $1

if [ "${action}" == "install" ] && [ -d ${serverPath}/php/${type} ];then
	cd ${rootPath} && python3 ${rootPath}/plugins/php/index.py start ${type}
	cd ${rootPath} && python3 ${rootPath}/plugins/php/index.py initd_install ${type}
fi
