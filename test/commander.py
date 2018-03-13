# --------------------------------
# Author : Garvey Ding
# Created: 2016-10-31
# Modify : 2017-07-07 by Garvey
# --------------------------------

import json
import random
import socket

from serializers.serializer import CommanderSerializer


class ConfigServer(object):
    host = '120.24.3.143'
    # host = '192.168.0.30'
    # host = 'api.axmtec.com'
    port = 9528
    timeout = 5
    delimiter = '\r\t\n'


"""
class Client(object):
    def __init__(self):
        self.server_host = ConfigServer.host
        self.server_port = ConfigServer.port
        self.timeout = ConfigServer.timeout
        self.delimiter = ConfigServer.delimiter

    def connect(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)

        try:
            sock.connect((self.server_host, self.server_port))

            while 1:
                data = self.format_data()
                self.send_data(sock, data)

                # data = sock.recv(1024)
                # print 'Received', repr(data)

        except KeyboardInterrupt:
            print 'Got Ctrl+C, exiting...'
            sock.close()

    def send_data(self, sock, data):
        if isinstance(data, list):
            for dct in data:
                sock.sendall(dct)

        else:
            sock.sendall(data)

    def format_data(self):
        try:
            command = raw_input('command >')

            clients = raw_input('clients >')
            clients = clients.split(' ') if clients else None

            args = raw_input('args >')
            args = args.split(' ') if args else []


            if command == 'fg':
                lst = self.format_finger_game_command(clients)
                f_lst = [json.dumps(dct) + self.delimiter for dct in lst]

                print 'format_data: %s' % json.dumps(lst)
                return f_lst

            # elif command == 'count_off':
            #     dct = {'command' : command, 'clients' : clients, 'args' : args}

            else:
                dct = {'command' : command, 'clients' : clients, 'args' : args}

                f_dct = json.dumps(dct)
                print 'format_dct: %s' % f_dct
                return f_dct + self.delimiter

        except Exception as e:
            print 'format_data error: %s' % e
            return '' + self.delimiter

    def format_finger_game_command(self, clients):
        assert len(clients) == 2, 'length of clients is not 2'

        random.shuffle(clients)
        gesture = ['rock', 'scissors', 'paper']

        rule = {
            'rock' : {
                'win' : 'scissors',
            },
            'scissors' : {
                'win' : 'paper',
            },
            'paper' : {
                'win' : 'rock',
            },
        }

        winner = clients[0]
        loser = clients[1]

        winner_result = 'win'
        loser_result = 'lose'

        winner_gesture = random.choice(gesture)
        loser_gesture = rule.get(winner_gesture).get('win')

        winner_args = [winner_result, winner_gesture]
        loser_args = [loser_result, loser_gesture]

        return [
            {'command' : 'finger_game', 'clients' : [winner], 'args' : winner_args},
            {'command' : 'finger_game', 'clients' : [loser], 'args' : loser_args}
        ]
"""


class Client(object):
    def __init__(self):
        self.server_host = ConfigServer.host
        self.server_port = ConfigServer.port
        self.timeout = ConfigServer.timeout
        self.delimiter = ConfigServer.delimiter

    def connect(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)

        try:
            sock.connect((self.server_host, self.server_port))
            print 'peername : %s' % str(sock.getpeername())
            print 'sockname : %s' % str(sock.getsockname())

            while 1:
                data = self.format_data()

                if data:
                    self.send_data(sock, data)

                # data = sock.recv(1024)
                # print 'Received', repr(data)

        except KeyboardInterrupt:
            print 'Got Ctrl+C, exiting...'
            sock.close()

    def send_data(self, sock, data):
        if isinstance(data, list):
            for dct in data:
                sock.sendall(dct)

        else:
            sock.sendall(data)

    def format_data(self):
        try:
            command = raw_input('command >')

            clients = raw_input('clients >')
            clients = clients.split(' ') if clients else None

            args = raw_input('args >')
            args = args.split(' ') if args else []

            if command:
                dct = {'command' : command, 'clients' : clients, 'args' : args}

                cs = CommanderSerializer()
                msg = cs.dict_to_string(dct)

                # msg = json.dumps(dct)

                print 'msg: %r' % msg
                return msg + self.delimiter

            else:
                print 'No command'
                return ''

            # if command == 'fg':
            #     lst = self.format_finger_game_command(clients)
            #     f_lst = [json.dumps(dct) + self.delimiter for dct in lst]

            #     print 'format_data: %s' % json.dumps(lst)
            #     return f_lst

            # elif command == 'count_off':
            #     dct = {'command' : command, 'clients' : clients, 'args' : args}

            # else:
            #     dct = {'command' : command, 'clients' : clients, 'args' : args}

            #     f_dct = json.dumps(dct)
            #     print 'format_dct: %s' % f_dct
            #     return f_dct + self.delimiter

        except Exception as e:
            print 'format_data error: %s' % e
            return ''


if __name__ == '__main__':
    client = Client()
    client.connect()
