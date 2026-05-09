#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:/opt/homebrew/bin:~/bin
export PATH
LANG=en_US.UTF-8

PANEL_DIR=$(cd "$(dirname "$0")/../../"; pwd)
DEV=$(dirname "$PANEL_DIR")

mkdir -p $DEV
mkdir -p $DEV/wwwroot
mkdir -p $DEV/server
mkdir -p $DEV/wwwlogs
mkdir -p $DEV/backup/database
mkdir -p $DEV/backup/site

# install brew
if ! command -v brew &> /dev/null; then
	/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

brew install libzip bzip2 gcc openssl re2c cmake wget

if [ ! -d $DEV/server/lib ]; then
	cd $PANEL_DIR/scripts && bash lib.sh
fi

mkdir -p $PANEL_DIR/logs
chmod 755 $PANEL_DIR/data
if [ -f $PANEL_DIR/bin/activate ];then
    cd $PANEL_DIR && python3 -m venv $PANEL_DIR
    source $PANEL_DIR/bin/activate
    pip3 install -r $PANEL_DIR/requirements.txt
else
	cd $PANEL_DIR && pip3 install -r $PANEL_DIR/requirements.txt
fi

cd $PANEL_DIR && ./cli.sh start
n=0
while [ ! -f $PANEL_DIR/scripts/init.d/slemp ];
do
    echo -e ".\c"
    sleep 1
    let n+=1
    if [ $n -gt 20 ];then
    	echo -e "generate init.d/slemp fail"
    	break
    fi
done
cd $PANEL_DIR && ./cli.sh stop

sleep 5
cd $PANEL_DIR && ./scripts/init.d/slemp start
cd $PANEL_DIR && ./scripts/init.d/slemp default
