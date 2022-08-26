#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

curPath=`pwd`
rootPath=$(dirname "$curPath")
rootPath=$(dirname "$rootPath")
serverPath=$(dirname "$rootPath")
sysName=`uname`

install_tmp=${rootPath}/tmp/mw_install.pl


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

	if [ $sysName == 'Darwin' ]; then
		pip install -I pyOpenSSL
		pip install -I google-api-python-client==2.39.0 google-auth-httplib2==0.1.0 google-auth-oauthlib==0.5.0 -i https://pypi.Python.org/simple
		pip install -I httplib2==0.18.1 -i https://pypi.Python.org/simple
	else
		$serverPath/panel/bin/pip install -I pyOpenSSL
		$serverPath/panel/bin/pip install -I google-api-python-client==2.39.0 google-auth-httplib2==0.1.0 google-auth-oauthlib==0.5.0 -i https://pypi.Python.org/simple
		$serverPath/panel/bin/pip install -I httplib2==0.18.1 -i https://pypi.Python.org/simple
		$serverPath/panel/bin/pip install cryptography==3.3.2
	fi

	mkdir -p $serverPath/gdrive
	cp $serverPath/panel/plugins/gdrive/credentials.json $serverPath/gdrive/credentials.json
	cp $serverPath/panel/plugins/gdrive/token.json $serverPath/gdrive/token.json
	cp $serverPath/panel/plugins/gdrive/hook_backup.json $serverPath/panel/data/hook_backup.json
	touch $serverPath/gdrive/authorization.pl
	echo '0.1' > $serverPath/gdrive/version.pl
	echo 'The installation is complete' > $install_tmp
}

Uninstall_Plugin()
{
	rm -rf $serverPath/gdrive
	echo "Uninstall" > $install_tmp
}

action=$1
if [ "${1}" == 'install' ];then
	Install_Plugin
else
	Uninstall_Plugin
fi
