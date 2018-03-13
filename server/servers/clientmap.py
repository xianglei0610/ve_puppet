


# import rx
from utils.logger import InfoLogger


class ConnectionMap(object):
    # Clients connecting to TCPServer
    # {
    #     'robot_body_id' : socket_connection_obj,
    # }
    clients = dict()

    # Store client info, write to websocket while broswer open
    # {
    #     'robot_body_id' : {}, # robot collector info    
    # }
    client_status = dict()

    # Store websocket connection from broswer
    # {
    #     'uuid' : websocket_obj,
    # }
    ws_conn = dict()

    # Store the socket connection
    sock_conn = None

    # ------------------------------------------------
    # For video

    # Store websocket connection from broswer for video
    # {
    #     'robot_uid' : {
    #         'ws_uid' : websocket_obj, 
    #     }
    # }
    video_ws_conn = dict()

    # Store robot is running video
    # {
    #     'robot_uid' : True,
    # }
    video_running = dict()

    # ------------------------------------------------
    # For audio

    # Store websocket connection from broswer for audio
    # {
    #     'robot_uid' : {
    #         'ws_uid' : websocket_obj, 
    #     }
    # }
    audio_ws_conn = dict()

    # Store robot is running audio
    # {
    #     'robot_uid' : True,
    # }
    audio_running = dict()

    # ------------------------------------------------
    # For sshserver

    # sock_pairs : {
    #     'robot_uid' : {
    #         'term_id_1' : broswer_sock_1,
    #         'term_id_2' : broswer_sock_2,
    #     },
    # }
    sock_pairs = {}

    # For sshserver
    # ws_pairs : {
    #     'robot_uid' : {
    #         'term_id_1' : broswer_websocket_1,
    #         'term_id_2' : broswer_websocket_2,
    #     },
    # }
    ws_pairs = {}

    # pairs : {
    #     'robot_uid' : {
    #         'term_id_1' : {'socket' : broswer_sock_1, 'websocket' : broswer_ws_1},
    #         'term_id_2' : {'socket' : broswer_sock_2, 'websocket' : broswer_ws_2},
    #     },
    # }

    # ------------------------------------------------

    # client_map = {
    #     'uid1' : {
    #         'client' : <object>,
    #         'tags' : ['boy', 'tall'],
    #         'groups' : ['airport'],
    #         'permissions' : [],
    #     },
    # }

    # tags_dict = {
    #     'boy' : set('uid1', 'uid2'),
    #     'girl' : set('uid3', 'uid4'),
    #     'tall' : set('uid1'),
    # }

    # groups_dict = {
    #     'airport' : set('uid1', 'uid2'),
    #     'bank' : set('uid3', 'uid4'),
    # }


class ClientManager(object):
    logger = InfoLogger("ClientManager").get_logger()

    @classmethod
    def clean_defunct_client(cls):
        for uid,iostream_obj in ConnectionMap.clients.items():

            cls.logger.info('Cleanning %s' % uid)
            cls.logger.info('closed %s' % str(iostream_obj._stream.closed()))

            if iostream_obj._stream.closed():
                cls.logger.info('%s is shutdown, clean' % uid)

                if ConnectionMap.clients.has_key(uid):
                    cls.logger.info('ConnectionMap clients pop: %s' % uid)
                    ConnectionMap.clients.pop(uid)

                if ConnectionMap.client_status.has_key(uid):
                    cls.logger.info('ConnectionMap client_status pop: %s' % uid)
                    ConnectionMap.client_status.pop(uid)

        for conn in ConnectionMap.ws_conn.values():
            conn.refresh_client_status()







class ConnectionManager(object):
    clients = {}

    @classmethod
    def set_client(cls, key, val):
        return

    @classmethod
    def get_client(cls, key):
        return


class SocketClient(ConnectionManager):
    # Clients connecting to TCPServer
    # {
    #     'robot_body_id' : socket_connection_obj,
    # }
    # clients = dict()

    # Store client info, write to websocket while broswer open
    # {
    #     'robot_body_id' : {}, # robot collector info    
    # }
    client_status = {}

    # Store the socket connection
    sock_conn = None

    @classmethod
    def set_clients_status(cls, key, status):
        return

    @classmethod
    def get_clients_status(cls, key):
        return



class WSClient(ConnectionManager):
    # Store websocket connection from broswer
    # {
    #     'uuid' : websocket_obj,
    # }
    ws_conn = dict()

    # Store websocket connection from broswer for video
    # {
    #     'robot_uid' : {
    #         'ws_uid' : websocket_obj, 
    #     }
    # }
    video_ws_conn = dict()

    # Store websocket connection from broswer for audio
    # {
    #     'robot_uid' : {
    #         'ws_uid' : websocket_obj, 
    #     }
    # }
    audio_ws_conn = dict()



class VideoClient(ConnectionManager):
    # Store robot is running video
    # {
    #     'robot_uid' : True,
    # }
    video_running = dict()



class AudioClient(ConnectionManager):
    # Store robot is running audio
    # {
    #     'robot_uid' : True,
    # }
    audio_running = dict()



class SSHConnections(object):
    # For sshserver

    # sock_pairs : {
    #     'robot_uid' : {
    #         'term_id_1' : broswer_sock_1,
    #         'term_id_2' : broswer_sock_2,
    #     },
    # }
    sock_pairs = {}

    # For sshserver
    # ws_pairs : {
    #     'robot_uid' : {
    #         'term_id_1' : broswer_websocket_1,
    #         'term_id_2' : broswer_websocket_2,
    #     },
    # }
    ws_pairs = {}

    # pairs : {
    #     'robot_uid' : {
    #         'term_id_1' : {'socket' : broswer_sock_1, 'websocket' : broswer_ws_1},
    #         'term_id_2' : {'socket' : broswer_sock_2, 'websocket' : broswer_ws_2},
    #     },
    # }

