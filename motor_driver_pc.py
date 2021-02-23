from time import sleep
# import RPi.GPIO as gpio

EN = 26
DIR = 19
STEP = 13
CW = 1
CCW = 0

A_STEP = 16 # açı motoru için step
A_DIR = 20 # açı motoru için direction
A_EN = 21 # açı motoru için enable

class motor_driver_pc:
    tick = -1
    tick_goal = 0
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
        print("motor icin sure ve tick sayisi hesaplandi")
        mm_per_tick = 180
        # 60mm için 60*180 tick
        ticks = speed * mm_per_tick

        drive_time = (distance / speed)*60

        frequency = ticks/60

        frequency = round(frequency, 3)
        return drive_time, frequency, direction

    def motor_run(self, time, ticks, direction):

        print("motor pwm ayarlandi")
        print("motor stop timer ayarlandi")
    def stop_motor(self):
        print("Motor stopped!")

    def handler(self, signum, _):
        self.stop_motor()



    def angle_test(self, signum, _):

        print("aci motoru durduruldu")

    def angle_slow_down(self, signum, _):

        angle = self.gyro_data()  # açıyı okuyoruz
        if angle == 30:  # açıya ulaştı ise motor duruyor
            print("açıya ulaştı açı motoru duruyor")
        elif angle < 30:  # geride kaldı ise aradaki farka oranlı bir hızda ileri dönüyor
            print("geride kaldı açı motoru oranlı ileri dönüyor")
        elif angle > 30:  # fazla gittiyse aradaki farka oranlı bir hızda geri dönüyor
            print("ileride kaldı açı motoru oranlı geri dönüyor")

    def start_angle_motor_rise(self, frequency=1000):
        pass
    def start_angle_motor_fall(self, frequency=1000):
        pass
    def gyro_data(self):
        return 30
