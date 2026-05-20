#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

function version_gt() { test "$(echo "$@" | tr " " "\n" | sort -V | head -n 1)" != "$1"; }
function version_le() { test "$(echo "$@" | tr " " "\n" | sort -V | head -n 1)" == "$1"; }
function version_lt() { test "$(echo "$@" | tr " " "\n" | sort -rV | head -n 1)" != "$1"; }
function version_ge() { test "$(echo "$@" | tr " " "\n" | sort -rV | head -n 1)" == "$1"; }

# cd /www/server/panel/plugins/gdrive && /bin/bash install.sh install 2.0

P_VER=`python3 -V | awk '{print $2}'`
echo "python:$P_VER"

DIR=$(cd "$(dirname "$0")"; pwd)
curPath=$DIR
rootPath=$(dirname "$(dirname "$DIR")")
serverPath=$(dirname "$rootPath")
export rootPath
export serverPath


PATH=$PATH:${rootPath}/bin
export PATH

# if [ -f ${rootPath}/bin/activate ];then
#     source ${rootPath}/bin/activate
# fi

VERSION=$2

Install_App()
{
    curl -s --connect-timeout 5 https://www.google.com > /dev/null 2>&1
    if [ $? -eq 0 ];then
        GDDIR=$serverPath/gdrive
        mkdir -p $GDDIR

        if [ ! -f ${GDDIR}/bin/activate ];then
            if version_ge "$P_VER" "3.11.0" ;then
                echo "python3 > 3.11"
                cd ${GDDIR} && python3 -m venv ${GDDIR}
            else
                echo "python3 < 3.10"
                cd ${GDDIR} && python3 -m venv .
            fi
        fi

        # Make pip installation robust using the virtualenv's direct pip binary
        ${GDDIR}/bin/pip install --upgrade pip -i https://pypi.org/simple
        ${GDDIR}/bin/pip install -I pyOpenSSL -i https://pypi.org/simple
        ${GDDIR}/bin/pip install -I google-api-python-client==2.39.0 google-auth-httplib2==0.1.0 google-auth-oauthlib==0.5.0 -i https://pypi.org/simple
        ${GDDIR}/bin/pip install -I httplib2==0.18.1 -i https://pypi.org/simple

        echo 'Sedang menginstal file skrip...'

        echo "${VERSION}" > $serverPath/gdrive/version.pl
        echo 'Instalasi selesai'
    else
        echo 'Server tidak dapat terhubung ke Google Cloud! Instalasi gagal!'
        exit 1
    fi
}

Uninstall_App()
{
	rm -rf $serverPath/gdrive
	echo 'Pencopotan selesai'
}


action=$1
type=$2

echo $action $type
if [ "${action}" == 'install' ];then
	Install_App
else
	Uninstall_App
fi
