import time
from modules.flight import Ship

if __name__ == '__main__':

    # Missions
    ship = Ship()

    time.sleep(5)
    ship.start()
    ship.prepare()

    time.sleep(5)
    ship.launch()
