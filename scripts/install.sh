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
    rootPath=$(dirname "$DIR")
    serverPath=$(dirname "$rootPath")
else
    rootPath="/opt/slemp/server/panel"
    serverPath="/opt/slemp/server"
fi

LOG_FILE=slemp-install.log
{

HTTP_PREFIX="https://"
LOCAL_ADDR=common
cn=$(curl -fsSL -m 10 -s http://ipinfo.io/json | grep "\"country\": \"CN\"")
if [ ! -z "$cn" ] || [ "$?" == "0" ] ;then
	LOCAL_ADDR=cn
fi

if [ "$LOCAL_ADDR" != "common" ];then
	declare -A PROXY_URL
	PROXY_URL["gh_proxy_com"]="https://gh-proxy.com/"
    PROXY_URL["github_do"]="https://github.do/"
    PROXY_URL["gh_llkk_cc"]="https://gh.llkk.cc/https://"
    PROXY_URL["gh_felicity_ac_cn"]="https://gh.felicity.ac.cn/https://"
    PROXY_URL["ghfast_top"]="https://ghfast.top/"
    PROXY_URL["ghproxy_net"]="https://ghproxy.net/"
    PROXY_URL["gh_927223_xyz"]="https://gh.927223.xyz/https://"
    PROXY_URL["gh_proxy_net"]="https://gh-proxy.net/"
    
    PROXY_URL["source"]="https://"


	SOURCE_LIST_KEY_SORT_TMP=$(echo ${!PROXY_URL[@]} | tr ' ' '\n' | sort -n)
	SOURCE_LIST_KEY=(${SOURCE_LIST_KEY_SORT_TMP//'\n'/})
	SOURCE_LIST_LEN=${#PROXY_URL[*]}
fi


function AutoSizeStr(){
	NAME_STR=$1
	NAME_NUM=$2

	NAME_STR_LEN=`echo "$NAME_STR" | wc -L`
	NAME_NUM_LEN=`echo "$NAME_NUM" | wc -L`

	fix_len=35
	remaining_len=`expr $fix_len - $NAME_STR_LEN - $NAME_NUM_LEN`
	FIX_SPACE=' '
	for ((ass_i=1;ass_i<=$remaining_len;ass_i++))
	do 
		FIX_SPACE="$FIX_SPACE "
	done
	echo -e " ❖   ${1}${FIX_SPACE}${2})"
}

function ChooseProxyURL(){
	clear
    echo -e '+---------------------------------------------------+'
    echo -e '|                                                   |'
    echo -e '|   =============================================   |'
    echo -e '|                                                   |'
    echo -e '|  Selamat datang di Skrip Instalasi Sekali Klik Panel Linux  |'
    echo -e '|                                                   |'
    echo -e '|   =============================================   |'
    echo -e '|                                                   |'
    echo -e '+---------------------------------------------------+'
    echo -e ''
    echo -e '#####################################################'
    echo -e ''
    echo -e '            Alamat proxy domestik berikut tersedia untuk dipilih:                 '
    echo -e ''
    echo -e '#####################################################'
    echo -e ''
    cm_i=0
    for V in ${SOURCE_LIST_KEY[@]}; do
    num=`expr $cm_i + 1`
	AutoSizeStr "${V}" "$num"
	cm_i=`expr $cm_i + 1`
	done
    echo -e ''
    echo -e '#####################################################'
    echo -e ''
    echo -e "        Waktu Sistem  ${BLUE}$(date "+%Y-%m-%d %H:%M:%S")${PLAIN}"
    echo -e ''
    echo -e '#####################################################'
    CHOICE_A=$(echo -e "\n${BOLD}└─ Silakan pilih dan masukkan alamat proxy yang ingin Anda gunakan [ 1-${SOURCE_LIST_LEN} ]：${PLAIN}")

    read -p "${CHOICE_A}" INPUT
    # echo $INPUT
    if [ "$INPUT" == "" ];then
        INPUT=1
        TMP_INPUT=`expr $INPUT - 1`
        INPUT_KEY=${SOURCE_LIST_KEY[$TMP_INPUT]}
        echo -e "\nMemilih [${BLUE}${INPUT_KEY}${PLAIN}] secara default untuk instalasi!"
    fi

    if [ "$INPUT" -lt "0" ];then
		INPUT=1
		TMP_INPUT=`expr $INPUT - 1`
		INPUT_KEY=${SOURCE_LIST_KEY[$TMP_INPUT]}
		echo -e "\nError di bawah batas! Memilih [${BLUE}${INPUT_KEY}${PLAIN}] untuk instalasi!"
		sleep 2s
	fi

	if [ "$INPUT" -gt "${SOURCE_LIST_LEN}" ];then
		INPUT=${SOURCE_LIST_LEN}
		TMP_INPUT=`expr $INPUT - 1`
		INPUT_KEY=${SOURCE_LIST_KEY[$TMP_INPUT]}
		echo -e "\nError di atas batas! Memilih [${BLUE}${INPUT_KEY}${PLAIN}] untuk instalasi!"
		sleep 2s
	fi

    INPUT=`expr $INPUT - 1`
    INPUT_KEY=${SOURCE_LIST_KEY[$INPUT]}
    HTTP_PREFIX=${PROXY_URL[$INPUT_KEY]}
}

if [ "$LOCAL_ADDR" != "common" ];then
	ChooseProxyURL

	if [ "$HTTP_PREFIX" != "https://" ];then
		DOMAIN=`echo $HTTP_PREFIX | sed 's|https://||g'`
		DOMAIN=`echo $DOMAIN | sed 's|/||g'`
		ping -c 3 $DOMAIN > /dev/null 2>&1
		if [ "$?" != "0" ];then
			echo "Alamat proxy tidak valid:${DOMAIN}"
			exit
		fi
	fi
fi

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
elif grep -Eqi "Debian" /etc/issue || grep -Eqi "Debian" /etc/os-release; then
	OSNAME='debian'
	# apt update -y
	apt install -y wget curl zip unzip tar cron
elif grep -Eqi "Ubuntu" /etc/issue || grep -Eqi "Ubuntu" /etc/os-release; then
	OSNAME='ubuntu'
	# apt update -y
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

echo "LOCAL:${LOCAL_ADDR}"
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
		curl --insecure -sSLo /tmp/master.tar.gz ${HTTP_PREFIX}github.com/midoks/panel/archive/refs/heads/master.tar.gz
		cd /tmp && tar -zxvf /tmp/master.tar.gz
		mv -f /tmp/panel-master ${rootPath}
		rm -rf /tmp/master.tar.gz
		rm -rf /tmp/panel-master
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