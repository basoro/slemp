#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:/opt/homebrew/bin:~/bin
export PATH
# LANG=en_US.UTF-8
is64bit=`getconf LONG_BIT`
# Set PANEL_DIR to the directory where the script is located (repo root)
# If running from a standalone script, it will default to the current directory or a fixed path
if [ -f "$(dirname "$0")/../cli.sh" ]; then
    PANEL_DIR=$(cd "$(dirname "$0")/../"; pwd)
else
    PANEL_DIR="/opt/slemp/server/panel"
fi
DEV=$(dirname "$PANEL_DIR")

{

if [ -f /etc/motd ];then
    echo "Welcome to SLEMP Panel" > /etc/motd
fi

startTime=`date +%s`

_os=`uname`
echo "use system: ${_os}"

if [ "$EUID" -ne 0 ] && [ "${_os}" != "Darwin" ]; then
  echo "Please run as root!"
  exit
fi

if [ ${_os} == "Darwin" ]; then
	OSNAME='macos'
elif grep -Eqi "openSUSE" /etc/*-release; then
	OSNAME='opensuse'
	zypper refresh
	zypper install cron wget curl zip unzip
elif grep -Eqi "FreeBSD" /etc/*-release; then
	OSNAME='freebsd'
elif grep -Eqi "CentOS" /etc/issue || grep -Eqi "CentOS" /etc/*-release; then
	OSNAME='rhel'
	yum install -y wget curl zip unzip tar crontabs
elif grep -Eqi "Fedora" /etc/issue || grep -Eqi "Fedora" /etc/*-release; then
	OSNAME='rhel'
	yum install -y wget curl zip unzip tar crontabs
elif grep -Eqi "Rocky" /etc/issue || grep -Eqi "Rocky" /etc/*-release; then
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
else
	OSNAME='unknow'
fi


if [ $OSNAME != "macos" ];then
	if id www &> /dev/null ;then
	  echo ""
	else
	  groupadd www
		useradd -g www -s /bin/bash www
	fi

	mkdir -p $DEV/server
	mkdir -p $DEV/wwwroot
	mkdir -p $DEV/wwwlogs
	mkdir -p $DEV/backup/database
	mkdir -p $DEV/backup/site

	if [ ! -d $PANEL_DIR ];then
		echo "Downloading SLEMP Panel..."
		curl --insecure -sSLo /tmp/master.zip https://codeload.github.com/basoro/slemp/zip/master
		(
			cd /tmp
			unzip -q master.zip
			mv -f slemp-master "$PANEL_DIR"
			rm -rf master.zip
		)
	fi

	# install acme.sh
	if [ ! -d /root/.acme.sh ];then
	    if [ ! -z "$cn" ];then
	        curl --insecure -sSL -o /tmp/acme.tar.gz https://ghproxy.com/github.com/acmesh-official/acme.sh/archive/master.tar.gz
	        tar xvzf /tmp/acme.tar.gz -C /tmp
	        (cd /tmp/acme.sh-master && bash acme.sh install)
	    fi

	    if [ ! -d /root/.acme.sh ];then
	        curl  https://get.acme.sh | sh
	    fi
	fi
fi



echo "use system version: ${OSNAME}"

cd $PANEL_DIR && bash scripts/install/${OSNAME}.sh

if [ "${OSNAME}" == "macos" ];then
	echo "macos end"
	exit 0
fi

INIT_DIR="/etc/init.d"
if [ -d /etc/rc.d/init.d ];then
	INIT_DIR="/etc/rc.d/init.d"
fi

cd $PANEL_DIR && bash cli.sh start
isStart=`ps -ef|grep 'gunicorn -c setting.py app:app' |grep -v grep|awk '{print $2}'`
n=0
while [ ! -f ${INIT_DIR}/slemp ];
do
    echo -e ".\c"
    sleep 1
    let n+=1
    if [ $n -gt 20 ];then
    	echo -e "start slemp fail"
    	exit 1
    fi
done

cd $PANEL_DIR && bash ${INIT_DIR}/slemp stop
cd $PANEL_DIR && bash ${INIT_DIR}/slemp start
cd $PANEL_DIR && bash ${INIT_DIR}/slemp default

sleep 2
if [ ! -e /usr/bin/slemp ]; then
	if [ -f ${INIT_DIR}/slemp ];then
		ln -s ${INIT_DIR}/slemp /usr/bin/slemp
	fi
fi

endTime=`date +%s`
((outTime=(${endTime}-${startTime})/60))
echo -e "Time consumed:\033[32m $outTime \033[0mMinute!"

} 1> >(tee slemp-install.log) 2>&1

echo -e "\nInstall completed. If error occurs, please contact us with the log file slemp-install.log ."
