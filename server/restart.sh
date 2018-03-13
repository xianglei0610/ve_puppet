#!/bin/bash

DIR=$(pwd)

MANAGE_FILE="manage.py"

# LOG_DIR="/var/log/axm_puppet"
LOG_DIR=$DIR

LOG_FILE="puppet_server.log"

echo 'Current dir: ' $DIR

if [ ! -d $LOG_DIR ]; then
    mkdir $LOG_DIR
fi

source $DIR/../bin/activate

cd $DIR
# nohup python $DIR/$MANAGE_FILE --restart >> $LOG_DIR/$LOG_FILE &
python $DIR/$MANAGE_FILE --restart &
