

class ConfigPort(object):
    command = 9528
    ssh = 9529
    websocket = 9530
    video = 9531
    audio = 9532
    file = 9533


class ConfigManager(object):
    pid_file = '/tmp/axmpuppet_server.pid'
    

class ConfigLogger(object):
    log_path = '/Users/xll/Downloads/All_In_One_From_Garvey/ve_axm_puppet/server'
    log_file = 'puppet_server.log'


class ConfigSSL(object):
    enable = False
    certfile = ''
    keyfile = ''


class ConfigServer(object):
    port = ConfigPort.command
    delimiter = '\r\t\n'


class ConfigSSH(object):
    sock_host = 'localhost'
    sock_port = ConfigPort.ssh
    
    delimiter = '\r\t\n'


class ConfigWebSocket(object):
    host = '0.0.0.0'
    port = ConfigPort.websocket


class ConfigVideo(object):
    port = ConfigPort.video

    delimiter = '\r\n'
    page = 6


class ConfigAudio(object):
    port = ConfigPort.audio
    delimiter = '\r\n'


class ConfigFile(object):
    port = ConfigPort.file
    # delimiter = '\r\n'

    private_key = 'keys/puppet.pvt'
    path = '/tmp'
    pkg_pattern = '{f_name}_{md5}_{ts}.pkg'

