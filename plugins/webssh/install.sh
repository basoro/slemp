#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH


curPath=`pwd`
rootPath=$(dirname "$curPath")
rootPath=$(dirname "$rootPath")
serverPath=$(dirname "$rootPath")


install_tmp=${rootPath}/tmp/slemp_install.pl


Install_webssh()
{
	echo 'installing script file...' > $install_tmp
	mkdir -p $serverPath/webssh
	echo '1.0' > $serverPath/webssh/version.pl
	echo 'The installation is complete' > $install_tmp

}

Uninstall_webssh()
{
	rm -rf $serverPath/webssh
	echo "Uninstall complete" > $install_tmp
}

action=$1
if [ "${1}" == 'install' ];then
	Install_webssh
else
	Uninstall_webssh
fi
