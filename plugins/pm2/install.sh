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

Install_pm2()
{
	echo 'Installing PM2 and Node.js...' > $install_tmp

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

	if [ "$OSNAME" == "debian" ] || [ "$OSNAME" == "ubuntu" ];then
		apt update -y
		apt install -y nodejs npm
	elif [[ "$OSNAME" == "macos" ]]; then
        if ! command -v node &> /dev/null; then
            if command -v brew &> /dev/null; then
                brew install node
            else
                echo "Node.js tidak ditemukan dan Homebrew tidak terinstal. Silakan instal Node.js secara manual."
            fi
        fi
	else
		yum install -y nodejs
		curl -fsLS https://npmjs.org/install.sh | sh
	fi

    export NVM_DIR="$HOME/.nvm"
    if [ ! -d "$NVM_DIR" ]; then
        curl -fsLS https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
    fi
    
    if [ -s "$NVM_DIR/nvm.sh" ]; then
        . "$NVM_DIR/nvm.sh"
        nvm install 18
        nvm alias default 18
        nvm use 18
    fi

	if command -v npm &> /dev/null; then
        npm install pm2 -g
    else
        echo "npm tidak ditemukan, instalasi PM2 mungkin gagal."
    fi
 
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
