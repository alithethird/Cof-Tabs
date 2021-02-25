import signal
import RPi.GPIO as gpio
import angle_read
import signal
from  threading import Thread
from time import sleep
import RPi.GPIO as gpio

import angle_read

IN1 = 26
IN2 = 19

EN = 26
DIR = 19
STEP = 13
CW = 1
CCW = 0


A_STEP = 16 # açı motoru için step
A_DIR = 20 # açı motoru için direction
A_EN = 21 # açı motoru için enable

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
        if self.soft:
            self.soft_thread = Thread(target=self.soft_start, args=(1, ))
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
            print("motor icin sure ve tick sayisi hesaplandi")
            mm_per_tick = 180  # kalibrasyon için
            # 60mm için 60*180 tick
            ticks = speed * mm_per_tick

            drive_time = (distance / speed) * 60

            frequency = ticks / 60

            frequency = round(frequency, 3)
            return drive_time, frequency, direction

        if self.select == 3 and not self.soft: # need to integrate soft start
            mm_per_second = 1
            drive_time = (distance / speed) * 60
            frequency = speed * mm_per_second
            frequency = round(frequency, 3)
            return drive_time, frequency, direction
        elif self.select == 3 and self.soft: #soft startta ilk x saniye yarı hızda çalışacak gibi hesaplanmalı
            mm_per_second = 1
            ramp_distance = (self.soft_time * speed) / 2
            drive_time = ((distance - ramp_distance) / speed) * 60
            drive_time += self.soft_time #
            frequency = 0
            return drive_time, frequency, direction




    def motor_run(self, drive_time, frequency, direction):
        if self.select == 1 or self.select == 2:
            gpio.output(DIR, direction)
            gpio.output(EN, 0)

            self.motor_pwm.ChangeFrequency(frequency)
            self.motor_pwm.start(50)
#            self.motor_pwm.ChangeDutyCycle()
            print("motor pwm ayarlandi")
            signal.signal(signal.SIGALRM, self.handler)
            signal.setitimer(signal.ITIMER_REAL, drive_time, 0)
            print("motor stop timer ayarlandi")
        if self.select == 3 and not self.soft:
            if direction == 1:
                gpio.output(IN1, 1)
                gpio.output(IN2, 0)
            elif direction == 0:
                gpio.output(IN1, 0)
                gpio.output(IN2, 1)
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
            gpio.output(DIR, direction)
            gpio.output(EN, 0)

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
            gpio.output(IN1, 0)
            gpio.output(IN2, 0)
        elif self.select == 3 and self.soft:
            try:
                self.output1_pwm.ChangeDutyCycle(0)
                self.output2_pwm.ChangeDutyCycle(0)
                self.output2_pwm.stop()
                self.output1_pwm.stop()
            except:
                pass
        print("motor pwm durduruldu")

    def set_angle_x(self, x):
        gpio.output(A_DIR, CW)

        self.angle_pwm.start(50)
        print("aci motoru pozitif yonde calismaya basladı")
        signal.signal(signal.SIGALRM, self.angle_slow_down)  # bu satır için mpu6050 lazım
        # signal.signal(signal.SIGALRM, self.angle_test) # test satırı
        signal.setitimer(signal.ITIMER_REAL, x, 0)
        print("aci motoru icin timer ayarlandi")

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

    def set_angle_30(self):
        angle = angle_read.get_rotation(
            1)  # açıyı okuyoruz, fonksiyon içine sayı almadan sayı döndürmüyor bu yüzden içeri 1 verdik, içeri verilen sayı işleme dahil edilmiyor istenen sayı verilebilir

        if angle >= 28 and angle <= 32:  # açıya ulaştı ise motor duruyor
            self.angle_pwm.stop()
        elif angle < 28:  # geride kaldı ise aradaki farka oranlı bir hızda ileri dönüyor
            gpio.output(A_DIR, CW)
            angle_freq = (angle - 30) * 10
            self.angle_pwm.ChangeFrequency(angle_freq)
        elif angle > 32:  # fazla gittiyse aradaki farka oranlı bir hızda geri dönüyor
            angle_freq = (30 - angle) * 10
            gpio.output(A_DIR, CCW)
            self.angle_pwm.ChangeFrequency(angle_freq)

    def set_angle_0(self):
        angle = angle_read.get_rotation(
            1)  # açıyı okuyoruz, fonksiyon içine sayı almadan sayı döndürmüyor bu yüzden içeri 1 verdik, içeri verilen sayı işleme dahil edilmiyor istenen sayı verilebilir

        if angle <= 2:  # açıya ulaştı ise motor duruyor
            self.angle_pwm.stop()
        elif angle > 2:  # fazla gittiyse aradaki farka oranlı bir hızda geri dönüyor
            angle_freq = angle * 10
            gpio.output(A_DIR, CCW)
            self.angle_pwm.ChangeFrequency(angle_freq)

    def angle_test(self, signum, _):

        self.angle_pwm.stop()
        print("aci motoru durduruldu")
        gpio.output(A_EN, 1)

    def angle_slow_down(self, signum, _):

        angle = angle_read.get_rotation(
            1)  # açıyı okuyoruz, fonksiyon içine sayı almadan sayı döndürmüyor bu yüzden içeri 1 verdik, içeri verilen sayı işleme dahil edilmiyor istenen sayı verilebilir

        if angle == 30:  # açıya ulaştı ise motor duruyor
            self.angle_pwm.stop()
        elif angle < 30:  # geride kaldı ise aradaki farka oranlı bir hızda ileri dönüyor
            gpio.output(A_DIR, CW)
            angle_freq = (angle - 30) * 10
            self.angle_pwm.ChangeFrequency(angle_freq)
        elif angle > 30:  # fazla gittiyse aradaki farka oranlı bir hızda geri dönüyor
            angle_freq = (30 - angle) * 10
            gpio.output(A_DIR, CCW)
            self.angle_pwm.ChangeFrequency(angle_freq)

    def send_tick(self, ticks):
        # change it to pin_status != pin_status
        # gpio.input(pin)
        print("timer sinyal verdi")
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
            print("motor 0")
        else:
            gpio.output(STEP, gpio.HIGH)
            print("motor 1")
