#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin:/opt/homebrew/bin
export PATH

RED='\033[31m'
GREEN='\033[32m'
YELLOW='\033[33m'
BLUE='\033[34m'
PLAIN='\033[0m'
BOLD='\033[1m'
SUCCESS='[\033[32mOK\033[0m]'
COMPLETE='[\033[32mDONE\033[0m]'
WARN='[\033[33mWARN\033[0m]'
ERROR='[\033[31mERROR\033[0m]'
WORKING='[\033[34m*\033[0m]'

# Path detection
OSNAME=$(uname -s)
if [ "$OSNAME" == "Darwin" ]; then
    DIR=$(cd "$(dirname "$0")"; pwd)
    export rootPath=$(dirname "$DIR")
    export serverPath=$(dirname "$rootPath")
else
    export rootPath="/opt/slemp/server/panel"
    export serverPath="/opt/slemp/server"
fi

LOG_FILE=slemp-install.log
{

HTTP_PREFIX="https://"

if [ -f /etc/motd ];then
    echo "welcome to panel panel" > /etc/motd
fi

startTime=`date +%s`

_os=`uname`
echo "menggunakan sistem: ${_os}"

if [ ${_os} == "Darwin" ]; then
	OSNAME='macos'
elif grep -Eqi "openSUSE" /etc/*-release; then
	OSNAME='opensuse'
	zypper refresh
	zypper install cron wget curl zip unzip
elif grep -Eqi "FreeBSD" /etc/*-release; then
	OSNAME='freebsd'
	pkg install -y wget curl zip unzip unrar rar
elif grep -Eqi "EulerOS" /etc/*-release || grep -Eqi "openEuler" /etc/*-release; then
	OSNAME='euler'
	yum install -y wget curl zip unzip tar crontabs
elif grep -Eqi "CentOS" /etc/issue || grep -Eqi "CentOS" /etc/*-release; then
	OSNAME='rhel'
	yum install -y wget curl zip unzip tar crontabs
elif grep -Eqi "Fedora" /etc/issue || grep -Eqi "Fedora" /etc/*-release; then
	OSNAME='rhel'
	yum install -y wget curl zip unzip tar crontabs
elif grep -Eqi "Rocky" /etc/issue || grep -Eqi "Rocky" /etc/*-release; then
	OSNAME='rhel'
	yum install -y wget curl zip unzip tar crontabs
elif grep -Eqi "Anolis" /etc/issue || grep -Eqi "Anolis" /etc/*-release; then
	OSNAME='rhel'
	yum install -y wget curl zip unzip tar crontabs
elif grep -Eqi "AlmaLinux" /etc/issue || grep -Eqi "AlmaLinux" /etc/*-release; then
	OSNAME='rhel'
	yum install -y wget curl zip unzip tar crontabs
elif grep -Eqi "Amazon Linux" /etc/issue || grep -Eqi "Amazon Linux" /etc/*-release; then
	OSNAME='amazon'
	yum install -y wget curl zip unzip tar crontabs
elif grep -Eqi "Ubuntu" /etc/issue || grep -Eqi "Ubuntu" /etc/os-release; then
	OSNAME='ubuntu'
	apt update -y
	apt install -y wget curl zip unzip tar cron
elif grep -Eqi "Debian" /etc/issue || grep -Eqi "Debian" /etc/os-release; then
	OSNAME='debian'
	apt update -y
	apt install -y wget curl zip unzip tar cron
elif grep -Eqi "Alpine" /etc/issue || grep -Eqi "Alpine" /etc/*-release; then
	OSNAME='alpine'
	apk update
	apk add devscripts -force-broken-world
	apk add wget zip unzip tar -force-broken-world
else
	OSNAME='unknow'
fi

if [ "$EUID" -ne 0 ] && [ "$OSNAME" != "macos" ];then 
	echo "Harap jalankan sebagai root!"
 	exit
fi

echo "OSNAME:${OSNAME}"

if [ $OSNAME != "macos" ];then
	if id www &> /dev/null ;then 
	    echo ""
	else
	    groupadd www
		useradd -g www -s /usr/sbin/nologin www
	fi

	mkdir -p ${serverPath}
	mkdir -p $(dirname "$serverPath")/wwwroot
	mkdir -p $(dirname "$serverPath")/wwwlogs
	mkdir -p $(dirname "$serverPath")/backup/database
	mkdir -p $(dirname "$serverPath")/backup/site

	if [ ! -d ${rootPath} ];then
		curl --insecure -sSLo /tmp/master.tar.gz ${HTTP_PREFIX}github.com/basoro/slemp/archive/refs/heads/master.tar.gz
		cd /tmp && tar -zxvf /tmp/master.tar.gz
		mv -f /tmp/slemp-master ${rootPath}
		rm -rf /tmp/master.tar.gz
		rm -rf /tmp/slemp-master
	fi

	# install acme.sh
	if [ ! -d /root/.acme.sh ];then
	    if [ "$LOCAL_ADDR" != "common" ];then
	        curl --insecure -sSLo /tmp/acme.sh-master.tar.gz ${HTTP_PREFIX}github.com/acmesh-official/acme.sh/archive/refs/heads/master.tar.gz
	        tar xvzf /tmp/acme.sh-master.tar.gz -C /tmp
	        cd /tmp/acme.sh-master
	        bash acme.sh install
	    else
	    	curl -fsSL https://get.acme.sh | bash
	    fi
	fi
fi

echo "menggunakan versi sistem: ${OSNAME}"
if [ "${OSNAME}" == "macos" ];then
	bash scripts/install/macos.sh
else
	cd ${rootPath} && bash scripts/install/${OSNAME}.sh
fi

if [ "${OSNAME}" == "macos" ];then
	echo "macos selesai"
	exit 0
fi

cd ${rootPath} && bash cli.sh start
isStart=`ps -ef|grep 'gunicorn -c setting.py app:app' |grep -v grep|awk '{print $2}'`
n=0
while [ ! -f /etc/rc.d/init.d/slemp ];
do
    echo -e ".\c"
    sleep 1
    let n+=1
    if [ $n -gt 20 ];then
    	echo -e "mulai mw gagal"
    	exit 1
    fi
done

cd ${rootPath} && bash /etc/rc.d/init.d/slemp stop
cd ${rootPath} && bash /etc/rc.d/init.d/slemp start
cd ${rootPath} && bash /etc/rc.d/init.d/slemp default

sleep 2
if [ ! -e /usr/bin/slemp ]; then
	if [ -f /etc/rc.d/init.d/slemp ];then
		ln -s /etc/rc.d/init.d/slemp /usr/bin/slemp
	fi
fi

endTime=`date +%s`
((outTime=(${endTime}-${startTime})/60))
echo -e "Waktu yang dihabiskan:\033[32m $outTime \033[0mMenit!"

} 1> >(tee $LOG_FILE) 2>&1

echo -e "\nInstalasi selesai. Jika terjadi kesalahan, silakan periksa file log slemp-install.log ."