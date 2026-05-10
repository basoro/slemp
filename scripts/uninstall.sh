#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
export LANG=en_US.UTF-8
is64bit=`getconf LONG_BIT`

if [ -f /etc/motd ];then
    echo "" > /etc/motd
fi

startTime=`date +%s`

_os=`uname`
echo "use system: ${_os}"

if [ "$EUID" -ne 0 ]
  then echo "Please run as root!"
  exit
fi

UNINSTALL_CHECK()
{
    echo -e "----------------------------------------------------"
    echo -e "Saat ini hanya dapat menghapus OpenResty/PHP/MySQL/Redis/Memcached"
    echo -e "Harap hapus instalasi plugin lain secara manual terlebih dahulu!"
    echo -e "----------------------------------------------------"
    echo -e "Risiko diketahui/ketik yes untuk hapus instalasi secara paksa! [yes/no]"
    read -p "Ketik yes untuk hapus instalasi secara paksa: " yes;
    if [ "$yes" != "yes" ];then
        echo -e "------------"
        echo "Membatalkan penghapusan instalasi"
        exit 1
    else
        echo "Memulai penghapusan instalasi!"
    fi
}


UNINSTALL_MySQL()
{
    MYSQLD_CHECK=$(ps -ef |grep mysqld | grep -v grep | grep ${serverPath}/mysql)
    if [ "$MYSQLD_CHECK" != "" ];then
        echo -e "----------------------------------------------------"
        echo -e "Memeriksa lingkungan MySQL yang ada, penghapusan instalasi dapat memengaruhi situs dan data yang ada"
        echo -e "----------------------------------------------------"
        echo -e "Risiko diketahui/ketik yes untuk hapus instalasi secara paksa! [yes/no]"
        read -p "Ketik yes untuk hapus instalasi secara paksa: " yes;
        if [ "$yes" != "yes" ];then
            echo -e "------------"
            echo "Membatalkan penghapusan instalasi MySQL"
        else
            cd ${rootPath}/plugins/mysql && sh install.sh uninstall 8.0
            echo "Penghapusan instalasi MySQL berhasil!"
        fi
    fi
}

UNINSTALL_OP()
{
    if [ -f ${serverPath}/openresty ];then
        echo -e "----------------------------------------------------"
        echo -e "Memeriksa lingkungan OpenResty yang ada, penghapusan instalasi dapat memengaruhi situs dan data yang ada"
        echo -e "----------------------------------------------------"
        echo -e "Risiko diketahui/ketik yes untuk hapus instalasi secara paksa! [yes/no]"
        read -p "Ketik yes untuk hapus instalasi secara paksa: " yes;
        if [ "$yes" != "yes" ];then
            echo -e "------------"
            echo "Membatalkan penghapusan instalasi OpenResty"
        else
            cd ${rootPath}/plugins/openresty && sh install.sh uninstall
            echo "Penghapusan instalasi OpenResty berhasil!"
        fi
    fi
}

UNINSTALL_PHP()
{
    if [ -d ${serverPath}/php ];then
        echo -e "----------------------------------------------------"
        echo -e "Memeriksa lingkungan PHP yang ada, penghapusan instalasi dapat memengaruhi situs dan data yang ada"
        echo -e "----------------------------------------------------"
        read -p "Ketik yes untuk menghapus semua PHP secara paksa [yes/no]: " yes;
        if [ "$yes" != "yes" ];then
            echo -e "------------"
            echo "Membatalkan penghapusan instalasi PHP"
        else
            PHP_VER_LIST=(53 54 55 56 70 71 72 73 74 80 81 82)
            for PHP_VER in ${PHP_VER_LIST[@]}; do
                if [ -d ${serverPath}/php/${PHP_VER} ];then
                    cd ${rootPath}/plugins/php && bash install.sh uninstall ${PHP_VER}
                fi
                echo "Penghapusan instalasi PHP${PHP_VER} berhasil!"
            done
        fi
    fi
}

UNINSTALL_MEMCACHED()
{
    if [ -d ${serverPath}/memcached ];then
        echo -e "----------------------------------------------------"
        echo -e "Memeriksa lingkungan Memcached yang ada, penghapusan instalasi dapat memengaruhi situs dan data yang ada"
        echo -e "----------------------------------------------------"
        read -p "Ketik yes untuk menghapus semua Memcached secara paksa [yes/no]: " yes;
        if [ "$yes" != "yes" ];then
            echo -e "------------"
            echo "Membatalkan penghapusan instalasi Memcached"
        else
            cd ${rootPath}/plugins/memcached && bash install.sh uninstall
            echo "Penghapusan instalasi Memcached berhasil"
        fi
    fi
}

UNINSTALL_REDIS()
{
    if [ -d ${serverPath}/redis ];then
        echo -e "----------------------------------------------------"
        echo -e "Memeriksa lingkungan Redis yang ada, penghapusan instalasi dapat memengaruhi situs dan data yang ada"
        echo -e "----------------------------------------------------"
        read -p "Ketik yes untuk menghapus semua Redis secara paksa [yes/no]: " yes;
        if [ "$yes" != "yes" ];then
            echo -e "------------"
            echo "Membatalkan penghapusan instalasi Redis"
        else
            cd ${rootPath}/plugins/redis && bash install.sh uninstall 7.0.4
            echo "Penghapusan instalasi Redis berhasil"
        fi
    fi
}

UNINSTALL_MW()
{
    echo -e "----------------------------------------------------"
    echo -e "Memeriksa lingkungan mderver-web yang ada, penghapusan instalasi dapat memengaruhi situs dan data yang ada"
    echo -e "----------------------------------------------------"
    read -p "Ketik yes untuk menghapus instalasi panel secara paksa: " yes;
    if [ "$yes" != "yes" ];then
        echo -e "------------"
        echo "Membatalkan penghapusan instalasi panel"
    else
        rm -rf /usr/bin/slemp
        rm -rf /etc/init.d/slemp
        systemctl daemon-reload
        rm -rf ${rootPath}
        echo "Penghapusan instalasi panel berhasil"
    fi
}

UNINSTALL_CHECK

UNINSTALL_OP
UNINSTALL_PHP
UNINSTALL_MySQL
UNINSTALL_MEMCACHED
UNINSTALL_REDIS
UNINSTALL_MW

endTime=`date +%s`
((outTime=(${endTime}-${startTime})/60))
echo -e "Time consumed:\033[32m $outTime \033[0mMinute!"
