#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:/opt/homebrew/bin:~/bin
export PATH

# Path detection
OSNAME=$(uname -s)
if [ "$OSNAME" == "Darwin" ]; then
    script_dir=$(cd "$(dirname "$0")" && pwd)
    rootPath=$(dirname "$(dirname "$script_dir")")
    serverPath=$(dirname "$rootPath")
else
    rootPath="/opt/slemp/server/panel"
    serverPath="/opt/slemp/server"
fi
install_tmp=${rootPath}/tmp/slemp_install.pl

echo $OSNAME

Install_Plugin()
{

	echo 'Installing script file...' > $install_tmp
	if [ ! -d $serverPath/wagw ];then
		wget --no-check-certificate -O $serverPath/wagw.zip https://codeload.github.com/basoro/wagw/zip/refs/heads/master
	fi
	cd $serverPath && unzip wagw.zip
	mv wagw-master wagw
	cd $serverPath/wagw
	source ~/.nvm/nvm.sh
	echo 'Installing WA Gateway module dependency...'
	echo 'Please wait......'
	#npm install
	echo '0.1' > $serverPath/wagw/version.pl
	rm -f $serverPath/wagw.zip
	echo 'The installation is complete' > $install_tmp
}

Uninstall_Plugin()
{
	rm -rf $serverPath/wagw
	echo "Uninstall" > $install_tmp
}

action=$1
if [ "${1}" == 'install' ];then
	Install_Plugin
else
	Uninstall_Plugin
fi
