#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH


curPath=`pwd`
rootPath=$(dirname "$curPath")
rootPath=$(dirname "$rootPath")
serverPath=$(dirname "$rootPath")

bash ${rootPath}/scripts/getos.sh
OSNAME=`cat ${rootPath}/data/osname.pl`

echo $OSNAME
install_tmp=${rootPath}/tmp/slemp_install.pl

Install_pm2()
{
	echo 'Installing script file...' > $install_tmp

	if [ "$OSNAME" == "debian" ] || [ "$OSNAME" == "ubuntu" ];then
		apt install -y nodejs npm
	elif [[ "$OSNAME" == "macos" ]]; then
		# brew install nodejs
		# brew install npm
		echo "ok"
	else
		yum install -y nodejs
		curl -fsLS http://npmjs.org/install.sh | sh
	fi

	#curl -o- http://npmjs.org/install.sh | bash
	npm install pm2 -g
	#curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.34.0/install.sh | bash
	curl -fsLS https://raw.githubusercontent.com/creationix/nvm/v0.34.0/install.sh | sh
	nvm install 18.20.4
	source ~/.nvm/nvm.sh
	nvm alias default 18.20.4
	nvm use 18.20.4
 
 
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
