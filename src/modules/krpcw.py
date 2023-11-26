import krpc

from .meta import Singleton

class KrpcHandler(metaclass=Singleton):

    def __init__(self) -> None:
        self.conn = krpc.connect(name='MB-Space')

    @classmethod
    @property
    def conn(cls):
        return cls().conn
