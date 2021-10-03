import time
import os
import airport
from SimConnect import *

#os.remove("airports_idx.rtree.dat")
#os.remove("airports_idx.rtree.idx")
airport.rebuildIdx()
connected = False

while not connected:
    try:
        sm = SimConnect()
        ae = AircraftEvents(sm)
        aq = AircraftRequests(sm, _time=10)
        connected = True
    except:
        print("No sim running?")
    time.sleep(2)

while True:
    try:
        lat = aq.get('PLANE_LATITUDE')
        lon = aq.get('PLANE_LONGITUDE')
        print(lat, lon)
        ident, dist = airport.getClosestAirport(lat, lon)
        with open('closestairport.txt','w') as f:
            print(ident)
            f.write(f"{ident}")
    except:
        print("Failed to get airport")

    time.sleep(2)
    
