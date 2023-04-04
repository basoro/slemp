#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
# LANG=en_US.UTF-8
is64bit=`getconf LONG_BIT`

{

if [ -f /etc/motd ];then
    echo "Welcome to SLEMP Panel" > /etc/motd
fi

startTime=`date +%s`

_os=`uname`
echo "use system: ${_os}"

if [ "$EUID" -ne 0 ]
  then echo "Please run as root!"
  exit
fi

if [ ${_os} == "Darwin" ]; then
	OSNAME='macos'
elif grep -Eq "openSUSE" /etc/*-release; then
	OSNAME='opensuse'
	zypper refresh
	zypper install cron wget curl zip unzip
elif grep -Eq "FreeBSD" /etc/*-release; then
	OSNAME='freebsd'
elif grep -Eqi "CentOS" /etc/issue || grep -Eq "CentOS" /etc/*-release; then
	OSNAME='rhel'
	yum install -y wget curl zip unzip tar crontabs
elif grep -Eqi "Fedora" /etc/issue || grep -Eq "Fedora" /etc/*-release; then
	OSNAME='fedora'
	yum install -y wget curl zip unzip tar crontabs
elif grep -Eqi "Rocky" /etc/issue || grep -Eq "Rocky" /etc/*-release; then
	OSNAME='rhel'
	yum install -y wget curl zip unzip tar crontabs
elif grep -Eqi "AlmaLinux" /etc/issue || grep -Eq "AlmaLinux" /etc/*-release; then
	OSNAME='rhel'
	yum install -y wget curl zip unzip tar crontabs
elif grep -Eqi "Amazon Linux" /etc/issue || grep -Eq "Amazon Linux" /etc/*-release; then
	OSNAME='amazon'
	yum install -y wget curl zip unzip tar crontabs
elif grep -Eqi "Debian" /etc/issue || grep -Eq "Debian" /etc/os-release; then
	OSNAME='debian'
	apt update -y
	apt install -y wget curl zip unzip tar cron
elif grep -Eqi "Ubuntu" /etc/issue || grep -Eq "Ubuntu" /etc/os-release; then
	OSNAME='ubuntu'
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

	mkdir -p /home/slemp/server
	mkdir -p /home/slemp/wwwroot
	mkdir -p /home/slemp/wwwlogs
	mkdir -p /home/slemp/backup/database
	mkdir -p /home/slemp/backup/site

	if [ ! -d /home/slemp/server/panel ];then
		curl --insecure -sSLo /tmp/master.zip https://codeload.github.com/basoro/slemp/zip/master

		cd /tmp && unzip /tmp/master.zip
		mv -f /tmp/slemp-master /home/slemp/server/panel
		rm -rf /tmp/master.zip
		rm -rf /tmp/slemp-master
	fi

	# install acme.sh
	if [ ! -d /root/.acme.sh ];then
	    if [ ! -z "$cn" ];then
	        curl --insecure -sSL -o /tmp/acme.tar.gz https://ghproxy.com/github.com/acmesh-official/acme.sh/archive/master.tar.gz
	        tar xvzf /tmp/acme.tar.gz -C /tmp
	        cd /tmp/acme.sh-master
	        bash acme.sh install
	        cd -
	    fi

	    if [ ! -d /root/.acme.sh ];then
	        curl  https://get.acme.sh | sh
	    fi
	fi
fi



echo "use system version: ${OSNAME}"

if [ "${OSNAME}" == "macos" ];then
	HTTP_PREFIX="https://"
	curl -fsSL ${HTTP_PREFIX}https://raw.githubusercontent.com/basoro/slemp/master/scripts/install/macos.sh | bash
else
	cd /home/slemp/server/panel && bash scripts/install/${OSNAME}.sh
fi

if [ "${OSNAME}" == "macos" ];then
	echo "macos end"
	exit 0
fi

cd /home/slemp/server/panel && bash cli.sh start
isStart=`ps -ef|grep 'gunicorn -c setting.py app:app' |grep -v grep|awk '{print $2}'`
n=0
while [ ! -f /etc/rc.d/init.d/slemp ];
do
    echo -e ".\c"
    sleep 1
    let n+=1
    if [ $n -gt 20 ];then
    	echo -e "start slemp fail"
    	exit 1
    fi
done

cd /home/slemp/server/panel && bash /etc/rc.d/init.d/slemp stop
cd /home/slemp/server/panel && bash /etc/rc.d/init.d/slemp start
cd /home/slemp/server/panel && bash /etc/rc.d/init.d/slemp default

sleep 2
if [ ! -e /usr/bin/slemp ]; then
	if [ -f /etc/rc.d/init.d/slemp ];then
		ln -s /etc/rc.d/init.d/slemp /usr/bin/slemp
	fi
fi

endTime=`date +%s`
((outTime=(${endTime}-${startTime})/60))
echo -e "Time consumed:\033[32m $outTime \033[0mMinute!"

} 1> >(tee slemp-install.log) 2>&1

echo -e "\nInstall completed. If error occurs, please contact us with the log file slemp-install.log ."
