

import argparse
import errno
import os
import signal

from config import ConfigManager
from libs.client import Client
from ssh_proxy.localserver import start_servers, stop_servers
from utils.logger import InfoLogger


parser = argparse.ArgumentParser()
parser.add_argument('--run', action = 'store_true', help = 'run client')
parser.add_argument('--restart', action = 'store_true', help = 'restart client')
parser.add_argument('--stop', action = 'store_true', help = 'stop client')
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


if args.run:
    logger = InfoLogger(__name__).get_logger()
    start_servers()

    pid = os.getpid()

    manager = Manager()
    result = manager.kill_process()
    logger.info('Stop clients : %s' % result)
    
    manager.set_pid(pid)
    
    client = Client()
    client.connect()

elif args.restart:
    logger = InfoLogger(__name__).get_logger()

    stop_servers()
    logger.info('Stop servers done')

    manager = Manager()
    result = manager.kill_process()
    logger.info('Stop clients : %s' % result)

    start_servers()

    pid = os.getpid()
    manager.set_pid(pid)

    client = Client()
    client.connect()

elif args.stop:
    logger = InfoLogger(__name__).get_logger()

    stop_servers()
    logger.info('Stop servers done')

    manager = Manager()
    result = manager.kill_process()
    logger.info('Stop clients : %s' % result)

