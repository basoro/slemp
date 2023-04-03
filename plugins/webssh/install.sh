#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH


curPath=`pwd`
rootPath=$(dirname "$curPath")
rootPath=$(dirname "$rootPath")
serverPath=$(dirname "$rootPath")


install_tmp=${rootPath}/tmp/slemp_install.pl

VERSION=$2

Install_webssh()
{
	echo 'Installing script file...' > $install_tmp
	mkdir -p $serverPath/webssh
	echo "${VERSION}" > $serverPath/webssh/version.pl
	echo '安装完成' > $install_tmp

}

Uninstall_webssh()
{
	rm -rf $serverPath/webssh
	echo "uninstall complete" > $install_tmp
}

action=$1
if [ "${1}" == 'install' ];then
	Install_webssh
else
	Uninstall_webssh
fi
