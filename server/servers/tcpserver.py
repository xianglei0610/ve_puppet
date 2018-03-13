

import json
import uuid

from config import ConfigServer
from serializers.serializer import BaseSerializer, ExecutorSerializer
from servers.clientmap import ConnectionMap, ClientManager
from servers.base import BaseConnection, BaseTCPServer


class PuppetConnection(BaseConnection):
    def __init__(self, stream, address):
        self.delimiter = ConfigServer.delimiter

        self.uid_key = 'uid'
        self.set_uid()

        super(PuppetConnection, self).__init__(stream, address, self.delimiter)

    def set_uid(self, uid=None):
        if not uid:
            uid = uuid.uuid4().hex

        if not hasattr(self, self.uid_key):
            setattr(self, self.uid_key, uid)
            ConnectionMap.clients.setdefault(self.get_uid(), self)

        else:
            r_uid = self.get_uid()

            if r_uid != uid:
                setattr(self, self.uid_key, uid)
                ConnectionMap.clients[uid] = ConnectionMap.clients.pop(r_uid)

    def get_uid(self):
        return getattr(self, self.uid_key)

    def on_message_read(self, msg):
        msg = msg.rstrip(self.delimiter)

        # self.logger.info('receive: %r' % msg)

        try:
            base_szer = BaseSerializer()
            msg_obj = base_szer.parse_from_string(msg)

            if msg_obj.character == 'collector':
                info = json.loads(msg_obj.collector.info)
                body_id = info.get('body_id', None)

                self.set_uid(body_id)

                ConnectionMap.client_status[self.get_uid()] = info
                info.setdefault('character', 'collector')

                # Send info to broswer
                self.send_to_ws(json.dumps(info))

            elif msg_obj.character == 'raiser':
                origin = msg_obj.raiser.origin

                dct = {
                    'character' : 'raiser',
                    'uid'       : self.get_uid(),
                    'command'   : msg_obj.raiser.command,
                    'args'      : list(msg_obj.raiser.args),
                    'response'  : msg_obj.raiser.response,
                    'exception' : msg_obj.raiser.exception,
                }

                self.send_to_ws(ws_uid = origin, data = json.dumps(dct))

            elif msg_obj.character == 'commander':
                c_uid_list = msg_obj.commander.clients
                self.logger.info('c_uid_list: %s' % c_uid_list)
                c_uid_set = set(c_uid_list)

                exec_dict = {
                    'command' : msg_obj.commander.command,
                    'args' : msg_obj.commander.args,
                    'origin' : 'commander',
                }

                executor_szer = ExecutorSerializer()
                exec_string = executor_szer.dict_to_string(exec_dict)

                if exec_string:

                    if c_uid_set:
                        for c_uid in c_uid_set:
                            client = ConnectionMap.clients.get(c_uid, None)
                            if client: 
                                client.send_message(exec_string)
                    else:
                        self.broadcast_messages(exec_string)

                else:
                    self.logger.info('exec_string is empty')

        except Exception as e:
            self.logger.info('explain messages error: %s' % e)

        self.read_message()

    def send_to_ws(self, data, ws_uid=None):
        if ConnectionMap.ws_conn:
            if ws_uid:
                conn = ConnectionMap.ws_conn.get(ws_uid, None)
                if conn:
                    conn.write_message(data)

            else:
                for conn in ConnectionMap.ws_conn.values():
                    conn.write_message(data)

    def send_message(self, data):
        self.logger.info('send message %r to %s' % (data, self._address))

        try:
            self._stream.write(data)
        except Exception as e:
            self.logger.info('send messages error: %s' % e)

    def broadcast_messages(self, data):
        self.logger.info('broadcast message: %r' % data)

        for uid, client in ConnectionMap.clients.iteritems():
            if client == self:
                continue
            client.send_message(data)

    def on_close(self):
        self.logger.info('client close: %s' % str(self._address))

        uid = self.get_uid()

        if ConnectionMap.clients.has_key(uid):
            self.logger.info('ConnectionMap clients pop: %s' % uid)
            ConnectionMap.clients.pop(uid)
            # iostream_obj = ConnectionMap.clients.pop(uid)

            # if not iostream_obj._stream.closed():
            #     self.logger.info('Client iostream close: %s' % uid)
            #     iostream_obj._stream.close()

        if ConnectionMap.client_status.has_key(uid):
            self.logger.info('ConnectionMap client_status pop: %s' % uid)
            ConnectionMap.client_status.pop(uid)

        for conn in ConnectionMap.ws_conn.values():
            conn.refresh_client_status()

    def send_json_message(self, data, ws_uid):
        try:
            command = data.get('command', None)
            c_uid_list = data.get('clients', [])
            args = data.get('args', [])

            self.logger.info('c_uid_list: %s' % c_uid_list)
            c_uid_set = set(c_uid_list)

            exec_dict = {
                'command' : command,
                'args' : args,
                'origin' : ws_uid,
            }

            executor_szer = ExecutorSerializer()
            exec_string = executor_szer.dict_to_string(exec_dict)

            if exec_string:

                if c_uid_set:
                    for c_uid in c_uid_set:
                        client = ConnectionMap.clients.get(c_uid, None)
                        if client: 
                            client.send_message(exec_string)
                else:
                    self.broadcast_messages(exec_string)

            else:
                self.logger.info('exec_string is empty')

        except Exception as e:
            self.logger.info('send_json_message error: %s' % e)


class PuppetServer(BaseTCPServer):
    def __init__(self):
        self.port = ConfigServer.port
        self.connection = PuppetConnection

        super(PuppetServer, self).__init__(self.port, self.connection)

    def handle_stream(self, stream, address):
        self.logger.info("[%s] new connection : %s %s" % (self.name, address, stream))

        conn = self.connection(stream, address)

        self.logger.info('[%s] connect count: %s' % \
            (self.name, len(ConnectionMap.clients)))

        if not ConnectionMap.sock_conn:
            ConnectionMap.sock_conn = conn

        # ClientManager.clean_defunct_client()
