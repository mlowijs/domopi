from avpy import fswebcam, mpg123
from gpyio import gpio
import os
from pathlib import Path
from pushbullet.client import Pushbullet
import signal
import time

from constants import *


def doorbell_pressed(pin, state):
    mpg123.play_sound(DOORBELL_FILE)

    now = time.localtime()
    image_path = "{}/Doorbell-{:.0f}.jpg".format(SNAPSHOT_DIR, time.mktime(now))

    fswebcam.save_image(image_path)
    pb.push_file(image_path, time.strftime("Doorbell was rung (%d-%m-%Y %H:%M:%S)", now))


def signal_handler(signal_number, frame):
    gpio.cleanup()


# Fork to run as a daemon
if os.fork() > 0:
    exit(0)

# Set signal handler
signal.signal(signal.SIGTERM, signal_handler)

# Create snapshot directory
snapshot_dir = Path(SNAPSHOT_DIR)

if not snapshot_dir.exists():
    snapshot_dir.mkdir(parents=True)

# Setup Pushbullet and the input pin
pb = Pushbullet(PUSHBULLET_API_KEY)

doorbell_pin = gpio.export_pin(18, gpio.INPUT)
doorbell_pin.set_resistor(gpio.RESISTOR_PULLUP)
doorbell_pin.monitor(doorbell_pressed, gpio.FALLING_EDGE)