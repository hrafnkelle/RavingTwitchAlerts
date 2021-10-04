import time
import os
import logging
import airport
from SimConnect import *

import pystray

from PIL import Image, ImageDraw

logging.basicConfig(filename='overlay.log', encoding='utf-8', level=logging.DEBUG)

running = True
with open('closestairport.txt','w') as f:
    f.write(f"")

def create_image():
    width = 128
    height = width
    # Generate an image and draw a pattern
    color1 = "red"
    color2 = "blue"
    image = Image.new('RGB', (width, height), color1)
    dc = ImageDraw.Draw(image)
    dc.rectangle(
        (width // 2, 0, width, height // 2),
        fill=color2)
    dc.rectangle(
        (0, height // 2, width // 2, height),
        fill=color2)

    return image

def stop():
    global running
    running = False
    icon.stop()

menu = pystray.Menu(pystray.MenuItem("Quit", stop ))
icon = pystray.Icon('AirportOverlay', menu = menu)


def setup(icon):
    connected = False
    icon.icon = img = create_image()
    icon.visible = True

    icon.title = "Rebuilding airport index"
    airport.rebuildIdx()
    while running and not connected:
        try:
            sm = SimConnect()
            ae = AircraftEvents(sm)
            aq = AircraftRequests(sm, _time=10)
            connected = True
        except:
            icon.title = "No sim running?"
            logging.exception("No sim running?")
        time.sleep(2)


    while running:
        try:
            lat = aq.get('PLANE_LATITUDE')
            lon = aq.get('PLANE_LONGITUDE')
            ident, dist = airport.getClosestAirport(lat, lon)
            dist_nm = dist*0.53996
            with open('closestairport.txt','w') as f:
                icon.title = f"{ident} is {dist:.2f} NM away"
                f.write(f"{ident}")
        except Exception as e:
            icon.title = "Failed to get airport"
            logging.exception("Failure while getting airport")

        time.sleep(2)

        with open('closestairport.txt','w') as f:
            f.write(f"")



icon.run(setup=setup)