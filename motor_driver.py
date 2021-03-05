import signal
import RPi.GPIO as gpio
# import angle_read
import signal
from threading import Thread
from time import sleep
import RPi.GPIO as gpio

# import angle_read

IN1 = 26
IN2 = 19

EN = 26
DIR = 19
STEP = 13
CW = 1
CCW = 0

A_STEP = 16  # açı motoru için step
A_DIR = 20  # açı motoru için direction
A_EN = 21  # açı motoru için enable


class motor_driver:
    # select
    # 1- sadece 1 adet step motor
    # 2- bi normal(step) 1 açı motoru(step)
    # 3- bir adet dc motor 1 adet açı -(step)
    # soft
    # True = soft start
    # False = no soft start

    def __init__(self, select, soft):
        self.soft = soft
        self.select = select
        self.soft_time = 1
        self.max_speed = 200
        if select == 1:
            tick = -1
            tick_goal = 0
            pin_state = 0
            gpio.setup(EN, gpio.OUT)
            gpio.setup(DIR, gpio.OUT)
            gpio.setup(STEP, gpio.OUT)
            gpio.output(DIR, CW)

            self.motor_pwm = gpio.PWM(STEP, 100)

        if select == 2:
            tick = -1
            tick_goal = 0
            pin_state = 0
            gpio.setup(EN, gpio.OUT)
            gpio.setup(DIR, gpio.OUT)
            gpio.setup(STEP, gpio.OUT)
            gpio.output(DIR, CW)

            gpio.setup(A_EN, gpio.OUT)
            gpio.setup(A_STEP, gpio.OUT)
            gpio.setup(A_DIR, gpio.OUT)

            self.motor_pwm = gpio.PWM(STEP, 100)
            self.angle_pwm = gpio.PWM(A_STEP, 1000)
        if select == 3:
            gpio.setup(IN1, gpio.OUT)
            gpio.setup(IN2, gpio.OUT)
            self.output1_pwm = gpio.PWM(IN1, 1000)
            self.output2_pwm = gpio.PWM(IN2, 1000)
        if self.soft:
            self.soft_thread = Thread(target=self.soft_start, args=(1,))
            pass

    def run_standard_test(self):
        distance, speed, direction = self.calculate_ticks(60, 150, 1)
        self.motor_run(distance, speed, direction)

    def calculate_ticks(self, distance=60, speed=150, direction=1):
        if self.select == 1 or self.select == 2:
            # speed decided in the standard ISO 8295 is 100mm/min
            # travel distance decided by me is 60 mm
            # vida aralığı 2mm
            # 1 tick 1 derece olsa :D
            # 180 tick 1 mm
            # dakikada 100 mm için 18000 tick
            # saniyede 300 tick
            # 0.003 saniyede 1 tick
            mm_per_tick = 180  # kalibrasyon için
            # 60mm için 60*180 tick
            ticks = speed * mm_per_tick

            drive_time = (distance / speed) * 60

            frequency = ticks / 60

            frequency = round(frequency, 3)
            return drive_time, frequency, direction

        if self.select == 3 and not self.soft:  # need to integrate soft start
            mm_per_second = 1
            drive_time = (distance / speed) * 60
            duty_cycle = (speed / self.max_speed) * 100
            duty_cycle = round(duty_cycle, 3)
            return drive_time, duty_cycle, direction
        elif self.select == 3 and self.soft:  # soft startta ilk x saniye yarı hızda çalışacak gibi hesaplanmalı
            mm_per_second = 1
            ramp_distance = (self.soft_time * speed) / 2
            drive_time = ((distance - ramp_distance) / speed) * 60
            drive_time += self.soft_time  #
            duty_cycle = (speed / self.max_speed) * 100
            duty_cycle = round(duty_cycle, 3)
            return drive_time, duty_cycle, direction

    def motor_run(self, drive_time, frequency, direction):
        if self.select == 1 or self.select == 2:
            gpio.output(EN, 0)
            sleep(0.000005)
            gpio.output(DIR, direction)
            sleep(0.000005)
            self.motor_pwm.ChangeFrequency(frequency)
            self.motor_pwm.start(50)
            #            self.motor_pwm.ChangeDutyCycle()
            signal.signal(signal.SIGALRM, self.handler)
            signal.setitimer(signal.ITIMER_REAL, drive_time, 0)
        if self.select == 3 and not self.soft:
            if direction == 1:
                self.output1_pwm.start(frequency)
            elif direction == 0:
                self.output2_pwm.start(frequency)
        if self.select == 3 and self.soft:
            self.soft_thread.start()

    def soft_start(self, pwm_value):
        if self.select == 3:
            while pwm_value < 100:
                if self.direction == 1:
                    if pwm_value == 1:
                        self.output1_pwm.start(pwm_value)
                    else:
                        self.output1_pwm.ChangeDutyCycle(pwm_value)
                else:
                    if pwm_value == 1:
                        self.output2_pwm.start(pwm_value)
                    else:
                        self.output2_pwm.ChangeDutyCycle(pwm_value)
                pwm_value += 1
                sleep(self.soft_time / 100)
        else:
            pass

    def motor_start(self, frequency, direction):
        if self.select == 1 or self.select == 2:
            gpio.output(EN, 0)
            sleep(0.000005)
            gpio.output(DIR, direction)
            sleep(0.000005)

            self.motor_pwm.ChangeFrequency(frequency)
            self.motor_pwm.start(50)
        elif self.select == 3:
            if direction == 1:
                gpio.output(IN1, 1)
                gpio.output(IN2, 0)
            elif direction == 0:
                gpio.output(IN1, 0)
                gpio.output(IN2, 1)

    def handler(self, signum, _):
        self.stop_motor()

    def stop_motor(self):
        if self.select == 1 or self.select == 2:
            self.motor_pwm.stop()
            gpio.output(EN, 1)
        elif self.select == 3 and not self.soft:
            self.output2_pwm.stop()
            self.output1_pwm.stop()
        elif self.select == 3 and self.soft:
            try:
                self.output2_pwm.stop()
                self.output1_pwm.stop()
            except:
                pass

    def set_angle_x(self, x):
        gpio.output(A_DIR, CW)

        self.angle_pwm.start(50)
        signal.signal(signal.SIGALRM, self.angle_slow_down)  # bu satır için mpu6050 lazım
        # signal.signal(signal.SIGALRM, self.angle_test) # test satırı
        signal.setitimer(signal.ITIMER_REAL, x, 0)

    def start_angle_motor_rise(self, frequency=1000):
        gpio.output(A_DIR, CW)
        gpio.output(A_EN, 0)
        self.angle_pwm.ChangeFrequency(frequency)
        self.angle_pwm.start(50)

    def start_angle_motor_fall(self, frequency=1000):
        gpio.output(A_DIR, CCW)
        gpio.output(A_EN, 0)

        self.angle_pwm.ChangeFrequency(frequency)
        self.angle_pwm.start(50)

    def stop_angle_motor(self):
        self.angle_pwm.stop()
        gpio.output(A_EN, 1)

    def angle_test(self, signum, _):

        self.angle_pwm.stop()
        gpio.output(A_EN, 1)

    def send_tick(self, ticks):
        # change it to pin_status != pin_status
        # gpio.input(pin)
        if self.tick > 0:  # countdown the ticks
            self.tick = self.tick - 1
        elif self.tick == -1:  # if tick counter is reset set the counter
            self.tick = ticks
        elif self.tick == 0:
            signal.setitimer(signal.ITIMER_REAL, 0, 0)  # if ticks done stop timer
            self.tick = -1  # reset counter

        pin_state = gpio.input(STEP)
        if pin_state == 1:
            gpio.output(STEP, gpio.LOW)  # output the reverse state to turn motor
        else:
            gpio.output(STEP, gpio.HIGH)
