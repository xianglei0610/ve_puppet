

# For broswer video websocket connect

import base64
import json
import zlib
from collections import OrderedDict

from config import ConfigVideo
from servers.clientmap import ConnectionMap
from servers.base import BaseConnection, BaseTCPServer


class ImageMap(object):
    # package = {
    #     'uid' : {
    #         'index_1' : 'pkg_1',
    #         'index_2' : 'pkg_2',
    #     },
    # }
    package = {}


class VideoConnection(BaseConnection):
    def __init__(self, stream, address):
        self.delimiter = ConfigVideo.delimiter
        super(VideoConnection, self).__init__(stream, address, self.delimiter)

    def on_message_read(self, data):
        # self.logger.info('VideoServer receive: %r' % data)
        # self.logger.info('VideoServer receive len : %s' % len(data))
        data = data.rstrip(self.delimiter)

        try:
            data_j = json.loads(data)

            robot_uid = data_j.get('robot_uid', None)
            image_uid = data_j.get('image_uid', None)

            image_index = data_j.get('index', None)
            image_data = data_j.get('content', None)

            assert robot_uid and image_uid and image_data, 'VideoServer image data error'

            # self.logger.info('image_uid %s image_index %s image_data len %s' % \
            #     (image_uid, image_index, len(image_data or '')))

            image = self.join_image_pkg(image_uid, image_index, image_data)

            if image:
                # image_ts = data_j.get('ts', None)

                # For debug
                # local_ts = int(round(time.time() * 1000))
                # self.logger.info('image_ts %s local_ts %s delta %s' % \
                #     (image_ts, local_ts, local_ts - image_ts))

                raw_image = self.reduce_image(image)

                raw_image_b = bytearray(raw_image)

                dct = { 
                    'image' : list(raw_image_b), 

                    'ts' : data_j.get('ts', None),
                    'width' : data_j.get('width', None),
                    'height' : data_j.get('height', None),
                    'color_space' : data_j.get('color_space', None),
                }
                dct_str = json.dumps(dct)

                self.send_to_ws(dct_str, robot_uid)

        except Exception as e:
             self.logger.info('VideoServer on_message_read error: %s' % e)

        self.read_message()

    def join_image_pkg(self, image_uid, image_index, image_data):
        """join image pkg into complete image"""
        page = ConfigVideo.page

        # if image pkgs do not all arrive in expire time?
        # if image2 all arrive before image1?

        if not ImageMap.package.has_key(image_uid):
            ImageMap.package.setdefault(image_uid, {image_index:image_data})

        else:
            ImageMap.package[image_uid].setdefault(image_index, image_data)

            if len(ImageMap.package[image_uid]) == page:
                # all image package received
                pkg_dct = ImageMap.package.pop(image_uid)

                # dictionary sorted by key
                ordered_pkg_dct = OrderedDict(sorted(pkg_dct.items(), key=lambda t: t[0]))

                full_image = reduce(lambda p_1,p_2: p_1+p_2, ordered_pkg_dct.values())

                return full_image

        return None

    def reduce_image(self, image):
        image_compressed = base64.b64decode(image)
        raw_image = zlib.decompress(image_compressed)

        return raw_image

    def send_to_ws(self, data, robot_uid):
        """Send to broswer through websocket"""
        try:
            ws_dict = ConnectionMap.video_ws_conn.get(robot_uid, {})

            if ws_dict:
                for ws_obj in ws_dict.values():
                    ws_obj.write_message(data)
            else:
                self.logger.info('VideoServer no ws found with robot_uid: %s' % robot_uid)

        except Exception as e:
            self.logger.info('VideoServer send_to_ws error: %s' % e)


class VideoServer(BaseTCPServer):
    def __init__(self):
        self.port = ConfigVideo.port
        self.connection = VideoConnection

        super(VideoServer, self).__init__(self.port, self.connection)
