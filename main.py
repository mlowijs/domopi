from gpyio import gpio
from pushbullet.client import Pushbullet
import time


def doorbell_pressed(pin, state):
    pb.push_note("Doorbell pressed", time.strftime("Time: %H:%m:%S"))


pb = Pushbullet("v1TiTlSs2yJMAlkkyvyC2j9RpbZNrVmulgujyXFSvH0zA")

doorbell_pin = gpio.export_pin(18, gpio.INPUT)
doorbell_pin.monitor(doorbell_pressed, gpio.RISING_EDGE)

try:
    while True:
        pass
except KeyboardInterrupt:
    gpio.cleanup()