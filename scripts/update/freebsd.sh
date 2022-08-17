#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
LANG=en_US.UTF-8


cd /home/slemp/server/panel/scripts && bash lib.sh
chmod 755 /home/slemp/server/panel/data

if [ -f /etc/init.d/slemp ];then
    sh /etc/init.d/slemp stop && rm -rf  /home/slemp/server/panel/scripts/init.d/slemp && rm -rf  /etc/init.d/slemp
fi


cd /home/slemp/server/panel && bash cli.sh start
isStart=`ps -ef|grep 'gunicorn -c setting.py app:app' |grep -v grep|awk '{print $2}'`
n=0
while [[ ! -f /etc/init.d/slemp ]];
do
    echo -e ".\c"
    sleep 1
    let n+=1
    if [ $n -gt 20 ];then
    	echo -e "start slemp fail"
        exit 1
    fi
done

cd /home/slemp/server/panel && bash /etc/init.d/slemp stop
cd /home/slemp/server/panel && bash /etc/init.d/slemp start
cd /home/slemp/server/panel && bash /etc/init.d/slemp default

