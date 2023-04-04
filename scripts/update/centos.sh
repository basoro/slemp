#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
export LANG=en_US.UTF-8


if [ -f /etc/motd ];then
    echo "Welcome to SLEMP Panel" > /etc/motd
fi

sed -i 's#SELINUX=enforcing#SELINUX=disabled#g' /etc/selinux/config

yum install -y curl-devel libmcrypt libmcrypt-devel python3-devel


cd /home/slemp/server/panel/scripts && bash lib.sh
chmod 755 /home/slemp/server/panel/data

if [ -f /etc/rc.d/init.d/slemp ];then
    bash /etc/rc.d/init.d/slemp stop && rm -rf /home/slemp/server/panel/scripts/init.d/slemp && rm -rf /etc/rc.d/init.d/slemp
fi

echo -e "stop slemp"
isStart=`ps -ef|grep 'gunicorn -c setting.py app:app' |grep -v grep|awk '{print $2}'`

port=7200
if [ -f /home/slemp/server/panel/data/port.pl ]; then
    port=$(cat /home/slemp/server/panel/data/port.pl)
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


echo -e "start slemp"
cd /home/slemp/server/panel && bash cli.sh start
isStart=`ps -ef|grep 'gunicorn -c setting.py app:app' |grep -v grep|awk '{print $2}'`
n=0
while [[ ! -f /etc/rc.d/init.d/slemp ]];
do
    echo -e ".\c"
    sleep 1
    let n+=1
    if [ $n -gt 20 ];then
        echo -e "start slemp fail"
        exit 1
    fi
done
echo -e "start slemp success"