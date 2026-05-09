#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

cd $PANEL_DIR
if [ -f bin/activate ];then
	source bin/activate
fi