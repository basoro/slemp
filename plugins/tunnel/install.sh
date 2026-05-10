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


Install_Plugin()
{

	echo 'Installing script file...' > $install_tmp
	mkdir -p $serverPath/tunnel
	touch $serverPath/tunnel/key.pl
	if [ ! -f $serverPath/tunnel/client ];then
		if [ "$OSNAME" == "Darwin" ];then
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
