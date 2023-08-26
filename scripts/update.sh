#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
# LANG=en_US.UTF-8
is64bit=`getconf LONG_BIT`

startTime=`date +%s`

_os=`uname`
echo "use system: ${_os}"

if [ "$EUID" -ne 0 ]
  then echo "Please run as root!"
  exit
fi

if [ ${_os} != "Darwin" ] && [ ! -d /home/slemp/server/panel/logs ]; then
	mkdir -p /home/slemp/server/panel/logs
fi

{

if [ ${_os} == "Darwin" ]; then
	OSNAME='macos'
elif grep -Eqi "openSUSE" /etc/*-release; then
	OSNAME='opensuse'
	zypper refresh
elif grep -Eqi "FreeBSD" /etc/*-release; then
	OSNAME='freebsd'
elif grep -Eqi "CentOS" /etc/issue || grep -Eqi "CentOS" /etc/*-release; then
	OSNAME='rhel'
	yum install -y wget zip unzip
elif grep -Eqi "Fedora" /etc/issue || grep -Eqi "Fedora" /etc/*-release; then
	OSNAME='rhel'
	yum install -y wget zip unzip
elif grep -Eqi "Rocky" /etc/issue || grep -Eqi "Rocky" /etc/*-release; then
	OSNAME='rhel'
	yum install -y wget zip unzip
elif grep -Eqi "AlmaLinux" /etc/issue || grep -Eqi "AlmaLinux" /etc/*-release; then
	OSNAME='rhel'
	yum install -y wget zip unzip
elif grep -Eqi "Amazon Linux" /etc/issue || grep -Eqi "Amazon Linux" /etc/*-release; then
	OSNAME='amazon'
	yum install -y wget zip unzip
elif grep -Eqi "Debian" /etc/issue || grep -Eqi "Debian" /etc/*-release; then
	OSNAME='debian'
	apt install -y wget zip unzip
elif grep -Eqi "Ubuntu" /etc/issue || grep -Eqi "Ubuntu" /etc/*-release; then
	OSNAME='ubuntu'
	apt install -y wget zip unzip
else
	OSNAME='unknow'
fi

curl -sSLo /tmp/master.zip https://codeload.github.com/basoro/slemp/zip/master

cd /tmp && unzip /tmp/master.zip

CP_CMD=/usr/bin/cp
if [ -f /bin/cp ];then
		CP_CMD=/bin/cp
fi
$CP_CMD -rf /tmp/slemp-master/* /home/slemp/server/panel

rm -rf /tmp/master.zip
rm -rf /tmp/slemp-master

#pip uninstall public
echo "use system version: ${OSNAME}"
cd /home/slemp/server/panel && bash scripts/update/${OSNAME}.sh

bash /etc/rc.d/init.d/slemp restart
bash /etc/rc.d/init.d/slemp default

if [ -f /usr/bin/slemp ];then
	rm -rf /usr/bin/slemp
fi

if [ ! -e /usr/bin/slemp ]; then
	if [ ! -f /usr/bin/slemp ];then
		ln -s /etc/rc.d/init.d/slemp /usr/bin/slemp
	fi
fi

endTime=`date +%s`
((outTime=($endTime-$startTime)/60))
echo -e "Time consumed:\033[32m $outTime \033[0mMinute!"

} 1> >(tee /home/slemp/server/panel/logs/slemp-update.log) 2>&1
