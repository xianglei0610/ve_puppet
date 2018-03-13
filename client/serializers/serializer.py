

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
        self.serializer.executor.origin = dct.get('origin')

        return self.serializer.SerializeToString()


class RaiserSerializer(BaseSerializer):
    def __init__(self):
        super(RaiserSerializer, self).__init__('raiser')
        self.character = 'raiser'

    def dict_to_string(self, dct):
        self.serializer.raiser.command = dct.get('command')
        self.serializer.raiser.args.extend(dct.get('args'))
        self.serializer.raiser.origin = dct.get('origin')
        self.serializer.raiser.response = dct.get('response')
        self.serializer.raiser.exception = dct.get('exception')

        return self.serializer.SerializeToString()


class CommanderSerializer(BaseSerializer):
    def __init__(self):
        super(CommanderSerializer, self).__init__('commander')
        self.character = 'commander'

    def dict_to_string(self, dct):
        self.serializer.commander.command = dct.get('command')
        self.serializer.commander.clients.extend(dct.get('client'))
        self.serializer.commander.args.extend(dct.get('args'))

        return self.serializer.SerializeToString()


class CollectorSerializer(BaseSerializer):
    def __init__(self):
        super(CollectorSerializer, self).__init__('collector')
        self.character = 'collector'

    def dict_to_string(self, dct):
        self.serializer.collector.info = json.dumps(dct)

        return self.serializer.SerializeToString()

        self.serializer.executor.args.extend(dct.get('args'))
        self.serializer.executor.response = dct.get('response')

        return self.serializer.SerializeToString()
