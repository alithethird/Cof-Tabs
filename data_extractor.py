import RPi.GPIO as gpio
gpio.setmode(gpio.BCM)
from hx711 import HX711
from time import sleep
hx = HX711(5, 6)
hx.set_reading_format("MSB", "MSB")
hx.reset()
hx.tare()

forces = [0]
global forces


def get_force():
    val = hx.get_weight(5)
    calib = 1  # kalibrasyon sayısı
    val /= calib
    forces.append(val)


for i in range(2000):
    get_force()
    sleep(0.005)
    print("data collecting")

print(forces)