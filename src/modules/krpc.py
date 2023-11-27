import krpc

from .meta import Singleton
from krpc import Client

class KrpcHandler(metaclass=Singleton):

    def __init__(self) -> None:
        self.conn = krpc.connect(name='MB-Space')

    @classmethod
    @property
    def conn(cls) -> Client:
        return cls().conn
