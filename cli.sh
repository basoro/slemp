#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin

curPath=`pwd`
rootPath=$(dirname "$curPath")
DIR=$(cd "$(dirname "$0")"; pwd)

PATH=$PATH:$DIR/bin
if [ -f bin/activate ];then
	source bin/activate
fi

export LC_ALL="en_US.UTF-8"


slemp_start_task()
{
    isStart=$(ps aux |grep 'task.py'|grep -v grep|awk '{print $2}')
    if [ "$isStart" == '' ];then
        echo -e "Starting slemp-tasks... \c"
        cd $DIR && python3 task.py >> ${DIR}/logs/task.log 2>&1 &
        sleep 0.3
        isStart=$(ps aux |grep 'task.py'|grep -v grep|awk '{print $2}')
        if [ "$isStart" == '' ];then
            echo -e "\033[31mfailed\033[0m"
            echo '------------------------------------------------------'
            tail -n 20 $DIR/logs/task.log
            echo '------------------------------------------------------'
            echo -e "\033[31mError: slemp-tasks service startup failed.\033[0m"
            return;
        fi
        echo -e "\033[32mdone\033[0m"
    else
        echo "Starting slemp-tasks... slemp-tasks (pid $(echo $isStart)) already running"
    fi
}

slemp_start(){
	gunicorn -c setting.py app:app
	slemp_start_task
}


slemp_start_debug(){
	python3 task.py >> $DIR/logs/task.log 2>&1 &
	port=7200
    if [ -f ${rootPath}/data/port.pl ];then
        port=$(cat ${rootPath}/data/port.pl)
    fi
    # gunicorn -b :${port} -k gevent -w 1 app:app
	gunicorn -b :${port} -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 app:app
}

slemp_start_debug2(){
	python3 task.py >> $DIR/logs/task.log 2>&1 &
	gunicorn -b :7200 -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1  app:app
}


slemp_stop()
{
	PLIST=`ps -ef|grep app:app |grep -v grep|awk '{print $2}'`
	for i in $PLIST
	do
	    kill -9 $i > /dev/null 2>&1
	done

	pids=`ps -ef|grep task.py | grep -v grep |awk '{print $2}'`
	arr=($pids)
    for p in ${arr[@]}
    do
    	kill -9 $p > /dev/null 2>&1
    done
}

case "$1" in
    'start') slemp_start;;
    'stop') slemp_stop;;
    'restart')
		slemp_stop
		slemp_start
		;;
	'debug')
		slemp_stop
		slemp_start_debug
		;;
	'debug2')
		slemp_stop
		slemp_start_debug2
		;;
esac
