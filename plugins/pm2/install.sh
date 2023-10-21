#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH


curPath=`pwd`
rootPath=$(dirname "$curPath")
rootPath=$(dirname "$rootPath")
serverPath=$(dirname "$rootPath")


install_tmp=${rootPath}/tmp/slemp_install.pl

Install_pm2()
{
	echo 'Installing script file...' > $install_tmp
	yum install -y nodejs
	#curl -o- http://npmjs.org/install.sh | bash
	curl -fsLS http://npmjs.org/install.sh | sh
	npm install pm2 -g
	curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.34.0/install.sh | bash
	#curl -fsLS https://raw.githubusercontent.com/creationix/nvm/v0.34.0/install.sh | sh

	mkdir -p $serverPath/pm2
	echo '1.0' > $serverPath/pm2/version.pl
	echo 'The installation is complete' > $install_tmp
}

Uninstall_pm2()
{
	rm -rf $serverPath/pm2
	echo "Uninstall complete" > $install_tmp
}

action=$1
if [ "${1}" == 'install' ];then
	Install_pm2
else
	Uninstall_pm2
fi
