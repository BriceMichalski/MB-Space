import krpc
import time
import csv
import json

from loguru import logger
from krpc.services.spacecenter import Vessel
from multiprocessing import Process
from datetime import datetime

conn = krpc.connect(name='Space-B')
vessel = conn.space_center.active_vessel

def launch():
    print()
    print('3...')
    time.sleep(1)
    print('2...')
    time.sleep(1)
    print('1...')
    time.sleep(1)
    print('Launch!')
    print()
    vessel.control.activate_next_stage()
    logger.info("First stage started")

def telemetry_recorder():
    with open('telemetry.csv', 'w', newline='') as csvfile:
        telemetry_writer = csv.writer(csvfile)

        # Écrivez l'en-tête du CSV avec les noms des champs
        fieldnames = ['Time','CurrentStage', 'Altitude', 'Velocity', 'Throttle','FuelAmount']
        telemetry_writer.writerow(fieldnames)

        # Enregistrez la télémétrie pendant 10 secondes (par exemple)
    while True:
        with open('telemetry.csv', 'a', newline='') as csvfile:
            telemetry_writer = csv.writer(csvfile)
            # Obtenez les données de télémétrie
            currentStage = vessel.control.current_stage
            altitude = vessel.flight().mean_altitude
            velocity = vessel.flight().speed
            throttle = vessel.control.throttle
            fuelAmount = vessel.resources_in_decouple_stage(vessel.control.current_stage - 1).amount('SolidFuel')

            # Obtenez le temps actuel
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Écrivez les données dans le fichier CSV
            telemetry_writer.writerow([current_time, currentStage, altitude, velocity, throttle,fuelAmount])

            # Attendez un court instant avant de mettre à jour les données
        time.sleep(1)

def parachute_handler():
    engaged = False
    deployed = False

    surface_alt = vessel.flight().surface_altitude
    engage_alt = surface_alt + 100
    trigger_alt = surface_alt + 7000

    previous_alt = surface_alt

    while not deployed:
        altitude = vessel.flight().mean_altitude

        #ENGAGE AT ASC
        if altitude > engage_alt > previous_alt and not engaged:
            engaged = True
            logger.info("Parachute Handler - engaged")

        # Trigger if :
        # DESC AND ENGAGE ALTITUDE NOT REACH
        # OR
        # ENGAGED AND ALTITUDE WAS LESS THAN PREVIOUS ALTITUDE
        SECURITY_CONDITION =  (not engaged) and (altitude < previous_alt) and (previous_alt - altitude > 5)
        ALTITUDE_COND = engaged and altitude < trigger_alt < previous_alt
        if SECURITY_CONDITION or ALTITUDE_COND:
            for parachute in vessel.parts.parachutes:
                parachute.deploy()
            deployed = True
            logger.info("Parachute Handler - deployed")
            if SECURITY_CONDITION:
                logger.debug("Parachutes deploy triggered by 'SECURITY_CONDITION'")
            if ALTITUDE_COND:
                logger.debug("Parachutes deploy triggered by 'ALTITUDE_COND'")

        previous_alt = altitude
        time.sleep(0.1)

def overview():
    print("Ship: " + vessel.name)
    print("Parts Count: " + str(len(vessel.parts.decouplers) + 1))

def confirm():
    print()
    while True:
        message = "Confirmer? (oui/non) "
        reponse = input(message).strip().lower()
        if reponse in ("oui", "yes", "o", "y"):
            time.sleep(2)
            return True
        elif reponse in ("non", "no", "n"):
            print("Aborted.")
            exit()
        else:
            print("Veuillez répondre par 'oui' ou 'non'.")

def drop_stage():
    surface_alt = vessel.flight().surface_altitude
    engaged_alt = surface_alt + 100
    engaged = False
    dropped = False

    while not engaged:
        altitude = vessel.flight().mean_altitude
        if altitude > engaged_alt:
            engaged = True
            logger.info("Stage Dropper - Engaged")
        time.sleep(0.1)

    while not dropped:
        fuelAmount = vessel.resources_in_decouple_stage(vessel.control.current_stage - 1).amount('SolidFuel')
        if fuelAmount < 0.05:
            vessel.control.activate_next_stage()
            logger.info("Drop stage number {}.".format(vessel.control.current_stage))
            time.sleep(0.5)
            dropped = True
        time.sleep(0.1)

    logger.info("Stage Dropper - Released")

def tilt():
    vessel.auto_pilot.target_pitch_and_heading(60, 90)

if __name__ == '__main__':
    overview()
    confirm()

    # MAIN
    pool = [
        Process(target=telemetry_recorder),
        Process(target=parachute_handler),
    ]

    for bprocess in pool:
        bprocess.start()

    stability()

    launch()

    time.sleep(4)
    tilt()

    time.sleep(1)
    drop_stage()