

import base64
import json

from config import ConfigAudio
from servers.clientmap import ConnectionMap
from servers.base import BaseConnection, BaseTCPServer


class AudioConnection(BaseConnection):
    def __init__(self, stream, address):
        self.delimiter = ConfigAudio.delimiter
        super(AudioConnection, self).__init__(stream, address, self.delimiter)

    def on_message_read(self, data):
        self.logger.info('AudioServer receive: %r' % data)
        data_str = data.rstrip(self.delimiter)

        try:
            data_dct = json.loads(data_str)

            robot_uid = data_dct.get('robot_uid')
            audio_data = data_dct.get('audio_data')

            self.write_to_local(audio_data)
            self.send_to_ws(data_str, robot_uid)

        except Exception as e:
             self.logger.info('AudioServer on_message_read error: %s' % e)

        self.read_message()

    def write_to_local(self, buffer):
        binary_data = base64.b64decode(buffer)
        with open('/tmp/test.wav', 'a') as f:
            f.write(binary_data)

    def send_to_ws(self, data, robot_uid):
        try:
            ws_dict = ConnectionMap.audio_ws_conn.get(robot_uid, {})

            if ws_dict:
                for ws_obj in ws_dict.values():
                    ws_obj.write_message(data)
            else:
                self.logger.info('AudioServer no ws found with robot_uid: %s' % robot_uid)

        except Exception as e:
            self.logger.info('AudioServer send_to_ws error: %s' % e)


class AudioServer(BaseTCPServer):
    def __init__(self):
        self.port = ConfigAudio.port
        self.connection = AudioConnection

        super(AudioServer, self).__init__(self.port, self.connection)
