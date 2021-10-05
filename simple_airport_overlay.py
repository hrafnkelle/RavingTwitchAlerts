import time
import os
import logging
import airport
from SimConnect import *

import pystray
import pyperclip

from PIL import Image, ImageDraw

logging.basicConfig(filename='overlay.log', encoding='utf-8', level=logging.DEBUG)

sm: SimConnect = None
ae: AircraftEvents = None
aq: AircraftRequests = None

running = True
connected = False

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

def path_to_clipboard():
    cwd = os.getcwd()
    pyperclip.copy(os.path.join(cwd,"closestairport.txt"))
    print(pyperclip.paste())

def connectToSim():
    global sm
    global ae
    global aq
    global icon
    global connected
    try:
        sm = SimConnect()
        ae = AircraftEvents(sm)
        aq = AircraftRequests(sm, _time=10)
        connected = True
    except:
        icon.title = "No sim running?"
        logging.exception("No sim running?")
        connected = False
    return connected

menu = pystray.Menu(pystray.MenuItem("Copy airport file path to clipboard", path_to_clipboard),
                    pystray.MenuItem("Reconnect to MSFS", connectToSim), 
                    pystray.MenuItem("Quit", stop ))
icon = pystray.Icon('AirportOverlay', menu = menu)



def setup(icon):
    global connected
    connected = False
    icon.icon = img = create_image()
    icon.visible = True

    icon.title = "Rebuilding airport index"
    airport.rebuildIdx()

    connected = connectToSim()

    while running:
        if connected:
            ident = ""
            dist_nm = 0.0
            try:
                lat = aq.get('PLANE_LATITUDE')
                lon = aq.get('PLANE_LONGITUDE')
                ident, dist = airport.getClosestAirport(lat, lon)
                dist_nm = dist*0.53996
                icon.title = f"{ident} is {dist_nm:.2f} NM away"
            except Exception as e:
                icon.title = "Failed to get airport"
                logging.exception("Failure while getting airport")
            with open('closestairport.txt','w') as f:
                f.write(f"{ident}")

        time.sleep(2)

    with open('closestairport.txt','w') as f:
        f.write(f"")



icon.run(setup=setup)