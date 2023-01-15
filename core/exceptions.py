import sys


class BatchException(Exception):
    def __init__(self, msg='', code=-1, file=sys.stderr, *args, **kwargs):
        self.msg = msg.format(*args, **kwargs)
        self.code = code
        self.file = file

    def stop(self):
        print(self.msg, file=self.file)
        sys.exit(self.code)
