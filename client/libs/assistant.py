

import base64
import hashlib
import inspect
import json
import os
import time
import uuid

import qi
import requests

from config import ConfigVideo, ConfigFile, ConfigMedia
from libs.videofeed import VideoFeedProxy
from libs.audiostream import AudioStreamProxy
from libs.mediastream import MediaStreamProxy
from serializers.serializer import CollectorSerializer, ExecutorSerializer, \
                                   RaiserSerializer
from ssh_proxy.localserver import start_servers, WebsocketServer
from ssh_proxy.localclient import ClientProxy
from utils.decorator import need_to_handle
from utils.logger import InfoLogger


class QiSession(object):
    session = None
    logger = InfoLogger('QiSession').get_logger()

    service_dct = {
        'ALAudioDevice' : None,
        'ALBasicAwareness' : None,
        'ALBattery' : None,
        'ALBehaviorManager' : None,
        'ALConnectionManager' : None,
        'ALMemory' : None,
        'ALMotion' : None,
        'ALSystem' : None,
        'ALTextToSpeech' : None,
        'ALVideoDevice' : None,
        'PackageManager' : None,
    }
    
    @classmethod
    def log(cls, msg):
        cls.logger.info(msg)

    @classmethod
    def get_session(cls, qi_path):
        if not cls.session or not cls.session.isConnected():
            cls.log('QiSession is setting up new session')

            try:
                try:
                    # If no session is connecting, start an session
                    app = qi.Application(url = qi_path)
                    app.start()
                    s = app.session

                except:
                    # Another session is connecting(maybe AXMService), connect directly
                    s = qi.Session()
                    s.connect(qi_path)

                cls.session = s

            except Exception as e:
                cls.log('QiSession get_session error : %s' % e)

        return cls.session

    @classmethod
    def get_session_service(cls, qi_path):
        if None in cls.service_dct.values():
            s = cls.get_session(qi_path)

            for k,v in cls.service_dct.items():
                cls.service_dct[k] = s.service(k)

        return cls.service_dct


class QiAssistant(object):
    def __init__(self, ip='127.0.0.1', port=9559):
        self.qi_ip = ip
        self.qi_port = port
        self.full_path = 'tcp://%s:%s' % (self.qi_ip, self.qi_port)
        self.session = None

        self.logger = InfoLogger(__name__).get_logger()

        self.set_session()
        self.setup_qi_services()

    def set_session(self):
        self.session = QiSession.get_session(self.full_path)

    def setup_qi_services(self):
        service_dct = QiSession.get_session_service(self.full_path)

        for s_key,s_val in service_dct.items():
            setattr(self, s_key, s_val)

    def text_to_speech(self, text):
        self.ALTextToSpeech.say(text)


class Collector(QiAssistant):
    robot_id = None

    def __init__(self):
        super(Collector, self).__init__()

        self.set_robot_id()

    def combine_robot_info(self):
        dct = {}
        dct_string = ''

        try:
            for f_name, func in inspect.getmembers(self, predicate = inspect.ismethod):
                if func.__name__ == 'msg_handler':
                    dct.update(func())

            collector_szer = CollectorSerializer()
            dct_string = collector_szer.dict_to_string(dct)

        except Exception as e:
            self.logger.info('Collector combine robot info error: %s' % e )

        return dct_string

    @need_to_handle
    def get_network_info(self):
        """
        [
            [
                ['ServiceId', 'wifi_48a9d24b4844_61786d646576_managed_psk'],
                ['Name', 'axmdev'],
                ['Type', 'wifi'],
                ['State', 'online'],
                ['Favorite', True],
                ['Autoconnect', True],
                ['Security', ['psk']],
                ['Domains', []],
                ['Nameserver', ['202.96.134.133', '202.96.128.166']],
                ['IPv4', [
                    ['Method', 'dhcp'],
                    ['Address', '192.168.1.147'],
                    ['Netmask', '255.255.255.0'],
                    ['Gateway', '192.168.1.1']
                ]],
                ['IPv6', [
                    ['Method', 'auto']
                ]],
                ['Proxy', [
                    ['Method', 'direct']
                ]],
                ['Strength', 78 L],
                ['Error', '']
            ]
        ]
        """
        network_info = {}

        services = self.ALConnectionManager.services()

        try:
            for service in services:
                if service[0][0] == 'ServiceId':
                    s_id = service[0][1]

                    if s_id.startswith('wifi'):
                        for item in service:
                            # for 'IPv4'/'IPv6'/'Proxy'
                            if isinstance(item[1], list) \
                                and len(item[1]) \
                                and isinstance(item[1][0], list):

                                v_dct = {}
                                for l in item[1]:
                                    v_dct.setdefault(l[0], l[1])

                                network_info.setdefault(item[0], v_dct)

                            # for other 
                            else:
                                network_info.setdefault(item[0], item[1])

        except Exception as e:
            self.logger.info('QiAssistant get network info errror: %s' % e)

        return {'network_info' : network_info}

    @need_to_handle
    def get_robot_info(self):
        info = {
            'robot_name' : self.ALSystem.robotName(),
            'system_version' : self.ALSystem.systemVersion(),

            'is_wakeup' : self.ALMotion.robotIsWakeUp(),

            'body_id' : self.ALMemory.getData("Device/DeviceList/ChestBoard/BodyId"),
        }

        return info

    @need_to_handle
    def get_battery_info(self):
        return {'battery_remain' : self.ALBattery.getBatteryCharge()}

    @need_to_handle
    def get_cpu_temperature(self):
        return {
            'cpu_temperature' : self.ALMemory.getData('Device/SubDeviceList/Head/Temperature/Sensor/Value'),
        }
    
    @need_to_handle
    def get_basic_awareness_status(self):
        return {
            'basic_awareness_enabled' : self.ALBasicAwareness.isEnabled(),
            'basic_awareness_running' : self.ALBasicAwareness.isRunning(),
            # 'basic_awareness_paused' : self.ALBasicAwareness.isAwarenessPaused(),
        }

    @need_to_handle
    def get_output_vol(self):
        return {
            'output_vol' : self.ALAudioDevice.getOutputVolume(),
        }

    @need_to_handle
    def get_device_error(self):
        key_lst = [
            "BackPlatformBoard",
            "Battery",
            "BatteryFuelGauge",
            "ChestBoard",
            "EarLeds",
            "FaceBoard",
            "FrontPlatformBoard",
            "FuseBoard",
            "HeadBoard",
            "HipBoard",
            "HubBoardPlatform",
            "InertialSensor",
            "InertialSensorBase",
            "LaserSensorFrontPlatform",
            "LaserSensorLeftPlatform",
            "LaserSensorRightPlatform",
            "LeftArmBoard",
            "LeftHandBoard",
            "LeftShoulderBoard",
            "RightArmBoard",
            "RightHandBoard",
            "RightShoulderBoard",
            "ThighBoard",
            "TouchBoard",
        ]
        pattern = "Device/DeviceList/{key}/Error"
        mem_key_lst = [pattern.format(key = k) for k in key_lst]
        
        val_tup = self.ALMemory.getListData(mem_key_lst),
        val_lst = val_tup[0]
        return { 'device_error' : dict(zip(key_lst, val_lst)), }

    @need_to_handle
    def get_joint_temperature(self):
        key_lst = [
            "HeadPitch",
            "HeadYaw",
            "HipPitch",
            "HipRoll",
            "KneePitch",
            "LElbowRoll",
            "LElbowYaw",
            "LHand",
            "LShoulderPitch",
            "LShoulderRoll",
            "LWristYaw",
            "RElbowRoll",
            "RElbowYaw",
            "RHand",
            "RShoulderPitch",
            "RShoulderRoll",
            "RWristYaw",
        ]
        pattern = "Device/SubDeviceList/{key}/Temperature/Sensor/Value"
        mem_key_lst = [pattern.format(key = k) for k in key_lst]

        val_tup = self.ALMemory.getListData(key_lst),
        val_lst = val_tup[0]
        return { 'joint_temperature' : dict(zip(key_lst, val_lst)), }

    def get_installed_behaviors(self):
        return {
            'installed' : self.ALBehaviorManager.getInstalledBehaviors(),
        }
    
    def get_loaded_behaviors(self):
        return {
            'loaded' : self.ALBehaviorManager.getLoadedBehaviors(),
        }

    def get_running_behaviors(self):
        return {
            'running' : self.ALBehaviorManager.getRunningBehaviors(),
        }

    def set_robot_id(self):
        if not Collector.robot_id:
            Collector.robot_id = self.ALMemory.\
                getData("Device/DeviceList/ChestBoard/BodyId")

    @classmethod
    def get_robot_id(cls):
        return cls.robot_id


class Executor(object):
    def __init__(self):
        self.logger = InfoLogger(__name__).get_logger()

        self.sys_command = SystemCommand()
        self.behavior_command = BehaviorCommand()
        self.package_command = PackageCommand()
        self.video_command = VideoCommand()
        self.demo_command = DemoCommand()
        self.ssh_command = SSHCommand()
        self.audio_command = AudioCommand()
        self.media_command = MediaCommand()

        self.command_maps = (
            self.sys_command,
            self.behavior_command,
            self.package_command,
            self.video_command,
            self.demo_command,
            self.ssh_command,
            self.audio_command,
            self.media_command,
        )

    def get_command_func(self, command):
        # command_map = {
        #     'reboot'      : self.sys_command.reboot,
        #     'shutdown'    : self.sys_command.shutdown,
        #     'change_pw'   : self.sys_command.change_pw,
        #     'change_name' : self.sys_command.change_name,
        #     'basic_awareness_enable'  : self.sys_command.basic_awareness_enable,
        #     'basic_awareness_disable' : self.sys_command.basic_awareness_disable,
        #     'set_output_vol' : self.sys_command.set_output_vol,
        #     'rest'    : self.sys_command.rest,
        #     'wake_up' : self.sys_command.wake_up,

        #     'count_off' : self.demo_command.count_off,
        #     'where_are_you' : self.demo_command.where_are_you,
        # }

        # return command_map.get(command, None)

        for command_cls in self.command_maps:
            if hasattr(command_cls, command):
                return getattr(command_cls, command)

        return None

    def command_explain(self, command_string):
        try:
            exec_szer = ExecutorSerializer()
            exec_obj = exec_szer.parse_from_string(command_string)

            command = exec_obj.executor.command
            args = exec_obj.executor.args
            origin = exec_obj.executor.origin

            self.logger.info('command: %s' % command)
            self.logger.info('args: %s' % str(args))
            self.logger.info('origin: %s' % origin)

            res = None
            exception = None

            func = self.get_command_func(command)

            if func:
                taken_args = inspect.getargspec(func).args

                try:
                    # taken_args : ['self', ...]
                    if len(taken_args) > 1:
                        res = func(args)
                    else:
                        res = func()

                    self.logger.info('Command excuted')

                except Exception as e:
                    self.logger.info('Executor run func error: %s' % e)
                    exception = str(e)

                try:
                    format_res = json.dumps(res)
                except:
                    format_res = str(res)

                raiser_szer = RaiserSerializer()
                raiser_str = raiser_szer.dict_to_string({
                                'command' : command,
                                'args' : args,
                                'origin' : origin,
                                'response' : format_res,
                                'exception' : str(exception),
                             })

                self.logger.info('raiser_str: %r' % raiser_str)

                return raiser_str

        except Exception as e:
            self.logger.info('Executor command explain error: %s' % e)


class SystemCommand(QiAssistant):
    def __init__(self):
        super(SystemCommand, self).__init__()

    def reboot(self):
        self.ALMotion.rest() 
        self.ALSystem.reboot()
        return None

    def shutdown(self):
        self.ALMotion.rest() 
        self.ALSystem.shutdown()
        return None

    def change_pw(self, args):
        assert len(args) == 2, 'length of args must be 2'

        old, new = args
        self.ALSystem.changePassword(old, new)
        return None

    def change_name(self, args):
        assert len(args) == 1, 'length of args must be 1'

        name = args[0]
        self.ALSystem.setRobotName(name)
        return None

    def basic_awareness_enable(self):
        self.ALBasicAwareness.setEnabled(True)
        return None

    def basic_awareness_disable(self):
        self.ALBasicAwareness.setEnabled(False)
        return None

    def set_output_vol(self, args):
        assert len(args) == 1, 'length of args must be 1'

        vol = args[0]
        assert str(vol).isdigit(), 'vol is not digits'

        self.ALAudioDevice.setOutputVolume(int(vol))
        return None

    def rest(self):
        res = self.ALMotion.rest()
        return res

    def wake_up(self):
        self.ALMotion.wakeUp() 
        return None

    def say(self, args):
        assert len(args) == 1, 'length of args must be 1'

        text = args[0]
        self.text_to_speech(text)
        return None

    def move_head(self, args):
        assert len(args) == 2, 'length of args must be 2'

        move_speed = 0.15
        max_yaw = 1.5
        min_yaw = -1.5
        max_pitch = 0.3
        min_pitch = -0.3

        yaw, pitch = [float(arg) for arg in args]

        # Horizontal range: left 90 degree, right 90 degree
        # Vertical range: up 30 degree, down 30 degree
        yaw = min(yaw, max_yaw) if yaw > 0 else max(yaw, min_yaw)
        pitch = min(pitch, max_pitch) if pitch > 0 else max(pitch, min_pitch)
        
        self.ALMotion.setAngles("HeadYaw", yaw, move_speed)
        self.ALMotion.setAngles("HeadPitch", pitch, move_speed)


class BehaviorCommand(QiAssistant):
    def __init__(self):
        super(BehaviorCommand, self).__init__()
        self.collector = Collector()

    def get_behaviors(self, args):
        types = args[0] if args else None

        d = {}
        d.update(self.collector.get_installed_behaviors())
        d.update(self.collector.get_loaded_behaviors())
        d.update(self.collector.get_running_behaviors())
        
        data = d.get(types, d)

        return data

    def run_behavior(self, args):
        assert len(args) == 1, 'length of args must be 1'

        b_name = args[0]
        self.ALBehaviorManager.runBehavior(b_name) 
        return None

    def start_behavior(self, args):
        assert len(args) == 1, 'length of args must be 1'

        b_name = args[0]
        self.ALBehaviorManager.startBehavior(b_name) 
        return None

    def stop_behavior(self, args):
        assert len(args) == 1, 'length of args must be 1'

        b_name = args[0]
        self.ALBehaviorManager.stopBehavior(b_name) 
        return None

    def is_behavior_installed(self, args):
        assert len(args) == 1, 'length of args must be 1'

        b_name = args[0]
        result = self.ALBehaviorManager.isBehaviorInstalled(b_name) 
        return {'result' : result}

    def is_behavior_loaded(self, args):
        assert len(args) == 1, 'length of args must be 1'

        b_name = args[0]
        result = self.ALBehaviorManager.isBehaviorLoaded(b_name) 
        return {'result' : result}

    def is_behavior_running(self, args):
        assert len(args) == 1, 'length of args must be 1'

        b_name = args[0]
        result = self.ALBehaviorManager.isBehaviorRunning(b_name) 
        return {'result' : result}

    def get_default_behaviors(self):
        result_lst = self.ALBehaviorManager.getDefaultBehaviors() 
        return {'default' : result_lst}

    def set_default_behavior(self, args):
        assert len(args) == 1, 'length of args must be 1'

        b_name = args[0]
        result = self.ALBehaviorManager.addDefaultBehavior(b_name) 
        return {'result' : result}

    def remove_default_behavior(self, args):
        assert len(args) == 1, 'length of args must be 1'

        b_name = args[0]
        result = self.ALBehaviorManager.removeDefaultBehavior(b_name) 
        return {'result' : result}


class PackageCommand(QiAssistant):
    def __init__(self):
        super(PackageCommand, self).__init__()

    def has_package(self, args):
        assert len(args) == 1, 'length of args must be 1'

        p_uuid = args[0]
        res = self.PackageManager.hasPackage(p_uuid)

        return {'has_package' : res}

    def install_package_local(self, args):
        path = args[0] if args else None
        md5 = args[1] if args else None

        if not path:
            # os.system('scp ...@data30.axmtec.com:/tmp/new.pkg /tmp')
            path = ConfigFile.local_path

        # result = self.PackageManager.install(path)
        # return {'result':result}

        pkg_md5 = hashlib.md5(open(path, 'r').read()).hexdigest()

        result = self.PackageManager.installCheckMd5(path, pkg_md5)
        return {'result':result}

    def install_package(self, args):
        pkg_path = ConfigFile.pkg_path

        md5 = args[0] if args else None
        pkg_name = args[1] if args else None

        assert md5 and pkg_name, '[PackageManager] md5 or pkg_name missing'

        res = requests.get(ConfigFile.pkg_dl_url, params = {'pkg_name' : pkg_name})

        pkg_data = res.content
        pkg_md5 = hashlib.md5(pkg_data).hexdigest()

        # self.logger.info('[PackageManager] md5:' + md5)
        # self.logger.info('[PackageManager] pkg_md5:' + pkg_md5)

        result = False

        if md5 == pkg_md5:
            with open(pkg_path, 'wb') as f:
                f.write(pkg_data)

            result = self.PackageManager.install(pkg_path)

            # self.logger.info('[PackageManager] install result:' + str(result))

            # Remove package
            os.remove(pkg_path)

        else:
            self.logger.info('[PackageManager] download package md5 error')
            self.logger.info('[PackageManager] md5:' + md5)
            self.logger.info('[PackageManager] pkg_md5:' + pkg_md5)

        return {'result':result}

    def remove_package(self, args):
        assert len(args) == 1, 'length of args must be 1'

        p_uuid = args[0]
        result = self.PackageManager.removePkg(p_uuid) 
        return {'result':result}


class VideoCommand(QiAssistant):
    def __init__(self):
        super(VideoCommand, self).__init__()

        self.robot_uid = Collector.get_robot_id()
        self.video_feed = VideoFeedProxy(self.robot_uid)

        self.name = None
        self.handle = None

    def video_start(self, args):
        self.logger.info("Starting robot video stream")

        image_scale = args[0] if args else None

        # Naoqi document show that same name can only use 6 times
        self.name = "axm_puppet_video" + uuid.uuid4().hex

        if image_scale == 'luma':
            resolution = ConfigVideo.resolution_luma
            color_space = ConfigVideo.color_space_luma
        else:
            resolution = ConfigVideo.resolution
            color_space = ConfigVideo.color_space

        camera_index = ConfigVideo.camera_index
        fps = ConfigVideo.fps

        try:
            handle = self.ALVideoDevice.subscribeCamera(\
                self.name, camera_index, resolution, color_space, fps)

            self.handle = handle

            func = self.ALVideoDevice.getImageRemote

            self.video_feed.start(func, handle)

        except Exception as e:
            self.logger.info('VideoCommand video_start error : %s' % e)

    def video_stop(self):
        self.logger.info("Stop robot video stream")

        try:
            self.video_feed.stop()

            self.ALVideoDevice.releaseImage(self.handle)
            self.ALVideoDevice.unsubscribe(self.name)

        except Exception as e:
            self.logger.info('VideoCommand video_stop error : %s' % e)

        self.logger.info("Robot video stream stopped")


class AudioCommand(QiAssistant):
    def __init__(self):
        super(AudioCommand, self).__init__()
        self.robot_uid = Collector.get_robot_id()
        self.audio_stream = AudioStreamProxy(self.robot_uid)

    def audio_start(self):
        self.logger.info("Starting robot audio")
        self.audio_stream.start()
        self.logger.info("Start robot audio done")

    def audio_stop(self):
        self.logger.info("Stop robot audio")
        self.audio_stream.stop()
        self.logger.info("Stop robot audio done")


class MediaCommand(QiAssistant):
    def __init__(self):
        super(MediaCommand, self).__init__()

        self.robot_uid = Collector.get_robot_id()
        self.media_stream = MediaStreamProxy(self.robot_uid)

        self.name = None
        self.handle = None

    def media_stream_start(self, args):
        self.logger.info("Starting robot media stream")

        # Naoqi document show that same name can only use 6 times
        self.name = "axm_puppet_media_stream_" + uuid.uuid4().hex

        # Default bitrates are set in config, something like '160k'
        bit_dict = {}
        if args and len(args) == 2 and args[0].endswith('k') and args[1].endswith('k'):
            bit_dict = {
                'audio_bitrate' : args[0],
                'video_bitrate' : args[1],
            }

        camera_index = ConfigMedia.camera_index
        resolution = ConfigMedia.resolution
        color_space = ConfigMedia.color_space
        fps = ConfigMedia.fps

        try:
            handle = self.ALVideoDevice.subscribeCamera(\
                self.name, camera_index, resolution, color_space, fps)

            self.handle = handle

            func = self.ALVideoDevice.getImageRemote

            self.media_stream.start(func, handle, bit_dict)

        except Exception as e:
            self.logger.info('MediaCommand media_stream_start error : %s' % e)

    def media_stream_stop(self):
        self.logger.info("Stop robot media stream")

        try:
            self.media_stream.stop()

            self.ALVideoDevice.releaseImage(self.handle)
            self.ALVideoDevice.unsubscribe(self.name)

        except Exception as e:
            self.logger.info('MediaCommand media_stream_stop error : %s' % e)

        self.logger.info("Robot media stream stopped")


class SSHCommand(object):
    def __init__(self):
        self.robot_uid = Collector.get_robot_id()
        self.client_proxy = ClientProxy(self.robot_uid)
        
    def start_ssh(self, args):
        assert len(args) == 1, 'length of args must be 1'
        term_id = args[0]

        self.client_proxy.start(term_id)
        return None

    def stop_ssh(self, args):
        assert len(args) == 1, 'length of args must be 1'
        term_id = args[0]

        self.client_proxy.stop(term_id)
        return None

    def restart_ssh(self, args):
        assert len(args) == 1, 'length of args must be 1'
        term_id = args[0]

        self.client_proxy.restart(term_id)
        return None

    def start_proxy_server(self):
        start_servers()
        return None


class MovingCommand(QiAssistant):
    def __init__(self):
        super(MovingCommand, self).__init__()

    def walk(self, args):
        self.ALMotion.wakeUp()

    def body_rotate(self, args):
        self.ALMotion.wakeUp()

    def arm_control(self, args):
        self.ALMotion.wakeUp()

    def waist_control(self, args):
        self.ALMotion.wakeUp()

    def head_control(self, args):
        pass

    def smooth_rotate(self, args):
        # move head first
        # move body
        # move arms and legs
        pass


class DemoCommand(QiAssistant):
    def __init__(self):
        super(DemoCommand, self).__init__()

    def uname(self):
        self.logger.info('Body_ID: %s' % Collector.get_robot_id())
        return None

    def where_are_you(self):
        self.text_to_speech('Hello! I am here!')
        return None

    def finger_game(self, args):
        assert len(args) == 2, 'length of args must be 2'
        my_gesture = args[0]
        result = args[1]

        self.raise_arm()

        self.text_to_speech('1')
        time.sleep(0.5)
        self.text_to_speech('2')
        time.sleep(0.5)
        self.text_to_speech('3')
        time.sleep(0.5)

        self.ALMotion.angleInterpolationWithSpeed('RShoulderPitch', 0.5, 0.2, isAbsolute = True)
        time.sleep(0.5)

        self.logger.info('my_gesture: %s' % my_gesture)
        self.logger.info('result: %s' % result)

        if my_gesture == 'rock':
            self.ALMotion.closeHand("RHand")
        # elif my_gesture == 'scissors':
        #     pass
        elif my_gesture == 'paper':
            self.ALMotion.openHand("RHand")

        self.text_to_speech('Haha')

        if result == 'win':
            self.text_to_speech('Yes')
        elif result == 'lose':
            self.text_to_speech('No')

        self.ALMotion.angleInterpolationWithSpeed('RShoulderPitch', 0.5, 0.2, isAbsolute = True)

        return None

    def count_off(self, args):
        my_num = args[0] if args else '1'
        self.text_to_speech(my_num)
        return None

    def raise_arm(self):
        # Only right arm now
        self.ALMotion.wakeUp()

        self.ALMotion.angleInterpolationWithSpeed('RShoulderRoll', -0.5, 0.2, isAbsolute = True)
        self.ALMotion.angleInterpolationWithSpeed('RShoulderPitch', -1.0, 0.2, isAbsolute = True)

        return None

    def lower_arm(self):
        self.ALMotion.angleInterpolationWithSpeed('RShoulderRoll', 0.5, 0.2, isAbsolute = True)
        self.ALMotion.angleInterpolationWithSpeed('RShoulderPitch', 1.0, 0.2, isAbsolute = True)

        return None

