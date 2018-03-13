import qi
ip='127.0.0.1'
port=9559
full_path = 'tcp://127.0.0.1:9559'
app = qi.Application(url = 'tcp://127.0.0.1:9559')

app.start()
session = app.session

vd = session.service('ALVideoDevice')
name = "axm_puppet_video_0"
camera_index = 0
import vision_definitions
resolution = vision_definitions.kQVGA
color_space = vision_definitions.kRGBColorSpace
fps = 10

handle = vd.subscribeCamera(name, camera_index, resolution, color_space, fps)
image_container = vd.getImageRemote(handle)

image = image_container[6]



color_space_luma = vision_definitions.kYuvColorSpace
handle_luma = vd.subscribeCamera(name, camera_index, resolution, color_space_luma, fps)
image_container_luma = vd.getImageRemote(handle_luma)

image_luma = image_container_luma[6]



160 * 120 * 1 = 19200
160 * 120 * 3 = 57600
320 * 240 * 1 = 76800
640 * 480 * 1 = 307200



ad = session.service('ALAudioDevice')
module = 'test'
ad.subscribe(module)


ar = session.service('ALAudioRecorder')
filename = '/tmp/test.ogg'
type = 'ogg'
samplerate = 48000
channels = (0,0,1,0)
channels = (1,1,1,1)
ar.startMicrophonesRecording(filename, type, samplerate, channels)
ar.startMicrophonesRecording('/tmp/test.ogg', 'ogg', 48000, (1,1,1,1))
ar.startMicrophonesRecording('/tmp/test.ogg', 'ogg', 16000, (1,1,1,1))
ar.stopMicrophonesRecording()


ogg 4 channel 48000
1.6M/3 seconds 
530 k/s

wav 4 channel 48000
1.8M/4 seconds 
450 k/s

ogg 4 channel 16000
1.2M/9 seconds 
140 k/s

wav 4 channel 16000
0.66M/5 seconds 
131 k/s

wav 16000
0.08M/5 seconds
16 k/s


arecord -t wav -r 16000 -d 5 > a.wav




from Crypto.PublicKey import RSA

private_key = RSA.generate(1024)
print(private_key.exportKey())

public_key = private_key.publickey()
print(public_key.exportKey())





with open("puppet.pub", "w") as pub_file:
    pub_file.write(public_key.exportKey())

with open("puppet.pvt", "w") as pvt_file:
    pvt_file.write(private_key.exportKey())





with open('puppet.pub', 'r') as pub_file:
    pub_key = RSA.importKey(pub_file.read())

encrypted = pub_key.encrypt('hello world', None)
print(encrypted)

with open('puppet.pvt', 'r') as pvt_file:
    pvt_key = RSA.importKey(pvt_file.read())

text = pvt_key.decrypt(encrypted)
print(text)



s = '0b6c6add74440af773c63d670c74bd5b'
en_s = pub_key.encrypt(s, None)
pvt_key.decrypt(en_s)






from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

message = s
key = pub_key
cipher = PKCS1_OAEP.new(key)
ciphertext = cipher.encrypt(message)


key = pvt_key
pvt_cipher = PKCS1_OAEP.new(pvt_key)
message = pvt_cipher.decrypt(ciphertext)





















apt-get install libpcre3 libpcre3-dev

mkdir nginx_test
cd nginx_test

wget http://nginx.org/download/nginx-1.11.9.tar.gz
wget https://github.com/arut/nginx-rtmp-module/archive/master.zip


tar -zxvf nginx-1.11.9.tar.gz
unzip master.zip

cd nginx

vim configure
-NGX_PREFIX
./configure --with-http_ssl_module --add-module=../nginx-rtmp-module-master

make
make install

rtmp {
    server {
        listen 1935;
        chunk_size 4096;

        application live {
            live on;
            record off;
        }
    }
}

location /stat {
    rtmp_stat all;

    # Use this stylesheet to view XML as web page
    # in browser
    rtmp_stat_stylesheet stat.xsl;
}


cd nginx/sbin
./nginx -c /home/garvey/nginx/conf/nginx.conf

cd nginx/logs
tail -f access.log





SRS
=================

cd srs/trunk
./configure && make
./objs/srs -c conf/srs.conf
tail -f objs/srs.log


listen              1935;
vhost __defaultVhost__ {
    #最小延迟打开，默认是打开的，该选项打开的时候，mr默认关闭。
    min_latency     on;
    #Merged-Read，针对RTMP协议，为了提高性能，SRS对于上行的read使用merged-read，即SRS在读写时一次读取N毫秒的数据
    mr {
        enabled     off;
        #默认350ms，范围[300-2000]
        #latency     350;
    }
    #Merged-Write,SRS永远使用Merged-Write，即一次发送N毫秒的包给客户端。这个算法可以将RTMP下行的效率提升5倍左右,范围[350-1800]
    mw_latency      100;
    #enabled         on;
    #https://github.com/simple-rtmp-server/srs/wiki/v2_CN_LowLatency#gop-cache
    gop_cache       off;
    #配置直播队列的长度，服务器会将数据放在直播队列中，如果超过这个长度就清空到最后一个I帧
    #https://github.com/simple-rtmp-server/srs/wiki/v2_CN_LowLatency#%E7%B4%AF%E7%A7%AF%E5%BB%B6%E8%BF%9F
    queue_length    10;
    tcp_nodelay     on;

    dvr {
        enabled             on;
        dvr_path            ./objs/nginx/html/[app]/[stream].[timestamp].flv;
        dvr_plan            session;
    }
}














qicli call ALMemory.getDataList "Diagnosis/"

[ 
    "Diagnosis/Active/CameraTop/Error", 
    "Diagnosis/Active/CameraDepth/Error", 
    "Diagnosis/Active/CameraBottom/Error", 

    "Diagnosis/Passive/CameraTop/Error", 
    "Diagnosis/Passive/CameraDepth/Error", 
    "Diagnosis/Passive/CameraBottom/Error", 

    "Diagnosis/Temperature/CameraTop/Error", 
    "Diagnosis/Temperature/CameraDepth/Error", 
    "Diagnosis/Temperature/CameraBottom/Error" 
]





http://192.168.0.136/apps/robots_advanced/#/hardware


Head CPU
Device/SubDeviceList/Head/Temperature/Sensor/Value  50


Configurations
RobotConfig/Head/FullHeadId AP990237G02Y59100656
RobotConfig/Head/HeadId AP990237G02Y59100656


