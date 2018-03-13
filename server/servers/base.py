

import uuid

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.tcpserver import TCPServer
from tornado.web import Application, RequestHandler
from tornado.websocket import WebSocketHandler

from config import ConfigSSL
from utils.logger import InfoLogger


class BaseConnection(object):
    def __init__(self, stream, address, delimiter):
        self.logger = InfoLogger(__name__).get_logger()
        self.name = self.__class__.__name__

        self.delimiter = delimiter

        self._stream = stream
        self._address = address

        self._stream.set_close_callback(self.on_close)
        self.read_message()

    def read_message(self):
        # self.logger.info("In read_message, %r" % self.delimiter)
        self._stream.read_until(self.delimiter, self.on_message_read)

    def on_message_read(self, data):
        pass

    # def send_to_ws(self, data, robot_uid):
    #     """Send to broswer through websocket"""
    #     pass

    def on_close(self):
        self.logger.info('[%s] client close: %s' % (self.name, str(self._address)))


class BaseTCPServer(TCPServer):
    def __init__(self, port, connection):
        super(BaseTCPServer, self).__init__()

        self.name = self.__class__.__name__
        self.logger = InfoLogger(self.name).get_logger()

        self.port = port
        self.connection = connection

    def handle_stream(self, stream, address):
        self.logger.info("[%s] new connection: %s %s" % (self.name, address, stream))
        self.connection(stream, address)

    def start(self):
        try:
            self.logger.info("[%s] starting at port %s" % (self.name, self.port))

            self.listen(self.port)
            self.logger.info("[%s] socket setup done" % self.name)

            ioloop = IOLoop()
            ioloop.current().start()

        except Exception as e:
            self.logger.info("[%s] start error: %s" % (self.name, e))


class BaseWebSocketHandler(WebSocketHandler):
    def check_origin(self, origin):
        return True

    def set_init_attr(self, uid=None):
        self.logger = InfoLogger(__name__).get_logger()
        self.uid = uid or uuid.uuid4().hex


class BaseHTTPServer(object):
    def __init__(self, port):
        self.name = self.__class__.__name__
        self.logger = InfoLogger(self.name).get_logger()

        self.port = port

    def set_app(self, app_tup_lst):
        app = Application(app_tup_lst)
        self.logger.info("[%s] app setup done" % self.name)
        return app

    def set_server(self, app):
        server = HTTPServer(app)

        if ConfigSSL.enable:
            server = HTTPServer(app, 
                ssl_options = {
                    "certfile" : ConfigSSL.certfile,
                    "keyfile" : ConfigSSL.keyfile,
                }
            )
        else:
            server = HTTPServer(app)

        server.listen(self.port)
        return server

    def start(self, app_tup_lst):
        try:
            app = self.set_app(app_tup_lst)
            server = self.set_server(app)

            self.logger.info("[%s] listen at port: %s" % (self.name, str(self.port)))

            ioloop = IOLoop()
            ioloop.current().start()

        except Exception as e:
            self.logger.info("[%s] start error: %s" % (self.name, e))


class BaseFileHandler(RequestHandler):
    def initialize(self):
        self.name = self.__class__.__name__
        self.logger = InfoLogger(self.name).get_logger()

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        # self.set_header("Access-Control-Allow-Credentials", "true")
        # self.set_header("Access-Control-Allow-Headers", "Content-Type")
        # self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    # def options(self):
    #     self.set_status(204)
    #     self.finish()
