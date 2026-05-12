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

    _os=`uname`
    if [ "${_os}" == "Darwin" ]; then
        OSNAME='macos'
    elif grep -Eqi "Ubuntu" /etc/issue || grep -Eqi "Ubuntu" /etc/os-release; then
        OSNAME='ubuntu'
    elif grep -Eqi "Debian" /etc/issue || grep -Eqi "Debian" /etc/os-release; then
        OSNAME='debian'
    else
        OSNAME='linux'
    fi

    if ! command -v node &> /dev/null; then
        if [ "$OSNAME" == "debian" ] || [ "$OSNAME" == "ubuntu" ];then
            apt update -y
            apt install -y nodejs npm
        elif [[ "$OSNAME" == "macos" ]]; then
            if command -v brew &> /dev/null; then
                brew install node
            fi
        fi
    fi

    export NVM_DIR="$HOME/.nvm"
    if [ ! -d "$NVM_DIR" ]; then
        curl -fsLS https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
    fi
    
    if [ -s "$NVM_DIR/nvm.sh" ]; then
        . "$NVM_DIR/nvm.sh"
        if ! command -v node &> /dev/null; then
            nvm install 18
            nvm use 18
        fi
    fi

    if ! command -v pm2 &> /dev/null; then
        if command -v npm &> /dev/null; then
            npm install pm2 -g
        fi
    fi

	if [ ! -d $serverPath/wagw ];then
		wget --no-check-certificate -O $serverPath/wagw.zip https://codeload.github.com/basoro/wagw/zip/refs/heads/master
	fi
	cd $serverPath && unzip wagw.zip
	mv wagw-master wagw
	cd $serverPath/wagw

    if [ -s "$NVM_DIR/nvm.sh" ]; then
        . "$NVM_DIR/nvm.sh"
    fi

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
