#!/bin/sh

LOG_DIR="/home/nao/log"

if [ ! -d $LOG_DIR ]; then
    mkdir $LOG_DIR
fi

# DIR=$(pwd)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "Current dir: " $DIR

cd $DIR

# {
#     nohup python $DIR/manage.py --run >> $LOG_DIR/puppet_client.log &
# } || {
#     echo "Run failed " >> $LOG_DIR/puppet_client.log
#     echo "DIR: " $DIR
#     echo "LOG_DIR: " $LOG_DIR
#     echo
# }

python $DIR/manage.py --run &
