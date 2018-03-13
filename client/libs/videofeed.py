

import base64
import json
import select
import socket
import threading

import uuid
import zlib

from tornado import gen 
from tornado.ioloop import IOLoop

from config import ConfigVideo
from utils.func import get_timestamp
from utils.logger import InfoLogger


def format_send_data(robot_uid, image_uid, image_dct):
    """Format data to send into socket"""
    dct = {
        'robot_uid' : robot_uid,
        'image_uid' : image_uid,

        # 'index' : image_dct.get('index'),
        # 'content' : image_dct.get('content'),

        # 'ts' : image_dct.get('ts'),
        # 'width' : image_dct.get('width'),
        # 'height' : image_dct.get('height'),
        # 'color_space' : image_dct.get('color_space'),
    }

    dct.update(image_dct)

    dct_str = json.dumps(dct)
    return dct_str + ConfigVideo.delimiter


def format_image_data(image_container):
    # http://doc.aldebaran.com/2-5/naoqi/vision/alvideodevice-api.html#image
    # Image container is an array as follow:
    # [0]: width.
    # [1]: height.
    # [2]: number of layers.
    # [3]: ColorSpace.
    # [4]: time stamp from qi::Clock (seconds).   ???
    # [5]: time stamp from qi::Clock (microseconds).   ???
    # [6]: binary array of size height * width * nblayers containing image data.
    # [7]: camera ID (kTop=0, kBottom=1).
    # [8]: left angle (radian). ???
    # [9]: topAngle (radian). ???
    # [10]: rightAngle (radian). ???
    # [11]: bottomAngle (radian). ???

    ts = get_timestamp()
    width = image_container[0]
    height = image_container[1]
    color_space = image_container[3]
    image = image_container[6]

    # left_angle = image_container[8]
    # top_angle = image_container[9]

    # binary data to string, and compress data
    image_compressed = zlib.compress(str(image))

    # compressed data would be binary, encode into string
    image_encoded = base64.b64encode(image_compressed)

    # devide image string into multiple packages
    # small package will send faster 
    length = len(image_encoded)
    page = ConfigVideo.page
    size = length / page

    lst = []
    for i in range(page):
        if i+1 == page:
            # The last page
            content = image_encoded[i*size:]
        else:
            content = image_encoded[i*size:(i+1)*size]

        dct = {
            'index': i,
            'content': content,

            'ts': ts,
            'width': width,
            'height': height,
            'color_space': color_space,
        }

        lst.append(dct)

    return lst


@gen.coroutine
def run_video_feed(robot_uid, sock, func, handle):
    logger = InfoLogger(__name__).get_logger()
    logger.info('[Video] run_video_feed start')

    try:
        while True:

            try:
                select.select([], [sock], [])
            except socket.error:
                logger.info('[Video] socket shutdown')
                break

            # image_container = yield func(handle)
            image_container = func(handle)
            image_data_lst = format_image_data(image_container)
            
            image_uid = uuid.uuid4().hex

            for image_dct in image_data_lst:
                send_data = format_send_data(robot_uid, image_uid, image_dct)
                sock.sendall(send_data)

            # logger.info('[Video] run_video_feed done')

    except Exception as e:
        logger.info('[Video] run_video_feed error : %s' % e)

    logger.info('[Video] run_video_feed exit done')


def start_video_feed(robot_uid, sock, func, handle):
    ioloop = IOLoop()
    ioloop.current().run_sync(\
        lambda: run_video_feed(robot_uid, sock, func, handle))


class VideoFeedProxy(object):
    def __init__(self, robot_uid):
        self.logger = InfoLogger(__name__).get_logger()

        self.host = ConfigVideo.host
        self.port = ConfigVideo.port
        self.robot_uid = robot_uid

        self.sock = None

    def start(self, func, handle):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, self.port))
            self.logger.info('video_feed socket setup done')

            self.sock = sock

            v_thread = threading.Thread( \
                target = start_video_feed, \
                kwargs = {'robot_uid' : self.robot_uid, 'sock' : sock,
                          'func' : func, 'handle' : handle})

            v_thread.start()

            self.logger.info('VideoProxy start done')

        except Exception as e:
            self.logger.info('VideoProxy.start error : %s' % e)

    def stop(self):

        if self.sock:
            try:
                # shutdown will send '' to socket, 
                # writer can cache and exit
                self.sock.shutdown(socket.SHUT_RDWR)

                self.sock.close()
                # self.sock = None
                self.logger.info('VideoProxy stop socket done')

            except Exception as e:
                self.logger.info('VideoProxy stop socket error : %s' % e)

        else:
            self.logger.info('VideoProxy no socket to stop')

        self.logger.info('VideoProxy stop done')
