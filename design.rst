
Robot Control System
==========================
Code: Emperor


Part I : Robot
-----------------
* Init run process on robot
* Detect whether internet is connected
* Create socket as soon as connected to internet
* Send message to server on cloud(robot ip address, robot location, ...)
* Run commands send from server(Restart, Stop, Get event subscribers, ...)
* Heart beat & Health check


Part II : Server On Cloud
---------------------------
* Nginx + uWSGI + Tornado/Django + Redis + MySQL + RabbitMQ + Jenkins/Ansible
* All service run as Docker Container
* Send commands to one or more Robot at the same time
* Commands send into queue
* Divide robots with tag/group
* Install behavior to robot through server?
* Display robot view?


Part III : Webview
---------------------------
* React + Redux + React Router
* Should be run flexable on browser/Android/iOS
* Index on left, button/form/table on the right


Part EX : Other Service
---------------------------
* Direct shell connect in browser
* Pad template
* QA update




.. server端socket端口：9528
.. 数据协议使用 protobuf (https://developers.google.com/protocol-buffers/docs/pythontutorial)

.. 上报机器人自己信息包括：
.. 设备ID: BodyID
.. 自己ip，包括内网外网ip
.. 电量、是否正在充电中
.. 传感器是否正常，是否有报警

.. 初步实现远程简单的命令控制：
.. 重启, 关机
.. 打开、关闭、设置 BasicAwareness

.. 需要考虑，当client与 server端的协议有增加时，机器人里面的client如何更新？


.. 机器人断网重连
.. log?
.. start-stop-daemon/supervisor!

.. terminate called after throwing an instance of 'qi FutureUserException'
..   what():  Promise broken (all promises are destroyed)
.. Aborted


Data from Robot
---------------------------

Send to server in time delta

    .. code-block:: javascript

        {
            'ip_addr'   : '...',
            'body_id'   : '...',
            'power_remain' : '...',

            'is_charging' : True,
            'sensor' : '...',
            'alert' : '...',
        }



Topology
---------------------------

Normal message(Robot Info)
* Robot -> Tornado(Socket Server) -> RabbitMQ(Queue) -> Django(Logic) -> Web

Web shell & Web robot view
* Robot -> Tornado(Socket Server) -> Web






Message Distribution
=========================

Web
----------

GET 
/robot/list
/robot?body_id=xxx&name=pepper

POST 
/robot

[
    {   
        'client' : '192.168.1.10',
        'client' : {
            'ip' : '192.168.1.10',
        },
        'command' : 'count_off',
        'args' : ['1'],
    },
    {   
        'client' : '192.168.1.104',
        'command' : 'count_off',
        'args' : ['2'],
    },
]



ManageServer
----------------

translate
{
    'send_to' : ['192.168.1.10', '192.168.1.104'],
    'command' : 'count_off',
    'args' : ['1', '2'],
}

push into queue(producer)



TCPServer
-------------
get command(customer)


push robot info(producer)




RobotClient 
--------------








Install package online
--------------------------

[My computer]
# package rename to new.pkg
mv *.pkg new.pkg

# package upload to data30.axmtec.com:/tmp/new.pkg
scp new.pkg garvey@data30.axmtec.com:/tmp

[Robot]
scp garvey@data30.axmtec.com:/tmp/new.pkg /tmp
http download
Resume broken downloads

[CommandSender]
install_package /tmp/new.pkg

if 'has_package {pkg_name}':
    'success'
else:
    'failed'






Commander
==================

Send Command

{
    'commander': [
        {
            "command" : "count_off", 
            "client" : "a", 
            "args" : 1,
        },
        {
            "command" : "count_off", 
            "client" : "b", 
            "args" : 2,
        },
    ]
}



Client
==================

Collector
-------------

{
    'collector': {
        "command" : "count_off", 
        "client" : "b", 
        "args" : 2,
    },
}

Excutor
-----------
recv protobuf string
serializer to command

"a" received:
{
    "command" : "count_off", 
    "args" : [1,]
}







SSH
--------------------------
 
Server "start ssh"
-> Robot receive and start ptyprocess
-> Web connect and send command from Server to Robot
-> Robot excute
-> Robot send result Server


install.sh install terminado?
pip install terminado

npm init
npm install --save xterm


Out of client?
Safety?

expired?
ws close on index terminate
