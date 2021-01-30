from time import sleep
import signal
import RPi.GPIO as gpio

EN = 21
DIR = 20
STEP = 16
CW = 1
CCW = 0

class motor_driver:
    tick = -1
    tick_goal = 0
    pin_state = 0
    def __init__(self):
        #gpio.setmode(gpio.BCM)
        gpio.setup(DIR, gpio.OUT)
        gpio.setup(STEP, gpio.OUT)
        gpio.output(DIR, CW)

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
        print("motor icin sure ve tick sayisi hesaplandi")
        mm_per_tick = 180
        # 60mm için 60*180 tick
        ticks = speed * mm_per_tick
        time = 1/(ticks/60) # 0.003
        time = round(time, 3)
        return time, ticks, direction
    def motor_run(self, time, ticks, direction):

        gpio.output(DIR, direction)
        self.tick_goal = ticks
        signal.signal(signal.SIGALRM, self.handler)
        signal.setitimer(signal.ITIMER_REAL, time, time)
        print("motor timer ayarlandi")

    def handler(self, signum, _):
        self.send_tick(self.tick_goal)

    def send_tick(self, ticks):
        # change it to pin_status != pin_status
        # gpio.input(pin)
        print("timer sinyal verdi")
        if self.tick > 0: # countdown the ticks
            self.tick = self.tick - 1
        elif self.tick == -1: # if tick counter is reset set the counter
            self.tick = ticks
        elif self.tick == 0:
            signal.setitimer(signal.ITIMER_REAL, 0, 0) # if ticks done stop timer
            self.tick = -1 # reset counter

        pin_state = gpio.input(STEP)
        if pin_state == 1:
            gpio.output(STEP, gpio.LOW) # output the reverse state to turn motor
            print("motor 0")
        else:
            gpio.output(STEP, gpio.HIGH)
            print("motor 1")

"""
# Main body of code
try:
    while True:
        sleep(1)
        gpio.output(DIR, CW)
        for x in range(400):
            gpio.output(STEP, gpio.HIGH)
            sleep(.0005)
            gpio.output(STEP, gpio.LOW)
            sleep(.0005)

        sleep(1)
        gpio.output(DIR, CCW)
        for x in range(400):
            gpio.output(STEP, gpio.HIGH)
            sleep(.0010)
            gpio.output(STEP, gpio.LOW)
            sleep(.0010)




except KeyboardInterrupt:  # If there is a KeyboardInterrupt (when you press ctrl+c), exit the program and cleanup
    print("Cleaning up!")
    gpio.cleanup()
"""