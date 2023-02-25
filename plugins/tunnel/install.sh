#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

curPath=`pwd`
rootPath=$(dirname "$curPath")
rootPath=$(dirname "$rootPath")
serverPath=$(dirname "$rootPath")
sysName=`uname`

install_tmp=${rootPath}/tmp/slemp_install.pl


sysName=`uname`
echo "use system: ${sysName}"

if [ ${sysName} == "Darwin" ]; then
	OSNAME='macos'
elif grep -Eqi "CentOS" /etc/issue || grep -Eq "CentOS" /etc/*-release; then
	OSNAME='centos'
elif grep -Eqi "Fedora" /etc/issue || grep -Eq "Fedora" /etc/*-release; then
	OSNAME='fedora'
elif grep -Eqi "Debian" /etc/issue || grep -Eq "Debian" /etc/*-release; then
	OSNAME='debian'
elif grep -Eqi "Ubuntu" /etc/issue || grep -Eq "Ubuntu" /etc/*-release; then
	OSNAME='ubuntu'
elif grep -Eqi "Raspbian" /etc/issue || grep -Eq "Raspbian" /etc/*-release; then
	OSNAME='raspbian'
else
	OSNAME='unknow'
fi


Install_Plugin()
{

	echo 'Installing script file...' > $install_tmp
	mkdir -p $serverPath/tunnel
	touch $serverPath/tunnel/key.pl
	if [ ! -f $serverPath/tunnel/client ];then
		if [ "$sysName" == "Darwin" ];then
			wget -O $serverPath/tunnel/client http://metro.basoro.id:8090/apps/client_darwin_amd64
		else
			wget -O $serverPath/tunnel/client http://metro.basoro.id:8090/apps/client_linux_amd64
		fi
	fi
	chmod +x $serverPath/tunnel/client
	echo '0.1' > $serverPath/tunnel/version.pl
	echo 'The installation is complete' > $install_tmp
}

Uninstall_Plugin()
{
	rm -rf $serverPath/tunnel
	echo "Uninstall" > $install_tmp
}

action=$1
if [ "${1}" == 'install' ];then
	Install_Plugin
else
	Uninstall_Plugin
fi
