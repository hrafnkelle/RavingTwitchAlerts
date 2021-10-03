import logging
from os import path
from dataclasses import dataclass
import sqlite3

from rtree import index

from geolocation import GeoLocation

idx = index.Rtree('airports_idx.rtree')

@dataclass
class AirportLoc:
    ident: str
    loc: GeoLocation

def rebuildIdx():
    try:
        con = sqlite3.connect(path.expandvars(r'%APPDATA%\ABarthel\little_navmap_db\little_navmap_msfs.sqlite'))
        cur = con.cursor()
        cur.execute('SELECT airport_id, ident, left_lonx, right_lonx, top_laty, bottom_laty, laty, lonx FROM airport WHERE is_closed=0 AND is_addon=0')
        for row in cur:
            #print(row)
            airport_id, ident, left, right, top, bottom, laty, lonx = row
            idx.insert(airport_id, (left, bottom, right, top), obj=AirportLoc(ident=ident, loc=GeoLocation.from_degrees(laty, lonx)))
        con.close()
        logging.info("Done building spatial index")
    except Exception as e:
        logging.exception("Failed building index. Do you have Little Navmap installed and has it indexed the MSFS airports?")
        exit(-1)
        


def getClosestAirport(lat, lon, dist=100.0):
    somewhere = GeoLocation.from_degrees(lat or 0.0, lon or 0.0)
    sw, ne = somewhere.bounding_locations(dist)
    closest_dist = 100000000000000000000
    closest_airport = None
    for airport in idx.intersection((sw.deg_lon, sw.deg_lat, ne.deg_lon, ne.deg_lat), objects=True):
        dist = somewhere.distance_to(airport.object.loc)
        if dist < closest_dist:
            closest_airport = airport.object
            closest_dist = dist
    if closest_airport is not None:
        return closest_airport.ident, closest_dist
    else:
        return None, None

if __name__ == '__main__':
    rebuildIdx()
    reykjavik = GeoLocation.from_degrees(64.113, -21.727)
    ident, dist = getClosestAirport(reykjavik.deg_lat, reykjavik.deg_lon)
    print(f"{ident} is only {dist:.2f} km away")
