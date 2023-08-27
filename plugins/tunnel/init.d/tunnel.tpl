#!/bin/bash
# chkconfig: 2345 55 25
# description: SLEMP Cloud Service

### BEGIN INIT INFO
# Provides:          bt
# Required-Start:    $all
# Required-Stop:     $all
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: starts slemp
# Description:       starts the slemp
### END INIT INFO


PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin

app_start(){
	isStart=`ps -ef | grep metro.basoro.id | grep -v grep | awk '{print $2}'`
	if [ "$isStart" == '' ];then
      echo -e "Starting tunnel... \c"
			key=`cat /home/slemp/server/tunnel/key.pl`
			/home/slemp/server/tunnel/client -s metro.basoro.id -p 4900 -k "$key" &
      echo -e "\033[32mdone\033[0m"
  else
      echo "Starting tunnel already running"
  fi
}

app_stop()
{
    echo -e "Stopping tunnel... \c";
		isStart = `ps -ef | grep metro.basoro.id | grep -v grep | awk '{print $2}'`
		if [ "$isStart" != '' ];then
			kill -9 "$isStart"
		fi
    echo -e "\033[32mdone\033[0m"
}

app_status()
{
    isStart=`ps -ef | grep metro.basoro.id | grep -v grep | awk '{print $2}'`
    if [ "$isStart" != '' ];then
        echo -e "\033[32mtunnel already running\033[0m"
    else
        echo -e "\033[31mtunnel not running\033[0m"
    fi
}

case "$1" in
    'start') app_start;;
    'stop') app_stop;;
    'restart'|'reload')
        app_stop
        app_start;;
    'status') app_status;;
esac
