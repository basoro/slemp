#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin:/opt/homebrew/bin
export PATH

curPath=`pwd`
rootPath=$(dirname "$curPath")
rootPath=$(dirname "$rootPath")
rootPath=$(dirname "$rootPath")
rootPath=$(dirname "$rootPath")

# echo $rootPath

SERVER_ROOT=$rootPath/lib
SOURCE_ROOT=$rootPath/source/lib

mkdir -p  $SOURCE_ROOT

if [ ! -d ${SERVER_ROOT}/libzip ];then

    cd $SOURCE_ROOT

    if [ ! -f ${SOURCE_ROOT}/libzip-1.3.2.tar.gz ];then
        wget --no-check-certificate -O libzip-1.3.2.tar.gz https://github.com/midoks/panel/releases/download/init/libzip-1.3.2.tar.gz -T 20
    fi

    if [ ! -d ${SOURCE_ROOT}/libzip-1.3.2 ];then
        cd $SOURCE_ROOT && tar -zxvf libzip-1.3.2.tar.gz
    fi

    cd ${SOURCE_ROOT}/libzip-1.3.2

    ./configure --prefix=${SERVER_ROOT}/libzip && make && make install
    #cd $SOURCE_ROOT

    if [ "$?" == "0" ];then
        rm -rf ${SOURCE_ROOT}/libzip-1.3.2
        rm -rf ${SOURCE_ROOT}/libzip-1.3.2.tar.gz
    fi

fi