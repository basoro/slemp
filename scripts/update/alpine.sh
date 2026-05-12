#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin:/opt/homebrew/bin
export PATH
LANG=en_US.UTF-8


# systemctl stop SuSEfirewall2

cd ${rootPath}/scripts && bash lib.sh
chmod 755 ${rootPath}/data

if [ -f /etc/rc.d/init.d/slemp ];then
    bash /etc/rc.d/init.d/slemp stop && rm -rf ${rootPath}/scripts/init.d/slemp && rm -rf /etc/rc.d/init.d/slemp
fi

echo -e "start slemp"
cd ${rootPath} && bash cli.sh start
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

cd ${rootPath} && bash /etc/rc.d/init.d/slemp stop
cd ${rootPath} && bash /etc/rc.d/init.d/slemp start
