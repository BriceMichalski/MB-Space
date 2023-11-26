import time

from .krpcw import KrpcHandler
from threading import Thread
from loguru import logger

from krpc.services.spacecenter import Vessel

class ParachuteHandler:
    @classmethod
    @property
    def process(cls):
        return cls().thread()

    def __init__(self) -> None:
        self.tps = 1 # tick per second
        self.vessel :Vessel = KrpcHandler.conn.space_center.active_vessel

        self.engaged = False
        self.deployed = False
        self.surface_alt = self.vessel.flight().surface_altitude
        self.previous_alt = self.surface_alt
        self.engage_alt = self.surface_alt + 100
        self.trigger_alt = self.surface_alt + 7000


    def tick(self):
        altitude = self.vessel.flight().mean_altitude

        #ENGAGE AT ASC
        if altitude > self.engage_alt > self.previous_alt and not self.engaged:
            self.engaged = True
            logger.info("Parachute Handler - engaged")

        # Trigger if :
        # DESC AND ENGAGE ALTITUDE NOT REACH
        # OR
        # ENGAGED AND ALTITUDE WAS LESS THAN PREVIOUS ALTITUDE
        SECURITY_CONDITION =  (not self.engaged) and (altitude < self.previous_alt) and (self.previous_alt - altitude > 5)
        ALTITUDE_COND = self.engaged and altitude < self.trigger_alt < self.previous_alt
        if SECURITY_CONDITION or ALTITUDE_COND:
            for parachute in self.vessel.parts.parachutes:
                parachute.deploy()
            self.deployed = True
            logger.info("Parachute Handler - deployed")
            if SECURITY_CONDITION:
                logger.debug("Parachutes deploy triggered by 'SECURITY_CONDITION'")
            if ALTITUDE_COND:
                logger.debug("Parachutes deploy triggered by 'ALTITUDE_COND'")

        self.previous_alt = altitude


    def run(self):
        logger.debug("ParachuteHandler start.")
        try:
            while not self.deployed:
                self.tick()
                time.sleep(1 / self.tps)
        finally:
            logger.debug("ParachuteHandler stop.")


    def thread(self):
        return Thread(target=self.run)