#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
export DEBIAN_FRONTEND=noninteractive

apt install -y locate
locale-gen en_US.UTF-8
localedef -v -c -i en_US -f UTF-8 en_US.UTF-8 > /dev/null 2>&1
export LC_CTYPE=en_US.UTF-8
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8

# echo "LC_ALL=en_US.UTF-8" > /etc/default/locale
# echo "LANG=en_US.UTF-8" > /etc/default/locale


if grep -Eq "Ubuntu" /etc/*-release; then
    sudo ln -sf /bin/bash /bin/sh
    #sudo dpkg-reconfigure dash
fi

VERSION_ID=`cat /etc/*-release | grep VERSION_ID | awk -F = '{print $2}' | awk -F "\"" '{print $2}'`
if [ "$VERSION_ID" == "9" ];then
    sed "s/flask==2.0.3/flask==1.1.1/g" -i /home/slemp/server/panel/requirements.txt
    sed "s/cryptography==3.3.2/cryptography==2.5/g" -i /home/slemp/server/panel/requirements.txt
    sed "s/configparser==5.2.0/configparser==4.0.2/g" -i /home/slemp/server/panel/requirements.txt
    sed "s/flask-socketio==5.2.0/flask-socketio==4.2.0/g" -i /home/slemp/server/panel/requirements.txt
    sed "s/python-engineio==4.3.2/python-engineio==3.9.0/g" -i /home/slemp/server/panel/requirements.txt
    # pip3 install -r /home/slemp/server/panel/requirements.txt
fi

cd /home/slemp/server/panel/scripts && bash lib.sh
chmod 755 /home/slemp/server/panel/data

if [ -f /etc/rc.d/init.d/slemp ];then
    bash /etc/rc.d/init.d/slemp stop && rm -rf /home/slemp/server/panel/scripts/init.d/slemp && rm -rf /etc/rc.d/init.d/slemp
fi

echo -e "stop slemp"
isStart=`ps -ef|grep 'gunicorn -c setting.py app:app' |grep -v grep|awk '{print $2}'`

port=7200
if [ -f /home/slemp/server/panel/data/port.pl ];then
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

systemctl daemon-reload
