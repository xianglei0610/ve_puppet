

import base64
import json
import select
import shlex
import socket
import subprocess
import threading

# from tornado.ioloop import IOLoop

from config import ConfigAudio
from utils.func import get_timestamp
from utils.logger import InfoLogger


def format_send_data(robot_uid, audio_data):
    """Format data to send into socket"""
    dct = {
        'robot_uid' : robot_uid,
        'audio_data' : base64.b64encode(audio_data),
        'ts' : get_timestamp(),
    }
    dct_str = json.dumps(dct)
    return dct_str + ConfigAudio.delimiter


def run_audio_stream(robot_uid, sock, proc):
    logger = InfoLogger(__name__).get_logger()
    logger.info('[Audio] run_audio_stream start')

    try:
        while True:
            if proc.poll():
                break

            output = proc.stdout.read(ConfigAudio.buffer_size)

            try:
                select.select([], [sock], [])
            except socket.error:
                logger.info('[Audio] socket shutdown')
                break

            format_data = format_send_data(robot_uid, output)
            sock.sendall(format_data)

            # logger.info('[Audio] send output : %s' % format_data)

    except Exception as e:
        logger.info('[Audio] run_audio_stream error : %s' % e)

    if not proc.poll():
        proc.terminate()
    #     proc.kill()

    logger.info('[Audio] run_audio_stream exit done')


class AudioStreamProxy(object):
    def __init__(self, robot_uid=None):
        self.logger = InfoLogger(__name__).get_logger()

        self.host = ConfigAudio.host
        self.port = ConfigAudio.port
        self.file_type = ConfigAudio.file_type
        self.rate = ConfigAudio.rate

        self.robot_uid = robot_uid

        self.sock = None
        self.proc = None

    def start(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, self.port))
            self.logger.info('audio_stream socket setup done')

            self.sock = sock
            
            command = 'arecord -t {file_type} -r {rate}'.\
                format(file_type = self.file_type, rate = self.rate)

            proc = subprocess.Popen(shlex.split(command), stdout = subprocess.PIPE)

            self.proc = proc

            a_thread = threading.Thread( \
                target = run_audio_stream, \
                kwargs = {'robot_uid' : self.robot_uid, 'sock' : sock, 'proc' : proc})

            a_thread.start()

            # multiple client read one proc at the same time?

            self.logger.info('AudioStreamProxy start done')

        except Exception as e:
            self.logger.info('AudioStreamProxy.start error : %s' % e)

    def stop(self):
        if self.proc:
            try:
                self.proc.terminate()
                # self.proc.kill()
                self.logger.info('AudioStreamProxy stop proc done')

            except Exception as e:
                self.logger.info('AudioStreamProxy stop proc error : %s' % e)

        if self.sock:
            try:
                # shutdown will send '' to socket, 
                # writer can cache and exit
                self.sock.shutdown(socket.SHUT_RDWR)

                self.sock.close()
                # self.sock = None
                self.logger.info('AudioStreamProxy stop socket done')

            except Exception as e:
                self.logger.info('AudioStreamProxy stop socket error : %s' % e)

        else:
            self.logger.info('AudioStreamProxy no socket to stop')

        self.logger.info('AudioStreamProxy stop done')



def run_audio_buffer(robot_uid, sock, proc):
    logger = InfoLogger(__name__).get_logger()
    logger.info('[Audio] run_audio_buffer start')

    try:
        while True:
            if proc.poll():
                break

            output = proc.stdout.read(ConfigAudio.buffer_size)

            try:
                select.select([], [sock], [])
            except socket.error:
                logger.info('[Audio] socket shutdown')
                break

            format_data = format_send_data(robot_uid, output)
            sock.sendall(format_data)

            # logger.info('[Audio] send output : %s' % format_data)

    except Exception as e:
        logger.info('[Audio] run_audio_buffer error : %s' % e)

    if not proc.poll():
        proc.terminate()
        # proc.kill()

    logger.info('[Audio] run_audio_buffer exit done')


class AudioBufferProxy(object):
    def __init__(self, robot_uid=None):
        self.logger = InfoLogger(__name__).get_logger()
        self.name = 'AudioBufferProxy'

        self.host = ConfigAudio.host
        self.port = ConfigAudio.port
        self.file_type = ConfigAudio.file_type
        self.rate = ConfigAudio.rate

        self.duration = '3'

        self.robot_uid = robot_uid

        self.sock = None
        self.proc = None

    def start(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, self.port))
            self.logger.info('audio_buffer socket setup done')

            self.sock = sock
            
            command = 'arecord -t {file_type} -r {rate} -d {duration}'.\
                format(file_type = self.file_type, rate = self.rate, \
                    duration = self.duration)

            proc = subprocess.Popen(shlex.split(command), stdout = subprocess.PIPE)

            self.proc = proc

            a_thread = threading.Thread( \
                target = run_audio_buffer, \
                kwargs = {'robot_uid' : self.robot_uid, 'sock' : sock, 'proc' : proc})

            a_thread.start()

            # multiple client read one proc at the same time?

            self.logger.info('%s start done' % self.name)

        except Exception as e:
            self.logger.info('%s.start error : %s' % (self.name, e))

    def stop(self):
        if self.proc:
            try:
                self.proc.terminate()
                # self.proc.kill()
                self.logger.info('%s stop proc done' % self.name)

            except Exception as e:
                self.logger.info('%s stop proc error : %s' % (self.name, e))

        if self.sock:
            try:
                # shutdown will send '' to socket, 
                # writer can cache and exit
                self.sock.shutdown(socket.SHUT_RDWR)

                self.sock.close()
                # self.sock = None
                self.logger.info('%s stop socket done' % self.name)

            except Exception as e:
                self.logger.info('%s stop socket error : %s' % (self.name, e))

        else:
            self.logger.info('%s no socket to stop' % self.name)

        self.logger.info('%s stop done' % self.name)


