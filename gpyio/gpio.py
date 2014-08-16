from os import path
from threading import Thread
from time import sleep

INPUT = 0
OUTPUT = 1

FALLING_EDGE = 0
RISING_EDGE = 1
BOTH_EDGES = 2

_exported_pins = []


class Pin:
    def __init__(self, number, direction):
        self._direction = direction
        self._name = "Pin {}".format(number)
        self._number = number
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
        """ Set the state of a pin, i.e. on (True) or off (False). """

        if self._direction == INPUT:
            raise IOError("Pin {} is exported as an input".format(self.get_number()))

        with open("/sys/class/gpio/gpio{}/value".format(self._number), "w") as f:
            f.write("1" if state else "0")

        self._state = bool(state)

    def monitor(self, callback, edge=BOTH_EDGES):
        """ Monitors a pin's state and calls the callback when it changes. """

        if self.get_direction() == OUTPUT:
            raise ValueError("Pin {} is exported as an output".format(self.get_number()))

        if self._monitoring:
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

        while True:
            if not self._monitoring:
                break

            new_state = self.get_state()

            if new_state != old_state:
                if edge in [new_state, BOTH_EDGES]:
                    callback(self, new_state)
                sleep(0.15)  # Wait 150 ms for debounce

            old_state = new_state


def export_pin(number, direction):
    """ Exports a pin for use as GPIO if it isn't and returns a Pin object. """

    if any(pin for pin in _exported_pins if pin.get_number() == number):
        raise ValueError("Pin {} is already exported".format(number))

    pin = Pin(number, direction)
    _exported_pins.append(pin)

    if not path.exists("/sys/class/gpio/gpio{}".format(number)):
        with open("/sys/class/gpio/export", "w") as f:
            f.write(str(number))

    with open("/sys/class/gpio/gpio{}/direction".format(number), "w") as f:
        f.write("out" if direction == OUTPUT else "in")

    return pin


def unexport_pin(pin):
    """ Stops monitoring of a Pin and unexports it. """

    if pin.is_monitoring():
        pin.stop_monitoring()

    with open("/sys/class/gpio/unexport", "w") as f:
        f.write(str(pin.get_number()))

    _exported_pins.remove(pin)


def cleanup():
    """ Calls unexport_pin for every exported pin. """

    for pin in _exported_pins:
        unexport_pin(pin)