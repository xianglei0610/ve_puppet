

import base64
import datetime
import hashlib
import os
import uuid

from tornado.web import HTTPError

from config import ConfigFile
from servers.base import BaseFileHandler, BaseHTTPServer
from servers.clientmap import ConnectionMap
from utils.rsa import decrypt_pkcs1_v1_5


class PackageFileHandler(BaseFileHandler):
    def initialize(self):
        super(PackageFileHandler, self).initialize()
        self.name = self.__class__.__name__
        self.uid = uuid.uuid4().hex

        self.private_key = ConfigFile.private_key

        self.path = ConfigFile.path
        self.pkg_pattern = ConfigFile.pkg_pattern

        # start download right after upload done
        self.dl_after_ul = True

    def decrypt(self, encoded_data):
        return decrypt_pkcs1_v1_5(self.private_key, encoded_data)

    def post(self):
        """
        Params
            * robot_uid   : Robot uid.               [Required]
            * encoded_md5 : Encrypt package md5.     [Required]
            * package     : Package file.            [Required]
        """
        try:
            robot_uid = self.get_body_argument('robot_uid', None)
            encoded_md5 = self.get_body_argument('encoded_md5', None)

            f_data = self.request.files.get('package', None)

            assert robot_uid and encoded_md5 and f_data,\
                'required params missing: robot_uid or encoded_md5 or package'

            f_info = f_data.pop()
            f_name = f_info.get('filename', None)
            pkg_data = f_info.get('body', None)

            cal_md5 = hashlib.md5(pkg_data).hexdigest()
            pkg_md5 = self.decrypt(encoded_md5)

            # self.logger.info('cal_md5 : %s' % cal_md5)
            # self.logger.info('pkg_md5 : %s' % pkg_md5)

            if cal_md5 == pkg_md5:
                self.logger.info('[%s] package md5 check done' % self.name)

                pkg_name = self.pkg_pattern.format(\
                    f_name = f_name, md5 = cal_md5[:4], \
                    ts = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S'))

                pkg_file = os.path.join(self.path, pkg_name)

                with open(pkg_file, 'wb') as f:
                    f.write(pkg_data)

                self.logger.info('[%s] package receive done: %s' % (self.name, pkg_file))

                if self.dl_after_ul:
                    json_data = {
                        'command': 'install_package',
                        'clients': [robot_uid,],
                        'args': [cal_md5, pkg_name],
                    }

                    if ConnectionMap.sock_conn:
                        ConnectionMap.sock_conn.send_json_message(json_data, self.uid)

                        self.logger.info('[%s] start download done' % self.name)

            else:
                self.logger.info('[%s] package md5 check error' % self.name)
                raise HTTPError(400, reason = 'package md5 check error')

        except AssertionError as e:
            raise HTTPError(400, reason = 'required params missing')

        except Exception as e:
            self.logger.info("[%s] post error: %s" % (self.name, e))
            raise HTTPError(400, reason = 'post error %s' % e)

    def get(self):
        """
        Params
            * pkg_name : Package name. [Required]
        """
        try:
            pkg_name = self.get_argument('pkg_name', None)

            assert pkg_name, 'pkg_name must be given'

            pkg_file = os.path.join(self.path, pkg_name)

            if os.path.exists(pkg_file):
                with open(pkg_file, 'rb') as f:
                    self.write(f.read())

                self.logger.info('[%s] package send: %s'  % (self.name, pkg_file))
                # self.finish()

                if self.dl_after_ul:
                    # delete the package after download
                    os.remove(pkg_file)
                    self.logger.info('[%s] package removed: %s' % (self.name, pkg_file))

            else:
                self.logger.info('[%s] package not exists: %s' % (self.name, pkg_file))
                raise HTTPError(400, reason = 'package not exists')

        except AssertionError as e:
            raise HTTPError(400, reason = 'required params missing')

        except Exception as e:
            self.logger.info("[%s] get error: %s" % (self.name, e))


class FileServer(BaseHTTPServer):
    def __init__(self):
        self.port = ConfigFile.port
        super(FileServer, self).__init__(self.port)

        app_tup_lst = [
            (r'/puppet/file/package', PackageFileHandler),
        ]

        self.start(app_tup_lst)

