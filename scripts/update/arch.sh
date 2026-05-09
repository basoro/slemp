#!/bin/bash
PANEL_DIR=$(cd "$(dirname "$0")/../.."; pwd)

PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:/opt/homebrew/bin:~/bin
export PATH
LANG=en_US.UTF-8



# echo y | pacman -Sy yaourt
# echo y | pacman -Sy python3

cd $PANEL_DIR/scripts && bash lib.sh
chmod 755 $PANEL_DIR/data

if [ -f /etc/rc.d/init.d/slemp ];then
    bash /etc/rc.d/init.d/slemp stop && rm -rf $PANEL_DIR/scripts/init.d/slemp && rm -rf /etc/rc.d/init.d/slemp
fi

echo -e "start slemp"
cd $PANEL_DIR && bash cli.sh start
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

cd $PANEL_DIR && bash /etc/rc.d/init.d/slemp stop
cd $PANEL_DIR && bash /etc/rc.d/init.d/slemp start