from .krpcw import KrpcHandler
from .telemetry import TelemetryRecorder
from .security import ParachuteHandler

from krpc.services.spacecenter import Vessel
from loguru import logger

class Ship:

    def __init__(self) -> None:
        self.vessel :Vessel = KrpcHandler.conn.space_center.active_vessel
        self.vessel_initial_stage_count = len(self.vessel.parts.decouplers) + 1
        self.ppool = [
            TelemetryRecorder.process,
            ParachuteHandler.process
        ]

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

    def prepare(self):
        logger.trace("Ship preparation start")
        self.auto_pilot_target_pitch_and_heading(90, 90)
        self.vessel.auto_pilot.engage()
        self.vessel.control.throttle = 1
        logger.trace("Ship preparation finished")

    def auto_pilot_target_pitch_and_heading(self, pitch: float, heading: float):
        self.vessel.auto_pilot.target_pitch_and_heading(pitch, heading)
        logger.info("Ship auto pilot pitch and heading cahnge for : [{},{}]".format(pitch,heading))

    def auto_pilot_engage(self):
        self.vessel.auto_pilot.engage()
        logger.info("Ship auto pilot engaged")

    def launch(self):
        self.vessel.control.activate_next_stage()