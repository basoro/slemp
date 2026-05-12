#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin:/opt/homebrew/bin
export PATH

curPath=`pwd`
rootPath=$(dirname "$curPath")
rootPath=$(dirname "$rootPath")
rootPath=$(dirname "$rootPath")
rootPath=$(dirname "$rootPath")

# cd ${rootPath}/plugins/php/lib && bash libiconv.sh

# echo $rootPath

SERVER_ROOT=$rootPath/lib
SOURCE_ROOT=$rootPath/source/lib

if [ ! -d ${SERVER_ROOT}/libiconv ];then
    cd $SOURCE_ROOT

    if [ ! -f ${SOURCE_ROOT}/libiconv-1.15.tar.gz ];then
	   wget --no-check-certificate -O ${SOURCE_ROOT}/libiconv-1.15.tar.gz https://github.com/midoks/panel/releases/download/init/libiconv-1.15.tar.gz  -T 5
    fi

    if [ ! -d ${SOURCE_ROOT}/libiconv-1.15 ];then
        cd $SOURCE_ROOT && tar -zxvf libiconv-1.15.tar.gz
    fi

    cd ${SOURCE_ROOT}/libiconv-1.15

    ./configure --prefix=${SERVER_ROOT}/libiconv --enable-static && make && make install

    if [ -d $SOURCE_ROOT/libiconv-1.15 ];then 
        cd $SOURCE_ROOT && rm -rf $SOURCE_ROOT/libiconv-1.15
    fi
fi