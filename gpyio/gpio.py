import mmap
import os
import sys
from threading import Thread
from time import sleep

INPUT = 0
OUTPUT = 1

FALLING_EDGE = 0
RISING_EDGE = 1
BOTH_EDGES = 2

RESISTOR_OFF = 0
RESISTOR_PULLDOWN = 1
RESISTOR_PULLUP = 2

GPIO_BASE = 0x20200000
GPPUD = 0x94
GPPUDCLK0 = 0x98

_exported_pins = []
_gpio_map = None


class Mmap2(mmap.mmap):
    def write_as_bytes(self, number, pos=0):
        self.seek(pos, os.SEEK_SET)
        self.write(number.to_bytes(4, sys.byteorder))


class Pin:
    def __init__(self, number, direction):
        self._direction = direction
        self._name = "Pin {}".format(number)
        self._number = number
        self._resistor_mode = RESISTOR_OFF
        self._state = None

        self._monitor_thread = None
        self._monitoring = False

    def __str__(self):
        return self.get_name()

    def __eq__(self, other):
        return self.get_number() == other.get_number()

    def get_direction(self):
        return self._direction

    def get_name(self):
        return self._name

    def get_number(self):
        return self._number

    def get_resistor_mode(self):
        return self._resistor_mode

    def get_state(self):
        if self.get_direction() == OUTPUT and not self.get_state() is None:
            return self._state

        with open("/sys/class/gpio/gpio{}/value".format(self._number), "r") as f:
            self._state = True if f.read(1) == "1" else False

        return self._state

    def is_monitoring(self):
        return self._monitoring

    def set_name(self, name):
        self._name = name

    def set_state(self, state):
        """ Sets the state of the pin, i.e. on (True) or off (False). """

        if self.get_direction() == INPUT:
            raise IOError("Pin {} is exported as an input".format(self.get_number()))

        with open("/sys/class/gpio/gpio{}/value".format(self._number), "w") as f:
            f.write("1" if state else "0")

        self._state = bool(state)

    def set_resistor(self, resistor_mode):
        """ Enables or disables the pin's pull-up/down resistor. """

        if self.get_direction() == OUTPUT:
            raise IOError("Pin {} is exported as an output".format(self.get_number()))

        # Write direction to GPPUD and sleep
        _gpio_map.write_as_bytes(resistor_mode, GPPUD)
        sleep(0.1)

        # Write pin number to GPPUDCLK0 and sleep
        _gpio_map.write_as_bytes(1 << self.get_number(), GPPUDCLK0)
        sleep(0.1)

        # Clear GPPUD and GPPUDCLK0
        _gpio_map.write_as_bytes(0, GPPUD)
        _gpio_map.write_as_bytes(0, GPPUDCLK0)

        self._resistor_mode = resistor_mode

    def monitor(self, callback, edge=BOTH_EDGES):
        """ Monitors the pin's state and calls the callback when it changes. """

        if self.get_direction() == OUTPUT:
            raise ValueError("Pin {} is exported as an output".format(self.get_number()))

        if self.is_monitoring():
            raise ValueError("This pin is already being monitored")

        self._monitoring = True
        self._monitor_thread = Thread(target=self._do_monitor_state, args=(callback, edge), daemon=False)
        self._monitor_thread.start()

    def stop_monitoring(self):
        self._monitoring = False

    #
    # Private methods
    #
    def _do_monitor_state(self, callback, edge):
        old_state = self.get_state()

        while self.is_monitoring():
            new_state = self.get_state()

            if new_state != old_state:
                if edge in (new_state, BOTH_EDGES):
                    callback(self, new_state)

                sleep(0.15)  # Wait 150 ms for debounce

            old_state = new_state


def export_pin(number, direction):
    """ Exports a pin for use as GPIO if it isn't and returns a Pin object. """
    if _gpio_map is None:
        _initialize()

    if any(pin for pin in _exported_pins if pin.get_number() == number):
        raise ValueError("Pin {} is already exported".format(number))

    pin = Pin(number, direction)
    _exported_pins.append(pin)

    if not os.path.exists("/sys/class/gpio/gpio{}".format(number)):
        with open("/sys/class/gpio/export", "w") as f:
            f.write(str(number))

    with open("/sys/class/gpio/gpio{}/direction".format(number), "w") as f:
        f.write("out" if direction == OUTPUT else "in")

    return pin


def unexport_pin(pin):
    """ Stops monitoring of a Pin, disables the resistor and unexports it. """

    if pin.is_monitoring():
        pin.stop_monitoring()

    if not pin.get_resistor_mode() == RESISTOR_OFF:
        pin.set_resistor(RESISTOR_OFF)

    with open("/sys/class/gpio/unexport", "w") as f:
        f.write(str(pin.get_number()))

    _exported_pins.remove(pin)


def cleanup():
    """ Calls unexport_pin for every exported pin and closes the GPIO mmap. """

    for pin in _exported_pins:
        unexport_pin(pin)

    if not _gpio_map is None:
        _gpio_map.close()


def _initialize():
    global _gpio_map

    fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
    _gpio_map = Mmap2(fd, 4096, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE, offset=GPIO_BASE)
    os.close(fd)