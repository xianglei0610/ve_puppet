

import argparse
import errno
import os
import signal
import threading
import time

from tornado.ioloop import IOLoop

from config import ConfigManager
from servers.audioserver import AudioServer
from servers.fileserver import FileServer
from servers.videoserver import VideoServer
from servers.sshserver import SSHSocketServer
from servers.tcpserver import PuppetServer
from servers.wsserver import PuppetWebSocketServer
from utils.logger import InfoLogger


parser = argparse.ArgumentParser()
parser.add_argument('--run', action = 'store_true', help = 'run server')
parser.add_argument('--restart', action = 'store_true', help = 'restart server')
parser.add_argument('--stop', action = 'store_true', help = 'stop server')
args = parser.parse_args()


class Manager(object):
    def __init__(self):
        self.pid_file = ConfigManager.pid_file
        self.logger = InfoLogger(__name__).get_logger()

    def set_pid(self, pid):
        with open(self.pid_file, 'a') as f:
            f.write(str(pid) + '\n')

    def get_pid(self):
        if not os.path.exists(self.pid_file):
            return []

        pids = [int(pid.rstrip('\n')) for pid in open(self.pid_file, 'r').readlines()]
        return pids

    def kill_process(self, pid=None):
        if pid:
            pids = [pid]
        else:
            pids = self.get_pid()

        try:
            for pid in pids:
                self.logger.info("Stopping pid %s" % pid)

                try:
                    os.kill(pid, signal.SIGTERM)

                except OSError, err:
                    if err.errno == errno.ESRCH:
                        self.logger.info("pid %s not running" % pid)
                        continue

                self.logger.info("Stop pid %s done" % pid)

            # clear file 
            with open(self.pid_file, 'w') as f:
                f.write('')

            return "Done"

        except OSError, err:
            # if err.errno == errno.ESRCH:
            #     return "Not running"
            if err.errno == errno.EPERM:
                return "No permission to signal this process!"
            else:
                return "Unknown error"


# -----------------------------------------
# Server utils import from AXMService
# -----------------------------------------

class ServerThread(threading.Thread):
    def __init__(self, server_ins):
        super(ServerThread, self).__init__()
        self.server_ins = server_ins
        self._stop = threading.Event()

        self.logger = InfoLogger(__name__).get_logger()

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def run(self):
        thread_name = threading.currentThread().getName()
        server_name = self.server_ins.__class__.__name__
        self.logger.info('[%s] Run server = %s' % (thread_name, server_name))

        try:
            self.server_ins.start()

        except Exception as e:
            self.logger.info('ServerThread run error : %s' % e)


class Servers(object):
    server_threads = {}

    @classmethod
    def start_server_thread(cls, server_ins):
        ins_name = server_ins.__class__.__name__

        if ins_name in cls.server_threads:
            return

        thread = ServerThread(server_ins)

        thread.setName('Thread-%s' % ins_name)
        cls.server_threads[ins_name] = thread

        logger = InfoLogger(__name__).get_logger()
        logger.info('server_threads count : %d' % len(cls.server_threads)) 

        thread.start()


# -----------------------------------------
# Start server func
# -----------------------------------------

def _start_sshsocket():
    socket_server = SSHSocketServer()
    Servers.start_server_thread(socket_server)


def _start_tcpserver():
    tcp_server = PuppetServer()
    Servers.start_server_thread(tcp_server)


def _start_wsserver():
    ws_server = PuppetWebSocketServer()
    Servers.start_server_thread(ws_server)


def _start_videoserver():
    v_server = VideoServer()
    Servers.start_server_thread(v_server)


def _start_audioserver():
    a_server = AudioServer()
    Servers.start_server_thread(a_server)


def _start_fileserver():
    f_server = FileServer()
    Servers.start_server_thread(f_server)


def start_servers():
    _start_tcpserver()
    _start_wsserver()
    _start_sshsocket()
    _start_videoserver()
    _start_audioserver()
    _start_fileserver()


def stop_servers():
    logger = InfoLogger(__name__).get_logger()
    # logger.info('Servers to stop: %d' % len(Servers.server_threads))

    for ins_name, thread in Servers.server_threads.iteritems():
        thread.stop()
        logger.info('Stop server : %s' % ins_name)


# -----------------------------------------
# Get args from shell
# -----------------------------------------

if args.run:
    logger = InfoLogger(__name__).get_logger()
    logger.info('Start running Puppet servers')

    pid = os.getpid()

    manager = Manager()
    manager.set_pid(pid)

    start_servers()

elif args.restart:
    logger = InfoLogger(__name__).get_logger()
    logger.info('Restart running Puppet servers')

    logger.info('Stopping Puppet servers')

    stop_servers()

    manager = Manager()
    manager.kill_process()
    logger.info('Puppet servers stopped')
    
    time.sleep(1)

    pid = os.getpid()
    manager.set_pid(pid)

    logger.info('Start running Puppet servers')
    start_servers()

elif args.stop:
    logger = InfoLogger(__name__).get_logger()
    logger.info('Stopping puppet servers')

    stop_servers()

    manager = Manager()
    manager.kill_process()

    logger.info('Puppet servers stopped')

