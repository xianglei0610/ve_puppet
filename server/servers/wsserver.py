

# For broswer websocket connect
# Cover JSON to Protobuf, send to socket

import json
import uuid

from tornado.ioloop import IOLoop
from tornado.web import Application

from config import ConfigSSH, ConfigWebSocket, ConfigSSL
from servers.base import BaseWebSocketHandler
from servers.clientmap import ConnectionMap
from utils.logger import InfoLogger


class PuppetWebSocketHandler(BaseWebSocketHandler):
    def open(self):
        self.set_init_attr()

        self.logger.info('[Puppet WS] connection opened from %s' % self.request.remote_ip)

        self.init_connect()

        if self.uid not in ConnectionMap.ws_conn.keys():
            ConnectionMap.ws_conn[self.uid] = self

    def init_connect(self):
        self.refresh_client_status()

    def refresh_client_status(self):
        # Return connecting robot info
        init_msg = json.dumps(ConnectionMap.client_status.values())
        self.write_message(init_msg)

    def on_message(self, message):
        self.logger.info('[Puppet WS] received message from %s: %s' % \
            (self.request.remote_ip, message))
        
        try:
            json_data = json.loads(message)

            if ConnectionMap.sock_conn:
                ConnectionMap.sock_conn.send_json_message(json_data, self.uid)

        except Exception as e:
            self.logger.info('[Puppet WS] on_message error: %s' % e)

    def on_close(self):
        self.logger.info('[Puppet WS] connection closed.')

        ConnectionMap.ws_conn.pop(self.uid)


class SSHWebSocketHandler(BaseWebSocketHandler):
    def open(self, uid):
        """Open websocket from broswer"""
        self.set_init_attr(uid)

        self.logger.info('[SSH] open ws with uid: %s' % uid)
        self.logger.info('[SSH] ws connection opened from %s' % self.request.remote_ip)

        term_id = uuid.uuid4().hex

        if ConnectionMap.ws_pairs.has_key(uid):
            pairs = ConnectionMap.ws_pairs[uid]
            pairs.setdefault(term_id, self)
            ConnectionMap.ws_pairs[uid] = pairs

        else:
            ConnectionMap.ws_pairs.setdefault(uid, {term_id : self})

        self.term_id = term_id

        self.start_ssh()

    def on_message(self, message):
        """Receive message from broswer, then send format message to proxy socket"""

        # message may be unicode string(chinese)
        self.logger.info('[SSH] received message from %s: %s' % \
            (self.request.remote_ip, message))
        
        sock = ConnectionMap.sock_pairs.get(self.uid, {}).get(self.term_id, None)

        if sock:
            dct = {
                'uid' : self.uid,
                'term_id' : self.term_id,
                'msg' : message.encode('utf-8'),
            }
            dct_string = json.dumps(dct) + ConfigSSH.delimiter

            try:
                sock.send_message(dct_string)
            except Exception as e:
                self.logger.info('[SSH] on_message error: %s' % e)

        else:
            self.logger.info('[SSH] no socket found with uid: %s' % self.uid)

    def on_close(self):
        """Broswer websocket close"""
        self.logger.info('[SSH] webSocket connection closed.')

        if ConnectionMap.ws_pairs.has_key(self.uid):
            ConnectionMap.ws_pairs[self.uid].pop(self.term_id)

        self.stop_ssh()

    def start_ssh(self):
        cmd = {
            'command' : 'start_ssh',
            'clients' : [self.uid],
            'args'    : [self.term_id],
        }
        self.send_to_puppet_sock(cmd)

    def stop_ssh(self):
        cmd = {
            'command' : 'stop_ssh',
            'clients' : [self.uid],
            'args'    : [self.term_id],
        }
        self.send_to_puppet_sock(cmd)

    def restart_ssh(self):
        cmd = {
            'command' : 'restart_ssh',
            'clients' : [self.uid],
            'args'    : [self.term_id],
        }
        self.send_to_puppet_sock(cmd)

    def send_to_puppet_sock(self, cmd):
        puppet_sock = ConnectionMap.clients.get(self.uid)
        ws_uid = 'ssh'

        if puppet_sock:
            puppet_sock.send_json_message(cmd, ws_uid)
        else:
            self.logger.info('[SSH] no puppet socket found with uid: %s' % self.uid)


class VideoWebSocketHandler(BaseWebSocketHandler):
    def open(self, robot_uid):
        self.set_init_attr()

        self.logger.info('[Video WS] connection opened from %s to %s' % \
            (self.request.remote_ip, robot_uid))

        # Returns a list of the arguments with the given name.
        scale = self.get_arguments('scale') or []

        self.robot_uid = robot_uid

        try:
            if ConnectionMap.video_ws_conn.has_key(robot_uid):
                # Another ws is connecting, video already running
                ConnectionMap.video_ws_conn[robot_uid].setdefault(self.uid, self)

            else:
                # No ws is connecting, start video
                # ConnectionMap.video_ws_conn.has_key(robot_uid) == False
                # or ConnectionMap.video_ws_conn[robot_uid] == {}
                ConnectionMap.video_ws_conn.setdefault(robot_uid, {self.uid : self})

            if not ConnectionMap.video_running.get(robot_uid, False):
                start_command = {
                    'command' : 'video_start',
                    'args' : scale,
                    'clients' : [self.robot_uid],
                }

                if ConnectionMap.sock_conn:
                    ConnectionMap.sock_conn.send_json_message(start_command, self.uid)

                ConnectionMap.video_running[robot_uid] = True

        except Exception as e:
            self.logger.info('[Video WS] open error: %s' % e)

    def on_close(self):
        self.logger.info('[Video WS] connection closed.')

        try:
            if ConnectionMap.video_ws_conn.has_key(self.robot_uid):
                if ConnectionMap.video_ws_conn[self.robot_uid].has_key(self.uid):
                    ConnectionMap.video_ws_conn[self.robot_uid].pop(self.uid)

                # if no ws is receiving the robot video, stop the video
                if not ConnectionMap.video_ws_conn[self.robot_uid]:
                    stop_command = {
                        'command' : 'video_stop',
                        'clients' : [self.robot_uid],
                    }

                    if ConnectionMap.sock_conn:
                        ConnectionMap.sock_conn.send_json_message(stop_command, self.uid)

                    ConnectionMap.video_running[self.robot_uid] = False

        except Exception as e:
            self.logger.info('[Video WS] on_close error: %s' % e)


class AudioWebSocketHandler(BaseWebSocketHandler):
    def open(self, robot_uid):
        self.set_init_attr()

        self.logger.info('[Audio WS] connection opened from %s to %s' % \
            (self.request.remote_ip, robot_uid))

        self.robot_uid = robot_uid

        try:
            if ConnectionMap.audio_ws_conn.has_key(robot_uid):
                # Another ws is connecting, audio already running
                ConnectionMap.audio_ws_conn[robot_uid].setdefault(self.uid, self)

            else:
                # No ws is connecting, start audio
                # ConnectionMap.audio_ws_conn.has_key(robot_uid) == False
                # or ConnectionMap.audio_ws_conn[robot_uid] == {}
                ConnectionMap.audio_ws_conn.setdefault(robot_uid, {self.uid : self})

            if not ConnectionMap.audio_running.get(robot_uid, False):
                start_command = {
                    'command' : 'audio_start',
                    'clients' : [self.robot_uid],
                }

                if ConnectionMap.sock_conn:
                    ConnectionMap.sock_conn.send_json_message(start_command, self.uid)

                ConnectionMap.audio_running[robot_uid] = True

        except Exception as e:
            self.logger.info('[Audio WS] open error: %s' % e)

    def on_close(self):
        self.logger.info('[Audio WS] connection closed.')

        try:
            if ConnectionMap.audio_ws_conn.has_key(self.robot_uid):
                if ConnectionMap.audio_ws_conn[self.robot_uid].has_key(self.uid):
                    ConnectionMap.audio_ws_conn[self.robot_uid].pop(self.uid)

                # if no ws is receiving the robot audio, stop the audio
                if not ConnectionMap.audio_ws_conn[self.robot_uid]:
                    stop_command = {
                        'command' : 'audio_stop',
                        'clients' : [self.robot_uid],
                    }

                    if ConnectionMap.sock_conn:
                        ConnectionMap.sock_conn.send_json_message(stop_command, self.uid)

                    ConnectionMap.audio_running[self.robot_uid] = False

        except Exception as e:
            self.logger.info('[Audio WS] on_close error: %s' % e)


# ---------------------------------------
# Server
# ---------------------------------------

class PuppetWebSocketServer(object):
    def __init__(self):
        self.logger = InfoLogger(__name__).get_logger()
        self.host = ConfigWebSocket.host
        self.port = ConfigWebSocket.port

    def start(self):
        try:
            app = Application([
                (r'/puppet', PuppetWebSocketHandler),
                (r'/puppet/ssh/([^/]*)', SSHWebSocketHandler),
                (r'/puppet/video/([^/]*)', VideoWebSocketHandler),
                (r'/puppet/audio/([^/]*)', AudioWebSocketHandler),
            ])
            self.logger.info("PuppetWebSocket Handler setup done")

            if ConfigSSL.enable:
                app.listen(address = self.host, port = self.port, 
                    ssl_options = {
                        "certfile" : ConfigSSL.certfile,
                        "keyfile" : ConfigSSL.keyfile,
                    }
                )
            else:
                app.listen(address = self.host, port = self.port)
            self.logger.info('Listening ws at ' + str(self.host) + ':' + str(self.port))

            ioloop = IOLoop()
            ioloop.current().start()

        except Exception as e:
            self.logger.info("PuppetWebSocketServer start error: %s" % e)

