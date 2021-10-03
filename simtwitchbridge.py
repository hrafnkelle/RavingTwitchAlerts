import logging
import random
from SimConnect import *
import yaml

class SimTwitchBridge:
    req = [
        'PLANE_ALTITUDE',
        'PLANE_LATITUDE',
        'PLANE_LONGITUDE',
        'AIRSPEED_INDICATED',
        'GROUND_VELOCITY',
        'FUEL_TOTAL_CAPACITY',
        'FUEL_TOTAL_QUANTITY',
        'MAGNETIC_COMPASS',
        'VERTICAL_SPEED',
        'TOTAL_AIR_TEMPERATURE',
        'AMBIENT_TEMPERATURE',
        'SIM_ON_GROUND'
    ]

    def __init__(self):
        self.sm:SimConnect = None
        self.ae = None
        self.aq = None
        self.connected = False
        self.rewards = {}

        with open("rewards.yaml", "r") as stream:
            try:
                rewards = yaml.load(stream, Loader=yaml.FullLoader)
                for name, id in rewards['rewards'].items():
                    print(f"{name}: {id}")
                    try:
                        id_handler = getattr(self, name)
                        self.rewards[id] = id_handler
                    except AttributeError:
                        logging.warning(f"Trying to register {id} for unknown method {name}")
            except yaml.YAMLError as exc:
                print(exc)

        self.tryConnect()

    def tryConnect(self):
        try:
            self.sm = SimConnect()
            self.ae = AircraftEvents(self.sm)
            self.aq = AircraftRequests(self.sm, _time=10)
            self.connected = True
        except OSError:
            self.connected = False
        return self.connected

    def trigger_event(self, event_name, value_to_use = None):
        # This function actually does the work of triggering the event

        EVENT_TO_TRIGGER = self.ae.find(event_name)
        if EVENT_TO_TRIGGER is not None:
            if value_to_use is None:
                EVENT_TO_TRIGGER()
            else:
                EVENT_TO_TRIGGER(int(value_to_use))

            status = "success"
        else:
            status = "Error: %s is not an Event" % (event_name)

        return status

    def doReward(self, id):
        if id in self.rewards:
            self.rewards[id]()
        else:
            logging.warning(f"Trying to doReward on id {id} with no registered handler")

    def addFuel(self):
        fuel_left_capacity = self.aq.get("FUEL_TANK_LEFT_MAIN_CAPACITY")
        fuel_right_capacity = self.aq.get("FUEL_TANK_RIGHT_MAIN_CAPACITY")
        current_fuel_left = self.aq.get("FUEL_TANK_LEFT_MAIN_QUANTITY")
        current_fuel_right = self.aq.get("FUEL_TANK_RIGHT_MAIN_QUANTITY")
        new_fuel_left = current_fuel_left + fuel_left_capacity*0.05
        new_fuel_right = current_fuel_right + fuel_right_capacity*0.05
        self.aq.set("FUEL_TANK_LEFT_MAIN_QUANTITY", new_fuel_left)
        self.aq.set("FUEL_TANK_RIGHT_MAIN_QUANTITY", new_fuel_right)

    def dumpFuel(self):
        fuel_left_capacity = self.aq.get("FUEL_TANK_LEFT_MAIN_CAPACITY")
        fuel_right_capacity = self.aq.get("FUEL_TANK_RIGHT_MAIN_CAPACITY")
        current_fuel_left = self.aq.get("FUEL_TANK_LEFT_MAIN_QUANTITY")
        current_fuel_right = self.aq.get("FUEL_TANK_RIGHT_MAIN_QUANTITY")
        new_fuel_left = current_fuel_left - fuel_left_capacity*0.05
        new_fuel_right = current_fuel_right - fuel_right_capacity*0.05
        self.aq.set("FUEL_TANK_LEFT_MAIN_QUANTITY", new_fuel_left)
        self.aq.set("FUEL_TANK_RIGHT_MAIN_QUANTITY", new_fuel_right)

    def turnAPOff(self):
        logging.info("Turning AP off")
        self.trigger_event("AUTOPILOT_OFF")
    
    def toggleLeftBrakeFailure(self):
        logging.info("Toggle left break failure")
        self.trigger_event("TOGGLE_LEFT_BRAKE_FAILURE")

    def toggleAlternator(self):
        logging.info("Toggling alternator")
        self.trigger_event("TOGGLE_MASTER_ALTERNATOR")

    def toggleEngineFailure(self):
        logging.info("Toggling engine failure")
        self.trigger_event("TOGGLE_ENGINE1_FAILURE")

    def toggleElectricalFailure(self):
        logging.info("Toggling electrical failure")
        self.trigger_event("TOGGLE_ELECTRICAL_FAILURE")

    def shutdownEngine(self):
        if random.random() < 0.3333:
            logging.info("Engine shutdown: Win!")
            self.trigger_event('ENGINE_AUTO_SHUTDOWN')
        else:
            logging.info("Engine shutdown: better luck next time")        
    
    def changeMixture(self):
        mixture = random.uniform(0.2, 1.0)
        self.trigger_event('MIXTURE_SET', int(mixture*16383))
        logging.info(f"Changing mixture to {int(mixture*100)}")

    def getFlightStatusVars(self):
        dataset = {'connected': False}
        try:
            if not self.connected:
                connected = self.tryConnect()
            if self.connected:
                for var in SimTwitchBridge.req:
                    dataset[var] = self.aq.get(var)
                dataset['connected'] = True
            return dataset
        except OSError:
            logging.debug("Flightim connection lost")
            self.connected = False
