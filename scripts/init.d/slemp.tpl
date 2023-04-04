#!/bin/bash
# chkconfig: 2345 55 25
# description: SLEMP Cloud Service

### BEGIN INIT INFO
# Provides:          Basoro
# Required-Start:    $all
# Required-Stop:     $all
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: starts slemp
# Description:       starts the slemp
### END INIT INFO


PATH=/usr/local/bin:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export LANG=en_US.UTF-8

slemp_path={$SERVER_PATH}
PATH=$PATH:$slemp_path/bin


if [ -f $slemp_path/bin/activate ];then
    source $slemp_path/bin/activate
fi

slemp_start_panel()
{
    isStart=`ps -ef|grep 'gunicorn -c setting.py app:app' |grep -v grep|awk '{print $2}'`
    if [ "$isStart" == '' ];then
        echo -e "starting slemp-panel... \c"
        cd $slemp_path &&  gunicorn -c setting.py app:app
        port=$(cat ${slemp_path}/data/port.pl)
        isStart=""
        while [[ "$isStart" == "" ]];
        do
            echo -e ".\c"
            sleep 0.5
            isStart=$(lsof -n -P -i:$port|grep LISTEN|grep -v grep|awk '{print $2}'|xargs)
            let n+=1
            if [ $n -gt 20 ];then
                break;
            fi
        done
        if [ "$isStart" == '' ];then
            echo -e "\033[31mfailed\033[0m"
            echo '------------------------------------------------------'
            tail -n 20 ${slemp_path}/logs/error.log
            echo '------------------------------------------------------'
            echo -e "\033[31mError: slemp-panel service startup failed.\033[0m"
            return;
        fi
        echo -e "\033[32mdone\033[0m"
    else
        echo "starting slemp-panel... slemp(pid $(echo $isStart)) already running"
    fi
}


slemp_start_task()
{
    isStart=$(ps aux |grep 'task.py'|grep -v grep|awk '{print $2}')
    if [ "$isStart" == '' ];then
        echo -e "starting slemp-tasks... \c"
        cd $slemp_path && python3 task.py >> ${slemp_path}/logs/task.log 2>&1 &
        sleep 0.3
        isStart=$(ps aux |grep 'task.py'|grep -v grep|awk '{print $2}')
        if [ "$isStart" == '' ];then
            echo -e "\033[31mfailed\033[0m"
            echo '------------------------------------------------------'
            tail -n 20 $slemp_path/logs/task.log
            echo '------------------------------------------------------'
            echo -e "\033[31mError: slemp-tasks service startup failed.\033[0m"
            return;
        fi
        echo -e "\033[32mdone\033[0m"
    else
        echo "starting slemp-tasks... slemp-tasks (pid $(echo $isStart)) already running"
    fi
}

slemp_start()
{
    slemp_start_task
	slemp_start_panel
}

# /home/slemp/server/panel/tmp/panelTask.pl && service slemp restart_task
slemp_stop_task()
{
    if [ -f $slemp_path/tmp/panelTask.pl ];then
        echo -e "\033[32mthe task is running and cannot be stopped\033[0m"
        exit 0
    fi

    echo -e "stopping slemp-tasks... \c";
    pids=$(ps aux | grep 'task.py'|grep -v grep|awk '{print $2}')
    arr=($pids)
    for p in ${arr[@]}
    do
        kill -9 $p  > /dev/null 2>&1
    done
    echo -e "\033[32mdone\033[0m"
}

slemp_stop_panel()
{
    echo -e "stopping slemp-panel... \c";
    arr=`ps aux|grep 'gunicorn -c setting.py app:app'|grep -v grep|awk '{print $2}'`
    for p in ${arr[@]}
    do
        kill -9 $p > /dev/null 2>&1
    done

    pidfile=${slemp_path}/logs/slemp.pid
    if [ -f $pidfile ];then
        rm -f $pidfile
    fi
    echo -e "\033[32mdone\033[0m"
}

slemp_stop()
{
    slemp_stop_task
    slemp_stop_panel
}

slemp_status()
{
    isStart=$(ps aux|grep 'gunicorn -c setting.py app:app'|grep -v grep|awk '{print $2}')
    if [ "$isStart" != '' ];then
        echo -e "\033[32mslemp (pid $(echo $isStart)) already running\033[0m"
    else
        echo -e "\033[31mslemp not running\033[0m"
    fi

    isStart=$(ps aux |grep 'task.py'|grep -v grep|awk '{print $2}')
    if [ "$isStart" != '' ];then
        echo -e "\033[32mslemp-task (pid $isStart) already running\033[0m"
    else
        echo -e "\033[31mslemp-task not running\033[0m"
    fi
}


slemp_reload()
{
	isStart=$(ps aux|grep 'gunicorn -c setting.py app:app'|grep -v grep|awk '{print $2}')

    if [ "$isStart" != '' ];then
    	echo -e "reload slemp... \c";
	    arr=`ps aux|grep 'gunicorn -c setting.py app:app'|grep -v grep|awk '{print $2}'`
		for p in ${arr[@]}
        do
                kill -9 $p
        done
        cd $slemp_path && gunicorn -c setting.py app:app
        isStart=`ps aux|grep 'gunicorn -c setting.py app:app'|grep -v grep|awk '{print $2}'`
        if [ "$isStart" == '' ];then
            echo -e "\033[31mfailed\033[0m"
            echo '------------------------------------------------------'
            tail -n 20 $slemp_path/logs/error.log
            echo '------------------------------------------------------'
            echo -e "\033[31mError: slemp service startup failed.\033[0m"
            return;
        fi
        echo -e "\033[32mdone\033[0m"
    else
        echo -e "\033[31mslemp not running\033[0m"
        slemp_start
    fi
}

slemp_close(){
    echo 'True' > $slemp_path/data/close.pl
}

slemp_open()
{
    if [ -f $slemp_path/data/close.pl ];then
        rm -rf $slemp_path/data/close.pl
    fi
}

slemp_unbind_domain()
{
    if [ -f $slemp_path/data/bind_domain.pl ];then
        rm -rf $slemp_path/data/bind_domain.pl
    fi
}

error_logs()
{
	tail -n 100 $slemp_path/logs/error.log
}

slemp_update()
{
    curl --insecure -fsSL https://raw.githubusercontent.com/basoro/slemp/master/scripts/update.sh | bash
}

slemp_install_app()
{
    bash $slemp_path/scripts/quick/app.sh
}

slemp_close_admin_path(){
    if [ -f $slemp_path/data/admin_path.pl ]; then
        rm -rf $slemp_path/data/admin_path.pl
    fi
}

slemp_force_kill()
{
    PLIST=`ps -ef|grep app:app |grep -v grep|awk '{print $2}'`
    for i in $PLIST
    do
        kill -9 $i
    done

    pids=`ps -ef|grep task.py | grep -v grep |awk '{print $2}'`
    arr=($pids)
    for p in ${arr[@]}
    do
        kill -9 $p
    done
}

slemp_debug(){
    slemp_stop
    slemp_force_kill

    port=7200
    if [ -f $slemp_path/data/port.pl ];then
        port=$(cat $slemp_path/data/port.pl)
    fi

    if [ -d /home/slemp/server/panel ];then
        cd /home/slemp/server/panel
    fi
    gunicorn -b :$port -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1  app:app
}

case "$1" in
    'start') slemp_start;;
    'stop') slemp_stop;;
    'reload') slemp_reload;;
    'restart')
        slemp_stop
        slemp_start;;
    'restart_panel')
        slemp_stop_panel
        slemp_start_panel;;
    'restart_task')
        slemp_stop_task
        slemp_start_task;;
    'status') slemp_status;;
    'logs') error_logs;;
    'close') slemp_close;;
    'open') slemp_open;;
    'update') slemp_update;;
    'install_app') slemp_install_app;;
    'close_admin_path') slemp_close_admin_path;;
    'unbind_domain') slemp_unbind_domain;;
    'debug') slemp_debug;;
    'default')
        cd $slemp_path
        port=7200

        if [ -f $slemp_path/data/port.pl ];then
            port=$(cat $slemp_path/data/port.pl)
        fi

        if [ ! -f $slemp_path/data/default.pl ];then
            echo -e "\033[33mInstall Failed\033[0m"
            exit 1
        fi

        password=$(cat $slemp_path/data/default.pl)
        if [ -f $slemp_path/data/domain.conf ];then
            address=$(cat $slemp_path/data/domain.conf)
        fi
        if [ -f $slemp_path/data/admin_path.pl ];then
            auth_path=$(cat $slemp_path/data/admin_path.pl)
        fi

        if [ "$address" == "" ];then
            v4=$(python3 $slemp_path/tools.py getServerIp 4)
            v6=$(python3 $slemp_path/tools.py getServerIp 6)

            if [ "$v4" != "" ] && [ "$v6" != "" ]; then

                if [ ! -f $slemp_path/data/ipv6.pl ];then
                    echo 'True' > $slemp_path/data/ipv6.pl
                    slemp_stop
                    slemp_start
                fi

                address="SLEMP-Panel-Url-Ipv4: http://$v4:$port$auth_path \nSLEMP-Panel-Url-Ipv6: http://[$v6]:$port$auth_path"
            elif [ "$v4" != "" ]; then
                address="SLEMP-Panel-Url: http://$v4:$port$auth_path"
            elif [ "$v6" != "" ]; then

                if [ ! -f $slemp_path/data/ipv6.pl ];then
                    #  Need to restart ipv6 to take effect
                    echo 'True' > $slemp_path/data/ipv6.pl
                    slemp_stop
                    slemp_start
                fi
                address="SLEMP-Panel-Url: http://[$v6]:$port$auth_path"
            else
                address="SLEMP-Panel-Url: http://you-server-ip:$port$auth_path"
            fi
        else
            address="SLEMP-Panel-Url: http://$address:$port$auth_path"
        fi

        show_panel_ip="$port|"
        echo -e "=================================================================="
        echo -e "\033[32mSLEMP-Panel default info!\033[0m"
        echo -e "=================================================================="
        echo -e "$address"
        echo -e `python3 $slemp_path/tools.py username`
        echo -e `python3 $slemp_path/tools.py password`
        # echo -e "password: $password"
        echo -e "\033[33mWarning:\033[0m"
        echo -e "\033[33mIf you cannot access the panel. \033[0m"
        echo -e "\033[33mrelease the following port (${show_panel_ip}888|80|443|22) in the security group.\033[0m"
        echo -e "=================================================================="
        ;;
    *)
        cd $slemp_path && python3 $slemp_path/tools.py cli $1
        ;;
esac
