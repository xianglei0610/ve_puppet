

import errno # available > Python 2.6
import json
import socket
import threading
import time

from config import ConfigCollector, ConfigServer
from libs.assistant import Collector, Executor
from utils.logger import InfoLogger


class Client(object):
    def __init__(self):
        self.server_host = ConfigServer.host
        self.server_port = ConfigServer.port
        self.delimiter = ConfigServer.delimiter
        self.timeout = ConfigServer.timeout
        self.reconnect_delta = ConfigServer.reconnect_delta

        self.collector_handle_delta = ConfigCollector.handle_delta

        self.logger = InfoLogger(__name__).get_logger()

        self.thread_stop = False

        self.collector = Collector()
        self.executor = Executor()

    def connect(self):
        self.logger.info('start connect')

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)

        try:
            sock.connect((self.server_host, self.server_port))

            self.logger.info('connect success')

            self.setup_threads(sock)

        except KeyboardInterrupt:
            self.logger.info('Got Ctrl+C, exiting...')
            self.stop_all_thread()
            self.disconnect(sock)

        except socket.timeout:
            self.logger.info('socket connect timeout, reconnect')
            self.reconnect()

        except socket.error as s_error:
            # [Errno 111] Connection refused: client is starting, server is down
            # [Errno 32] Broken pipe: client is running, server is down
            if s_error.errno in (errno.ECONNREFUSED, errno.EPIPE):
                self.logger.info('socket connect error, try to reconnect')
                self.logger.info(str(s_error))
                self.reconnect()
            else:
                raise

        except Exception as e:
            self.logger.info('Client connect error: %s' % e)

    def disconnect(self, sock):
        try:
            sock.close()
            self.logger.info('disconnect done')
        except:
            # sock is not available
            pass

    def reconnect(self):
        try:
            self.logger.info('try to reconnect socket')

            self.stop_all_thread()
            time.sleep(self.reconnect_delta)

            self.connect()

        except Exception as e:
            self.logger.info('Client reconnect error: %s' % e)

    def setup_threads(self, sock):
        try:
            self.logger.info('Setup new threads')
            self.thread_stop = False

            collector_thread = threading.Thread( \
                target = self.run_collector_thread, \
                kwargs = {'sock' : sock, 'stop' : lambda: self.thread_stop})

            executor_thread = threading.Thread( \
                target = self.run_executor_thread, \
                kwargs = {'sock' : sock, 'stop' : lambda: self.thread_stop})

            collector_thread.daemon = False
            executor_thread.daemon = False

            collector_thread.start()
            executor_thread.start()

            while collector_thread.isAlive() or executor_thread.isAlive():
                collector_thread.join(10)
                executor_thread.join(10)

        except Exception as e:
            self.logger.info('setup_threads error: %s' % e)

    def stop_all_thread(self):
        self.thread_stop = True

    def run_collector_thread(self, sock, stop):
        try:
            while 1:
                data = self.collect_data()
                sock.sendall(data)

                time.sleep(self.collector_handle_delta)

                if stop():
                    self.logger.info('collector stopped')
                    break

        except socket.error as s_error:
            if s_error.errno == errno.EPIPE:
                self.logger.info('collector get broken pipe, stopped, try to reconnect')
                self.reconnect()

            elif s_error.errno == errno.ETIMEDOUT:
                self.logger.info('collector socket connect timeout, try to reconnect')
                self.reconnect()

            else:
                self.logger.info('run_collector_thread error: %s' % s_error)
                raise

        except Exception as e:
            self.logger.info('run_collector_thread error: %s' % e)

    def run_executor_thread(self, sock, stop):
        try:
            while 1:
                try:
                    data = sock.recv(1024)

                except socket.timeout:
                    if stop():
                        self.logger.info('executor stopped')
                        break
                    else:
                        continue

                self.logger.info('Receive data : %r' % data)

                if data:
                    res = self.executor.command_explain(data)

                    if res:
                        res_format = self.format_data(res)
                        sock.sendall(res_format)

                else:
                    # Server stopped, received an empty string 
                    self.logger.info('executor receive empty data from server, stopped')
                    break

        except Exception as e:
            self.logger.info('run_executor_thread error: %s' % e)

    def collect_data(self):
        try:
            data = self.format_data(self.collector.combine_robot_info())
            
        except Exception as e:
            self.logger.info('collect_data error: %s' % e)
            data = ''

        return data

    def format_data(self, data):
        return str(data) + self.delimiter
