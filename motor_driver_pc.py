from time import sleep
import signal
# import RPi.GPIO as gpio

EN = 21
DIR = 20
STEP = 16
CW = 1
CCW = 0

class motor_driver_pc:

    def __init__(self):
        #gpio.setmode(gpio.BCM)
        #gpio.setup(DIR, gpio.OUT)
        #gpio.setup(STEP, gpio.OUT)
        #gpio.output(DIR, CW)
        tick = -1
        pin_state = 0
    def run_standard_test(self):
        time, ticks, direction = self.calculate_ticks(60, 100, 1)
        self.motor_run(time, ticks, direction)

    def calculate_ticks(self, distance = 60, speed = 100, direction = 1):
        # speed decided in the standard ISO 8295 is 100mm/min
        # travel distance decided by me is 60 mm
        # vida aralığı 2mm
        # 1 tick 1 derece olsa :D
        # 180 tick 1 mm
        # dakikada 100 mm için 18000 tick
        # saniyede 300 tick
        # 0.003 saniyede 1 tick

        mm_per_tick = 180
        # 60mm için 60*180 tick
        ticks = speed * mm_per_tick
        time = 1/(ticks/60) # 0.003
        time = round(time, 3)
        return time, ticks, direction
    def motor_run(self, time, ticks, direction):

        #gpio.output(DIR, direction)

        signal.signal(signal.SIGALRM, lambda: self.send_tick(ticks))
        signal.setitimer(signal.ITIMER_REAL, time, time)

    def send_tick(self, ticks):
        # change it to pin_status != pin_status
        # gpio.input(pin)

        if self.tick > 0: # countdown the ticks
            self.tick = self.tick - 1
        elif self.tick == -1: # if tick counter is reset set the counter
            self.tick = ticks
        elif self.tick == 0:
            signal.setitimer(signal.ITIMER_REAL, 0, 0) # if ticks done stop timer
            self.tick = -1 # reset counter

        self.pin_state = not self.pin_state
        if self.pin_state == 1:
            print(0)
            self.pin_state = 0
        else:
            print(1)
            self.pin_state = 1
