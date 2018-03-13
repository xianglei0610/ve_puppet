

import logging
import os.path

from config import ConfigLogger


class BaseLogger(object):

    def __init__(self, name = None):
        self.name = name or __name__
        # self.logging_format = "%(asctime)s.%(msecs)03d %(levelname)s [%(name)s]: %(message)s"
        self.logging_format = "%(asctime)s %(levelname)s : %(message)s"
        self.date_format = "%Y-%m-%d %H:%M:%S"
        self.level = logging.INFO

        self.filename = os.path.join(ConfigLogger.log_path, ConfigLogger.log_file)

    def get_logger(self):
        logging.basicConfig(filename = self.filename, format = self.logging_format, datefmt = self.date_format)
        
        logger = logging.getLogger(self.name)
        logger.setLevel(self.level)

        return logger


class InfoLogger(BaseLogger):

    def __init__(self, name = None):
        super(InfoLogger, self).__init__(name = name)
        self.level = logging.INFO
