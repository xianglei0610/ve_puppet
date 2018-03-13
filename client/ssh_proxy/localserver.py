

import threading

import tornado.web
from tornado.ioloop import IOLoop
from terminado import TermSocket, SingleTermManager, UniqueTermManager

from config import ConfigSSH
from utils.logger import InfoLogger


# class MyTermSocket(TermSocket):
#     def open(self, url_component=None):
#         super(MyTermSocket, self).open(url_component)

#         logger = InfoLogger(__name__).get_logger()
#         logger.info('a term socket is opened')

#     def check_origin(self, origin):  
#         return True  

#     def get(self, *args, **kwargs):
#         # if not self.get_current_user():
#         #     raise web.HTTPError(403)
#         return super(MyTermSocket, self).get(*args, **kwargs)


class WebsocketServer(object):
    def __init__(self):
        self.logger = InfoLogger(__name__).get_logger()
        # self.ioloop = IOLoop()

        self.shell = ConfigSSH.local_ws_shell
        self.port = ConfigSSH.local_ws_port

        self.height = ConfigSSH.height
        self.width = ConfigSSH.width
        self.winheight = ConfigSSH.winheight
        self.winwidth = ConfigSSH.winwidth

        self.max_terminals = ConfigSSH.max_terminals

        self.running = False

    def start(self):
        self.logger.info('Starting websocket server')

        term_settings = {
            'height' : self.height, 
            'width' : self.width,
            'winheight' : self.winheight, 
            "winwidth" : self.winwidth,
        }

        # term_manager = SingleTermManager(shell_command=[self.shell])
        term_manager = UniqueTermManager(shell_command = [self.shell], \
            max_terminals = self.max_terminals, term_settings = term_settings)

        handlers = [
            # (r"/websocket", MyTermSocket, {'term_manager': term_manager}),
            # (r"/websocket", TermSocket, {'term_manager': term_manager}),
            (r"/websocket/([^/]*)", TermSocket, {'term_manager': term_manager}),
        ]

        app = tornado.web.Application(handlers)

        app.listen(self.port)
        self.logger.info('Listen on port ' + str(self.port))
        
        self.running = True
        self.logger.info('Start websocket server done')

        # self.ioloop.current().start()
        IOLoop.current().start()

    def stop(self):
        # self.ioloop.current().stop()
        IOLoop.current().stop()
        self.running = False
        self.logger.info('Stop websocket server done')

    def is_running(self):
        return self.running


# -----------------------------------------
# Run Server utils import from AXMService
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
        self.logger.info('[%s] Run server=%s' % (thread_name, server_name))

        self.server_ins.start()


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

        thread.start()


def _start_websocket():
    websocket_server = WebsocketServer()
    Servers.start_server_thread(websocket_server)


def start_servers():
    _start_websocket()


def stop_servers():
    logger = InfoLogger(__name__).get_logger()

    for server_name, thread in Servers.server_threads.items():
        thread.stop()
        logger.info('Stop server : %s' % server_name)

