#!/bin/sh

LOG_DIR="/home/nao/log"

if [ ! -d $LOG_DIR ]; then
    mkdir $LOG_DIR
fi

DIR=$(pwd)
echo "Current dir: " $DIR

cd $DIR

# nohup python $DIR/manage.py --restart >> $LOG_DIR/puppet_client.log &
python $DIR/manage.py --restart &
