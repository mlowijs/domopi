from array import array
import ctypes
import fcntl
import struct


class Spi:
    #
    # Setup and teardown
    #
    def __init__(self, device, port):
        self._bits_per_word = None
        self._cs_deselect_after_transfer = False
        self._delay = 0
        self._speed = None

        self._device = device
        self._port = port
        self._transfer_struct = struct.Struct("L L I I H B B I")

    #
    # Public methods
    #
    def set_bits_per_word(self, bits_per_word):
        self._bits_per_word = bits_per_word
        return self._do_ioctl(0x40016b03, array("L", [bits_per_word]))

    def set_mode(self, phase, polarity, cs_active_high=False, lsb_first=False):
        mode = int(phase) | int(polarity) << 1 | int(cs_active_high) << 2 | int(lsb_first) << 3
        return self._do_ioctl(0x40016b01, array("L", [mode]))

    def set_speed(self, speed):
        self._speed = speed
        return self._do_ioctl(0x40046b04, array("L", [speed]))

    def transfer(self, bytes_to_write):
        length = len(bytes_to_write)

        buffer_type = ctypes.c_byte * length

        tx_buffer = buffer_type()
        rx_buffer = buffer_type()

        for i in range(length):
            tx_buffer[i] = ctypes.c_byte(bytes_to_write[i])

        self._do_spi_transfer(tx_buffer, rx_buffer)

        return [b for b in rx_buffer]

    #
    # Private methods
    #
    def _do_ioctl(self, operation, argument):
        with open("/dev/spidev{0}.{1}".format(self._device, self._port), "wb") as fd:
            return fcntl.ioctl(fd, operation, argument)

    def _do_spi_transfer(self, tx_buffer, rx_buffer):
        s = SpiIocTransfer(ctypes.addressof(tx_buffer), ctypes.addressof(rx_buffer), len(tx_buffer), self._speed,
                           self._delay, self._bits_per_word, self._cs_deselect_after_transfer, 0)

        self._do_ioctl(0x40006b00 | (32 << 16), ctypes.addressof(s))


class SpiIocTransfer(ctypes.Structure):
    _fields_ = [("tx_buf", ctypes.c_uint64),
                ("rx_buf", ctypes.c_uint64),
                ("len", ctypes.c_uint32),
                ("speed_hz", ctypes.c_uint32),
                ("delay_usecs", ctypes.c_uint16),
                ("bits_per_word", ctypes.c_uint8),
                ("cs_change", ctypes.c_uint8),
                ("pad", ctypes.c_uint32)]