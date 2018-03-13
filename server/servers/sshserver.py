
import json
import uuid

from config import ConfigSSH
from servers.clientmap import ConnectionMap
from servers.base import BaseConnection, BaseTCPServer


class SSHConnection(BaseConnection):
    def __init__(self, stream, address):
        self.delimiter = ConfigSSH.delimiter

        self.uid_key = 'uid'
        self.set_uid()

        super(SSHConnection, self).__init__(stream, address, self.delimiter)

    def set_uid(self, uid=None):
        if not uid:
            uid = str(uuid.uuid4())

        if not hasattr(self, self.uid_key):
            setattr(self, self.uid_key, uid)

        else:
            r_uid = self.get_uid()

            if r_uid != uid:
                setattr(self, self.uid_key, uid)

    def get_uid(self):
        return getattr(self, self.uid_key)

    def on_message_read(self, msg_string):
        msg_string = msg_string.rstrip(self.delimiter)

        # self.logger.info('receive: %r' % msg_string)
        
        try:
            msg_dct = json.loads(msg_string)

            uid = msg_dct.get('uid', None)
            term_id = msg_dct.get('term_id', None)
            msg = msg_dct.get('msg', None)

            if uid:
                self.set_uid(uid)
                self.term_id = term_id

                # self.logger.info('setup socket with uid: %s' % uid)
                # ConnectionMap.sock_pairs.setdefault(uid, self)

                if ConnectionMap.sock_pairs.has_key(uid):
                    pairs = ConnectionMap.sock_pairs[uid]
                    pairs.setdefault(term_id, self)
                    ConnectionMap.sock_pairs[uid] = pairs

                else:
                    ConnectionMap.sock_pairs.setdefault(uid, {term_id : self})

                ws = ConnectionMap.ws_pairs.get(uid, {}).get(term_id, None)

                if ws:
                    ws.write_message(msg)
                else:
                    self.logger.info('[SSH] No ws found with term_id : %s' % term_id)

        except Exception as e:
            self.logger.info('[SSH] explain messages error: %s' % e)

        self.read_message()

    def send_message(self, data):
        # self.logger.info('[SSH] send message %r to %s' % (data, self._address))
        try:
            self._stream.write(data)
        except Exception as e:
            self.logger.info('[SSH] send messages error: %s' % e)

    def on_close(self):
        self.logger.info('[SSH] client close: %s' % str(self._address))
        uid = self.get_uid()

        # if ConnectionMap.sock_pairs.has_key(uid):
        #     ConnectionMap.sock_pairs.pop(uid)

        if ConnectionMap.sock_pairs.has_key(uid):
            ConnectionMap.sock_pairs[uid].pop(self.term_id)


class SSHSocketServer(BaseTCPServer):
    def __init__(self):
        self.port = ConfigSSH.sock_port
        self.connection = SSHConnection

        super(SSHSocketServer, self).__init__(self.port, self.connection)
