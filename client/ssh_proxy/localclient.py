

import json
import select
import socket
import threading
import time

from tornado import gen 
from tornado.websocket import websocket_connect
from tornado.ioloop import IOLoop

from config import ConfigSSH
from utils.logger import InfoLogger


def format_sock_msg(uid, term_id, msg=None):
    dct = {
        'uid' : uid,
        'term_id' : term_id,
        'msg' : msg,
    }
    return json.dumps(dct) + ConfigSSH.delimiter


@gen.coroutine
def run_read_client(sock, ws_connect, robot_uid, term_id):
    logger = InfoLogger(__name__).get_logger()
    logger.info('[reader] start')

    ws = yield ws_connect

    pairs = SocketMap.pairs.get(term_id, None)
    if pairs:
        pairs['websocket'] = ws
        SocketMap.pairs[term_id] = pairs

    while True:
        try:
            msg = yield ws.read_message()
            # logger.info('[reader] ws.read_message : %r' % msg)

            # ws server may return None after UnicodeDecodeError raised
            # if msg is None:
            #     break

            if msg:
                # make sure the socket is not closed
                try:
                    select.select([], [sock], [])
                except socket.error:
                    logger.info('[reader] socket shutdown')
                    break

                sock_msg = format_sock_msg(robot_uid, term_id, msg)
                sock.sendall(sock_msg)

                # logger.info('[reader] send to sock : %r' % sock_msg)
            else:
                logger.info('[reader] read no msg from ws : %r' % msg)
                break

        except Exception as e:
            logger.info('[reader] error: %s' % e)
            # break
            continue

    logger.info('[reader] exit done')


@gen.coroutine
def run_write_client(sock, ws_connect):
    logger = InfoLogger(__name__).get_logger()
    logger.info('[writer] start')

    ws = yield ws_connect

    while True:
        try:
            recv_sock = sock.recv(1024)
            # logger.info('[writer] recv_sock : %r' % recv_sock)

            if recv_sock:
                msg_list = recv_sock.split(ConfigSSH.delimiter)

                for msg_str in msg_list:
                    # msg_str may be '', if json loads failed, continue to next one
                    try:
                        msg_dict = json.loads(msg_str)
                    except:
                        continue

                    msg = msg_dict.get('msg', None)

                    if msg:
                        # yield ws.write_message(msg)
                        ws.write_message(msg)
                        # logger.info('[writer] write to ws : %r' % msg)
                    else:
                        logger.info('[writer] read no msg from sock : %r' % msg)

            else:
                # sock.shutdown(socket.SHUT_RDWR) is called
                logger.info('[writer] socket shutdown')

                # send to ws, let run_read_client know and exit
                ws.write_message(r'["stdin", "\r"]')

                break

        except Exception as e:
            logger.info('[writer] error: %s' % e)
            break

    logger.info('[writer] exit done')


def start_read_client(sock, ws_connect, robot_uid, term_id):
    ioloop = IOLoop()
    ioloop.current().run_sync(\
        lambda: run_read_client(sock, ws_connect, robot_uid, term_id))
    # ioloop.clear_instance()


def start_write_client(sock, ws_connect):
    ioloop = IOLoop()
    ioloop.current().run_sync(lambda: run_write_client(sock, ws_connect))
    # ioloop.clear_instance()


class SocketMap(object):
    # pairs = {
    #     'term_id_1' : {'socket' : sock_1, 'websocket' : ws_1},
    #     'term_id_2' : {'socket' : sock_2, 'websocket' : ws_2},
    # }
    pairs = {}


class ClientProxy(object):
    def __init__(self, robot_uid):
        self.logger = InfoLogger(__name__).get_logger()

        self.robot_uid = robot_uid
        self.running = False

    def start(self, term_id):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ConfigSSH.sock_host, ConfigSSH.sock_port))

            SocketMap.pairs.setdefault(term_id, {'socket' : sock, 'websocket' : None})
            self.logger.info('socket connect done')

            # socket init send, let cloud server know where the client comes from
            sock_init = format_sock_msg(self.robot_uid, term_id)
            sock.sendall(sock_init)

            # create ws connect here to make sure only a term socket is opened
            ws_connect = websocket_connect(ConfigSSH.local_ws + '/' + term_id)

            write_thread = threading.Thread( \
                target = start_write_client, \
                kwargs = {'sock' : sock, 'ws_connect' : ws_connect})

            read_thread = threading.Thread( \
                target = start_read_client, \
                kwargs = {'sock' : sock, 'ws_connect' : ws_connect,\
                          'robot_uid' : self.robot_uid, 'term_id' : term_id})

            self.logger.info('read/write thread setup done')

            write_thread.start()
            read_thread.start()

            self.running = True
            self.logger.info('ClientProxy start done')

        except Exception as e:
            self.logger.info('ClientProxy.start error : %s' % e)

    def stop(self, term_id):
        sock = SocketMap.pairs.get(term_id, {}).get('socket', None)

        if sock:
            try:
                # shutdown will send '' to socket, 
                # writer can cache and exit
                sock.shutdown(socket.SHUT_RDWR)

                sock.close()
                self.logger.info('stop socket done')

            except Exception as e:
                self.logger.info('stop socket error : %s' % e)

        else:
            self.logger.info('no socket to stop')

        ws = SocketMap.pairs.get(term_id, {}).get('websocket', None)

        if ws:
            ws.close()

        self.running = False
        self.logger.info('ClientProxy stop done')

    def is_running(self):
        return self.running

    def restart(self, term_id):
        self.stop(term_id)
        time.sleep(1)
        self.start(term_id)
