from gpyio import gpio

pin = gpio.export_pin(18, gpio.OUTPUT)
gpio.unexport_pin(pin)