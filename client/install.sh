#!/bin/sh

DIR=$(pwd)
echo 'Current dir: ' $DIR

cd $DIR

echo 'Change mod of run.sh & restart.sh'
chmod 755 run.sh
chmod 755 restart.sh

echo 'pip install protobuf for user'
pip install protobuf --user

echo 'pip install terminado for user'
pip install terminado --user

echo 'pip install requests for user'
pip install requests --user

echo 'pip install ffmpy for user'
pip install ffmpy --user

# check whether $DIR/run.sh in /home/nao/naoqi/preferences/autoload.ini
if grep -Fxq "$DIR/run.sh" /home/nao/naoqi/preferences/autoload.ini
then
    echo "$DIR/run.sh already in autoload.ini"
else
    echo "$DIR/run.sh" >> /home/nao/naoqi/preferences/autoload.ini
    echo "Append $DIR/run.sh into autoload.ini done"
fi
