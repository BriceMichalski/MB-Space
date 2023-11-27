import time

from .krpc import KrpcHandler
from krpc.services.spacecenter import Vessel
from loguru import logger
from threading import Thread

class ScienceCollector:
    @classmethod
    @property
    def process(cls):
        return cls().thread()

    def __init__(self) -> None:
        self.vessel :Vessel = KrpcHandler.conn.space_center.active_vessel
        self.experiments = self.vessel.parts.experiments

        self.expi = 10 # experiment intervale

    def runExperiments(self):
        for exp in self.experiments :
            if exp.rerunnable:
                exp.run()
                exp.transmit()
        logger.debug("ScienceCollector experiments done.")

    def run(self):
        logger.debug("ScienceCollector start.")
        try:
            while True:
                self.runExperiments()
                time.sleep(self.expi)
        finally:
            logger.debug("ScienceCollector stop.")

    def thread(self):
        return Thread(target=self.run)