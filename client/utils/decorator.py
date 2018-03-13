


def need_to_handle(func):
    def msg_handler(self, *args, **kwargs):
        return func(self, *args, **kwargs)
    return msg_handler
