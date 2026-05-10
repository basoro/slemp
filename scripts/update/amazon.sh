#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin:/opt/homebrew/bin
export PATH
LANG=en_US.UTF-8


if [ -f /etc/motd ];then
    echo "welcome to panel panel" > /etc/motd
fi

sed -i 's#SELINUX=enforcing#SELINUX=disabled#g' /etc/selinux/config

yum install -y curl-devel libmcrypt libmcrypt-devel python3-devel


cd ${rootPath}/scripts && bash lib.sh
chmod 755 ${rootPath}/data

if [ -f /etc/rc.d/init.d/slemp ];then
    bash /etc/rc.d/init.d/slemp stop && rm -rf ${rootPath}/scripts/init.d/slemp && rm -rf /etc/rc.d/init.d/slemp
fi

echo -e "stop mw"
isStart=`ps -ef|grep 'gunicorn -c setting.py app:app' |grep -v grep|awk '{print $2}'`

port=7200
if [ -f ${rootPath}/data/port.pl ]; then
    port=$(cat ${rootPath}/data/port.pl)
fi

n=0
while [[ "$isStart" != "" ]];
do
    echo -e ".\c"
    sleep 0.5
    isStart=$(lsof -n -P -i:$port|grep LISTEN|grep -v grep|awk '{print $2}'|xargs)
    let n+=1
    if [ $n -gt 15 ];then
        break;
    fi
done


echo -e "start mw"
cd ${rootPath} && bash cli.sh start
isStart=`ps -ef|grep 'gunicorn -c setting.py app:app' |grep -v grep|awk '{print $2}'`
n=0
while [[ ! -f /etc/rc.d/init.d/slemp ]];
do
    echo -e ".\c"
    sleep 1
    let n+=1
    if [ $n -gt 20 ];then
        echo -e "start mw fail"
        exit 1
    fi
done
echo -e "start mw success"