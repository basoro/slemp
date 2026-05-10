#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH


DIR=$(cd "$(dirname "$0")"; pwd)
curPath=$DIR
rootPath=$(dirname "$(dirname "$DIR")")
serverPath=$(dirname "$rootPath")
export rootPath
export serverPath

VERSION=$2

Install_webssh()
{
	echo 'Sedang menginstal file skrip...'
	mkdir -p $serverPath/webssh
	echo "${VERSION}" > $serverPath/webssh/version.pl
	echo 'Instalasi selesai'

}

Uninstall_webssh()
{
	rm -rf $serverPath/webssh
	echo "Penghapusan instalasi selesai"
}

action=$1
if [ "${1}" == 'install' ];then
	Install_webssh
else
	Uninstall_webssh
fi
