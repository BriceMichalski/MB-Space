import time
from modules.ship import Ship

if __name__ == '__main__':

    # Missions
    ship = Ship()

    time.sleep(5)
    ship.start()


    ## Orbit
    ship.ascension_computer.setup(orbit_target_altitude=75000,turn_start_altitude=2500)
    ship.ascension_computer.engage()

    # # Launch
    # time.sleep(5)
    ship.launch()
