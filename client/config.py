

import vision_definitions


class ConfigHost(object):
    host = '192.168.0.30'
    # host = 'api.axmtec.com'


class ConfigPort(object):
    command = 9528
    ssh = 9529
    video = 9531
    audio = 9532
    file = 9533
    media = 1935


class ConfigManager(object):
    pid_file = '/tmp/axmpuppet_client.pid'


class ConfigLogger(object):
    log_path = '/home/nao/log'
    log_file = 'puppet_client.log'


class ConfigSSL(object):
    # enable = False
    certfile = ''
    keyfile = ''


class ConfigServer(object):
    host = ConfigHost.host
    port = ConfigPort.command

    delimiter = '\r\t\n'
    timeout = 3
    reconnect_delta = 5


class ConfigCollector(object):
    handle_delta = 15


class ConfigSSH(object):
    sock_host = ConfigHost.host
    sock_port = ConfigPort.ssh
    delimiter = '\r\t\n'

    local_ws_shell = 'bash'
    local_ws_port = 8090
    local_ws = "ws://localhost:" + str(local_ws_port) + "/websocket"

    # SSH term env
    height = 50
    width = 160
    winheight = 0
    winwidth = 0
    max_terminals = 10


class ConfigVideo(object):
    camera_index = 0

    resolution = vision_definitions.kQQVGA # Image of 160*120
    color_space = vision_definitions.kRGBColorSpace

    # resolution_luma = vision_definitions.kVGA # Image of 640*480px
    resolution_luma = vision_definitions.kQVGA # Image of 320*240px
    color_space_luma = vision_definitions.kYuvColorSpace
    fps = 10

    page = 6
    delimiter = '\r\n'

    host = ConfigHost.host
    port = ConfigPort.video


class ConfigAudio(object):
    host = ConfigHost.host
    port = ConfigPort.audio

    delimiter = '\r\n'

    file_type = 'wav'
    rate = 16000
    buffer_size = 256


class ConfigFile(object):
    local_path = '/tmp/new.pkg'

    pkg_path = '/tmp/new_cloud.pkg'
    pkg_dl_path = '/puppet/file/package'
    pkg_dl_url = 'http://' + ConfigHost.host + ':' + str(ConfigPort.file) + pkg_dl_path
    # pkg_dl_url = 'http://192.168.124.78:9533/puppet/file/package'


class ConfigMedia(object):
    """
    color_space : vision_definitions.kRGBColorSpace 
    -> pix_fmt : 'rgb24'

    color_space : vision_definitions.kYUV422ColorSpace 
    -> pix_fmt : 'yuyv422'
    """
    camera_index = 0
    resolution = vision_definitions.kVGA # Image of 640*480
    color_space = vision_definitions.kYUV422ColorSpace 
    fps = 30

    host = ConfigHost.host
    port = ConfigPort.media
    path = '/live/'

    a_format = 'wav'       # Related to both arecord and ffmpeg audio input
    analyze_duration = '0' # Set to 0 to decrease delay

    v_format = 'rawvideo'  # Single frame input
    # v_rate = '18'          # Video frame rate <-- No rate force input, would cost delay
    pix_fmt = 'yuyv422'      # Follow the color_space
    v_resolution = '640*480' # Follow the resolution

    audio_codec = 'aac'    # ffmpeg audio output encode 
    audio_bitrate = '160k' # ffmpeg audio output bitrate
    strict_lvl = '2'

    video_bitrate = '1200k' # ffmpeg video output bitrate

    output_format = 'flv'   # ffmpeg media stream output format

