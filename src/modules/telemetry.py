import random
import string
import time

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from .krpcw import KrpcHandler

from krpc.services.spacecenter import Vessel,Flight
from threading import Thread
from loguru import logger

class TelemetryRecorder:

    @classmethod
    @property
    def process(cls):
        return cls().thread()

    def __init__(self) -> None:

        self.influx_url = "http://localhost:8086"
        self.influx_org = "MB-SPACE"
        self.influx_bucket = "telemetry"
        self.influx_token = "mD4DML-OQ7mJTSt2C3ZRzhSCw7VFHkRD2MtrndViKQtNnHIU4_qD0jyJ1oE6M2J-B_Nx8NspgMUWszktSfeaRw=="
        self.influx_client =  InfluxDBClient(url=self.influx_url, token=self.influx_token, org=self.influx_org)
        self.influx = self.influx_client.write_api(write_options=SYNCHRONOUS)

        self.vessel :Vessel = KrpcHandler.conn.space_center.active_vessel

        self.flight_uid = ''.join(random.choice(string.ascii_lowercase) for i in range(6))
        logger.info("TelemetryRecorder flight uid : " + self.flight_uid)

        self.vessel_stage_count = len(self.vessel.parts.decouplers) + 1
        self.pps = 4 # point per second

    def instant_point(self):

        print(self.vessel.flight().speed)
        flight :Flight= self.vessel.flight()
        point = (
            Point("flight")
                .tag("uid", self.flight_uid)
                .tag("ship", self.vessel.name)
                .tag("stage", self.vessel.control.current_stage if self.vessel.control.current_stage <= self.vessel_stage_count else None)

                .field("mean_altitude", flight.mean_altitude)
                .field("elevation", flight.elevation)
                .field("latitude", flight.latitude)
                .field("longitude", flight.longitude)
                .field("velocity", flight.velocity)
                .field("horizontal_speed", flight.horizontal_speed)
                .field("vertical_speed", flight.vertical_speed)
                .field("total_air_temperature", flight.total_air_temperature)
        )

        self.influx.write(bucket=self.influx_bucket, org=self.influx_org, record=point)

    def run(self):
        logger.debug("TelemetryRecorder start.")
        try:
            while True:
                self.instant_point()
                time.sleep(1 / self.pps)
        finally:
            self.influx_client.close()
            logger.debug("TelemetryRecorder stop.")

    def thread(self):
        return Thread(target=self.run)