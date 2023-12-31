import time

from .krpc import KrpcHandler
from .telemetry import TelemetryRecorder
from .security import ParachuteHandler
from .science import ScienceCollector
from .computer import AscensionComputer,TWRComputer, DirectionComputer

from threading import Thread

from krpc.services.spacecenter import Vessel
from loguru import logger

class Ship:

    def __init__(self) -> None:
        self.vessel :Vessel = KrpcHandler.conn.space_center.active_vessel
        self.vessel_initial_stage_count = len(self.vessel.parts.decouplers) + 1
        self.ppool = [
            TelemetryRecorder.process,
            ParachuteHandler.process,
            StageDropper.process
            # ScienceCollector.process
        ]

        self.ascension_computer = AscensionComputer()
        self.direction_computer = DirectionComputer()
        self.twr_computer = TWRComputer()


    def start(self):
        logger.trace("Ship starting")
        for process in self.ppool:
            process.start()
        logger.trace("Ship started")

    def stop(self):
        logger.trace("Ship stopping")
        for process in self.ppool:
            process.join()
        logger.trace("Ship stopped")

    def launch(self):
        self.direction_computer.prepare_to_launch()
        self.vessel.control.throttle = 1
        self.vessel.auto_pilot.engage()

        self.vessel.control.activate_next_stage()


class StageDropper:
    @classmethod
    @property
    def process(cls):
        return cls().thread()

    def __init__(self) -> None:
        self.vessel :Vessel = KrpcHandler.conn.space_center.active_vessel
        self.engage_alt = 200
        self.tps = 1 # tick per second

    def checkFuelInstage(self):
        solidFuelAmount = self.vessel.resources_in_decouple_stage(self.vessel.control.current_stage - 1).amount('SolidFuel')
        LiquidFuelAmount = self.vessel.resources_in_decouple_stage(self.vessel.control.current_stage - 1).amount('LiquidFuel')

        fuelAmount = solidFuelAmount + LiquidFuelAmount

        if fuelAmount < 0.05:
            self.vessel.control.activate_next_stage()
            logger.info("StageDropper stage number {} dropped. ".format(self.vessel.control.current_stage))
            time.sleep(0.5)

    def run(self):
        logger.debug("StageDropper start.")
        try:
            altitude = self.vessel.flight().mean_altitude
            while altitude < self.engage_alt:
                time.sleep(0.1)
                altitude = self.vessel.flight().mean_altitude

            logger.debug("StageDropper engaged")
            while self.vessel.control.current_stage > 1:
                self.checkFuelInstage()
                time.sleep(self.tps)
        finally:
            logger.debug("StageDropper stop.")

    def thread(self):

        return Thread(target=self.run)

