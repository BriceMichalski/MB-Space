import time
import math

from .math import Vector
from .meta import Singleton
from .krpc import KrpcHandler
from krpc.services.spacecenter import Vessel,VesselSituation
from loguru import logger
from threading import Thread


class Computer(metaclass=Singleton):
    def __init__(self) -> None:
        self.computerThread = Thread(target=self.run)
        self.vessel :Vessel = KrpcHandler.conn.space_center.active_vessel


    def run(self):
        raise Exception("Not implemented")

    def engage(self):
        if not self.computerThread.is_alive():
            self.computerThread.start()

    def disengage(self):
        self.computerThread.join()


class AscensionComputer(Computer):

    def run(self):
        self.inclinationThread.start()
        self.thrustherThread.start()

    def __init__(self) -> None:
        super().__init__()
        self.orbit_reached = False
        self.orbit_target_altitude = 0

        self.turn_start_altitude = 0
        self.turn_angle = 0

        self.twr = 0
        self.orbital_velocity = 0

        self.TWRComputer = TWRComputer()
        self.DIRComputer = DirectionComputer()

        self.inclinationThread = Thread(target=self.inclination)
        self.thrustherThread = Thread(target=self.thruster)


    # SETUP
    def setup(self,orbit_target_altitude,turn_start_altitude):
        self.orbit_target_altitude = orbit_target_altitude
        self.turn_start_altitude = turn_start_altitude
        self.compute_orbital_velocity()

        logger.info("AscensionComputer - new orbite target set at {}m".format(orbit_target_altitude))

    def compute_orbital_velocity(self):
        G = KrpcHandler.conn.space_center.g
        body_mass = self.vessel.orbit.body.mass
        body_radius = self.vessel.orbit.body.equatorial_radius

        distance_from_center = self.orbit_target_altitude + body_radius
        orbital_velocity = math.sqrt(G * body_mass / distance_from_center)

        self.orbital_velocity = orbital_velocity
        logger.debug("AscensionComputer - Orbital velocity computed: {} m/s".format(orbital_velocity) )


    # Trusther
    def thruster(self):
        self.waitSolidFuelBurned()
        logger.debug("AscensionComputer - Solid fuel burned, thruster regulation start")

        self.updateTWR(1.5)
        self.TWRComputer.engage()

        while  self.vessel.orbit.apoapsis_altitude < (self.orbit_target_altitude * 0.95):
            time.sleep(0.5)

        self.updateTWR(0)
        logger.info("AscensionComputer - Apoapsis approche target altitude")

    def updateTWR(self,twr):
        self.twr = twr
        self.TWRComputer.setup(self.twr)

    def waitSolidFuelBurned(self):
        while self.vessel.situation == VesselSituation.pre_launch:
            time.sleep(1)
        while   self.vessel.resources_in_decouple_stage(self.vessel.control.current_stage - 1).amount('SolidFuel') > 0:
            time.sleep(1)


    def compute_delta_velocity(self):
        return self.orbital_velocity - self.vessel.flight().horizontal_speed

    # Inclination
    def inclination(self):
        logger.debug("AscensionComputer - engaged")
        self.waitTurnStartAltitude()
        logger.info("AscensionComputer - gravity turn start")
        self.gravityTurnGuidance()
        logger.info("AscensionComputer - Approaching target apoapsis")
        logger.info("AscensionComputer - Orbit reached")
        logger.info("AscensionComputer - stopped")

    def waitTurnStartAltitude(self):
        altitude = self.vessel.flight().mean_altitude
        while altitude < self.turn_start_altitude:
            time.sleep(0.1)
            altitude = self.vessel.flight().mean_altitude


    def gravityTurnGuidance(self):
        self.DIRComputer.set_pitch(85)
        time.sleep(5)

        self.DIRComputer.set_pitch(None)
        while not self.orbit_reached:
            self.DIRComputer.point_to_prograde()
            time.sleep(0.2)






class TWRComputer(Computer):
    def __init__(self) -> None:
        super().__init__()
        self.target_twr = None
        self.throttle_adjustment = 0

    def setup(self,target_twr):
        self.target_twr = target_twr

    def run(self):
        logger.info("TWRComputer - engaged")
        while True:
            current_twr = self.vessel.thrust / (self.vessel.mass * self.vessel.orbit.body.surface_gravity)
            error = self.target_twr - current_twr

            self.throttle_adjustment = error * 0.05

            current_throttle = self.vessel.control.throttle
            new_throttle = max(0.0, min(1.0, current_throttle + self.throttle_adjustment))
            self.vessel.control.throttle = new_throttle

            time.sleep(0.1)

class DirectionComputer(Computer):
    def __init__(self) -> None:
        super().__init__()
        self.target_dir = (0,1,0)
        self.reference_frame = None


    def run(self):
        while True:
            self.vessel.auto_pilot.reference_frame = self.reference_frame
            self.vessel.auto_pilot.target_direction = self.target_dir
            time.sleep(0.1)

    def use_vessel_velocity_reference_frame(self):
        if  self.reference_frame != self.vessel.surface_velocity_reference_frame:
            self.reference_frame = self.vessel.surface_velocity_reference_frame
            logger.debug("DirectionComputer - vessel.surface_velocity_reference_frame adopted")


    def use_vessel_reference_frame(self):
        if self.reference_frame != self.vessel.surface_reference_frame:
            self.reference_frame = self.vessel.surface_reference_frame
            logger.debug("DirectionComputer - vessel.surface_reference_frame adopted")

    def target(self,dir):
        self.target_dir = dir
        logger.debug("DirectionComputer - new target direction {} ".format(dir))

    def point_to_prograde(self):
        self.use_vessel_velocity_reference_frame()
        self.target((0,1,0))

    def point_to_retrograde(self):
        self.reference_frame = self.vessel.surface_velocity_reference_frame
        self.target((0,1,0))

    def prepare_to_launch(self):
        self.use_vessel_reference_frame()
        self.vessel.auto_pilot.target_pitch = 90
        self.vessel.auto_pilot.target_heading = 90

    def set_pitch(self,pitch):
        self.vessel.auto_pilot.target_pitch = pitch