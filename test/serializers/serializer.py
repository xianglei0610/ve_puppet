# --------------------------------
# Author : Garvey Ding
# Created: 2016-11-15
# Modify : 2016-11-17 by Garvey
# --------------------------------

import json
from serializer_pb2 import Serializer


class BaseSerializer(object):
    def __init__(self, character='base'):
        self.serializer = Serializer()
        self.serializer.character = character

    # def dict_to_string(self, dct):
    #     return ''

    def parse_from_string(self, msg_string):
        self.serializer.ParseFromString(msg_string)
        return self.serializer


class ExecutorSerializer(BaseSerializer):
    def __init__(self):
        super(ExecutorSerializer, self).__init__('executor')
        self.character = 'executor'

    def dict_to_string(self, dct):
        self.serializer.executor.command = dct.get('command')
        self.serializer.executor.args.extend(dct.get('args'))

        return self.serializer.SerializeToString()


class CommanderSerializer(BaseSerializer):
    def __init__(self):
        super(CommanderSerializer, self).__init__('commander')
        self.character = 'commander'

    def dict_to_string(self, dct):
        self.serializer.commander.command = dct.get('command')
        self.serializer.commander.clients.extend(dct.get('clients'))
        self.serializer.commander.args.extend(dct.get('args'))

        return self.serializer.SerializeToString()


class CollectorSerializer(BaseSerializer):
    def __init__(self):
        super(CollectorSerializer, self).__init__('collector')
        self.character = 'collector'

    def dict_to_string(self, dct):
        self.serializer.collector.info = json.dumps(dct)

        return self.serializer.SerializeToString()
