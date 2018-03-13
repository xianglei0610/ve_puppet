

import os
import shlex
import subprocess
import threading
import time
from collections import OrderedDict

import ffmpy

from config import ConfigMedia
from utils.logger import InfoLogger


class BasePipe(object):
    def __init__(self):
        self.pipe_r, self.pipe_w = os.pipe()
        self.closed = False

    def write(self, data):
        os.write(self.pipe_w, data)

    def read(self):
        return os.read(self.pipe_r)

    def get_read_pipe(self):
        return self.pipe_r

    def get_write_pipe(self):
        return self.pipe_w

    def close(self):
        os.close(self.pipe_r)
        os.close(self.pipe_w)
        self.closed = True

    def is_closed(self):
        return self.closed


class ImagePipe(BasePipe):
    def __init__(self):
        super(ImagePipe, self).__init__()


class AudioPipe(BasePipe):
    def __init__(self):
        super(AudioPipe, self).__init__()


# -----------------------------------------------------------------------------

def run_video_feed(func, handle, image_pipe):
    logger = InfoLogger(__name__).get_logger()
    logger.info('[Media] run_video_feed start')

    try:
        while not image_pipe.is_closed():
            image_container = func(handle)
            image_pipe.write(image_container[6])

    except Exception as e:
        logger.info('[Media] run_video_feed error : %s' % e)

    logger.info('[Media] run_video_feed exit done')


def run_audio_feed(proc, audio_pipe):
    logger = InfoLogger(__name__).get_logger()
    logger.info('[Media] run_audio_feed start')

    try:
        while not audio_pipe.is_closed():
            # audio_pipe.write(proc.stdout.read(80))
            audio_pipe.write(proc.stdout.readline())

    except Exception as e:
        logger.info('[Media] run_audio_feed error : %s' % e)

    logger.info('[Media] run_audio_feed exit done')


def run_media_stream(robot_uid, ff_obj):
    logger = InfoLogger(__name__).get_logger()
    logger.info('[Media] run_media_stream start')

    try:
        ff_obj.run()

    except Exception as e:
        logger.info('[Media] run_media_stream error : %s' % e)

    logger.info('[Media] run_media_stream exit done')


# -----------------------------------------------------------------------------

class MediaStreamProxy(object):
    def __init__(self, robot_uid):
        self.logger = InfoLogger(__name__).get_logger()

        self.robot_uid = robot_uid

        self.host = ConfigMedia.host
        self.port = ConfigMedia.port
        self.path = ConfigMedia.path

        self.a_format = ConfigMedia.a_format
        self.analyze_duration = ConfigMedia.analyze_duration

        self.v_format = ConfigMedia.v_format
        self.pix_fmt = ConfigMedia.pix_fmt
        self.v_resolution = ConfigMedia.v_resolution

        self.audio_codec = ConfigMedia.audio_codec
        self.audio_bitrate = ConfigMedia.audio_bitrate
        self.strict_lvl = ConfigMedia.strict_lvl

        self.video_bitrate = ConfigMedia.video_bitrate
        self.output_format = ConfigMedia.output_format

        self.a_proc = None
        self.v_thread = None
        self.a_thread = None

        self.ff = None
        self.m_thread = None

        self.image_pipe = None
        self.audio_pipe = None

    def start(self, func, handle, bit_dict=None):
        try:
            self.image_pipe = ImagePipe()
            self.audio_pipe = AudioPipe()

            # Video thread
            self.v_thread = threading.Thread( \
                target = run_video_feed,      \
                kwargs = {'func' : func, 'handle' : handle, 
                          'image_pipe' : self.image_pipe})

            # Pipe for media stream
            audio_pipe_r = self.audio_pipe.get_read_pipe()
            image_pipe_r = self.image_pipe.get_read_pipe()

            audio_input = 'pipe:%s' % str(audio_pipe_r)
            image_input = 'pipe:%s' % str(image_pipe_r)

            # Cover bitrate config from args
            if bit_dict:
                self.audio_bitrate = bit_dict.get('audio_bitrate')
                self.video_bitrate = bit_dict.get('video_bitrate')

            # -re (input) : Read input at native frame rate. 
            # Set analyzeduration to 0 for audio to disable analyze delay
            audio_args = '-f {f} -analyzeduration {ad} -re'.format(
                f = self.a_format, ad = self.analyze_duration)

            image_args = '-f {f} -pix_fmt {pf} -s:v {sv} -re'.format(
                f = self.v_format, pf = self.pix_fmt, sv = self.v_resolution)

            # For dev
            # receiver = '/tmp/test.flv'
            # if os.path.exists(receiver):
            #     os.unlink(receiver)
            receiver = 'rtmp://' + self.host + ':' + str(self.port) + \
                self.path + str(self.robot_uid)

            # -c:a : audio codec, must be set in output
            # -b:a : audio bitrate
            # -b:v : video bitrate
            # output total bitrate = (video bitrate + audio bitrate)kbits/s
            # -muxdelay seconds   : Set the maximum demux-decode delay.
            # -muxpreload seconds : Set the initial demux-decode delay.
            receiver_args = """-map 0 -c:a {ca} -strict -{s} -b:a {ba}
                               -map 1 -b:v {bv} 
                               -f {f} -muxdelay 0.1 -muxpreload 0""".\
                format(ca = self.audio_codec, s = self.strict_lvl, 
                       ba = self.audio_bitrate, bv = self.video_bitrate,
                       f = self.output_format)

            ff_input = OrderedDict(
                [ (audio_input, audio_args), (image_input, image_args), ]
            )
            ff_output = {receiver : receiver_args,}

            self.ff = ffmpy.FFmpeg(inputs = ff_input, outputs = ff_output)
            self.logger.info('[MediaStreamProxy] ff.cmd : %s' % self.ff.cmd)

            self.m_thread = threading.Thread( \
                target = run_media_stream, \
                kwargs = {'robot_uid' : self.robot_uid, 'ff_obj' : self.ff})

            # Audio related
            # Do not use stdout=PIPE or stderr=PIPE with this function as 
            # that can deadlock based on the child process output volume.
            # Use Popen with the communicate() method when you need pipes.
            a_command = 'arecord -f cd -t {a_format}'.format(a_format = self.a_format)
            self.a_proc = subprocess.Popen(shlex.split(a_command), \
                stdout = self.audio_pipe.get_write_pipe())

            self.m_thread.start()
            self.v_thread.start()

            self.logger.info('[MediaStreamProxy] start done')

        except Exception as e:
            self.logger.info('[MediaStreamProxy] start error : %s' % e)

    def stop(self):
        try:
            # Close working pipes
            if self.image_pipe:
                self.image_pipe.close()
                self.logger.info('[MediaStreamProxy] close image_pipe done')

            if self.audio_pipe:
                self.audio_pipe.close()
                self.logger.info('[MediaStreamProxy] close audio_pipe done')

            # Stop audio process
            if self.a_proc:
                self.a_proc.terminate()
                # self.a_proc.kill()

                # Use wait() to terminate the defunct process
                self.a_proc.wait()
                self.logger.info('[MediaStreamProxy] stop audio proc done')

            # Stop ffmpeg process
            if self.ff:
                self.ff.process.terminate()
                # self.ff.process.kill()
                self.logger.info('[MediaStreamProxy] stop ffmpeg proc done')

        except Exception as e:
            self.logger.info('[MediaStreamProxy] stop error : %s' % e)

        self.logger.info('[MediaStreamProxy] stop done')
