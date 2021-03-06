import datetime
import os

os.environ['KIVY_GL_BACKEND'] = 'gl'
from math import cos, pow, radians, sin, tan
import threading
from time import sleep
import RPi.GPIO as gpio
import signal
from kivy.config import Config

gpio.cleanup()
gpio.setwarnings(False)
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Config.set('kivy', 'keyboard_mode', 'systemanddock')
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy_garden.graph import MeshLinePlot
from kivy.uix.popup import Popup
from kivy.uix.floatlayout import FloatLayout

# import angle_read
from fpdf_handler import fpdf_handler

gpio.setmode(gpio.BCM)
from hx711 import HX711
from motor_driver import motor_driver
from json_dumper import JsonHandler

# set up the load cell

hx = HX711(5, 6)
hx.set_gain(128)  # bunun olması lazım
hx.reset()
# hx.tare()

start_switch = 23  # start kısmındaki switch
stop_switch = 25  # stop kısmındaki switch

gpio.setup(start_switch, gpio.IN, pull_up_down=gpio.PUD_UP)
gpio.setup(stop_switch, gpio.IN, pull_up_down=gpio.PUD_UP)

reset_motor_speed = 200
Builder.load_file('cof.kv')

angle_switch_start = 27  # açı motoru bu switch ile resetlenmeli
angle_switch_stop = 17  # açı motoru bu switche kadar çalışmalı

gpio.setup(angle_switch_start, gpio.IN, pull_up_down=gpio.PUD_UP)
gpio.setup(angle_switch_stop, gpio.IN, pull_up_down=gpio.PUD_UP)

md = motor_driver(2, False)  # bir adet dc bir adet açı(step) motor modu seçildi, soft start kapatıldı
json_handler = JsonHandler()
md.stop_motor()


class sample:
    name = ""
    width = 0
    height = 0
    age = 0
    testing_weight = 0
    company_name = ""
    operator_name = ""


test_mode = 0  # 0-motorized test
# 1-angle test

sample1 = sample()
sample2 = sample()

global normal_force  # üstte kayan metal malzemenin kütlesi (kg)
normal_force = 200
global test_angle
test_angle = 0
global forces
forces = [[0, 0]]
global angles
angles = [[0, 0]]
global ip_var
ip_var = False  # ip varsa True yoksa false
global angular_speed  # zamanı açıya çevirmek için açısal değer
angular_speed = 1

global calib  # kalibrasyon sayısı


def time_to_angle(angle_time):
    # return 73.85459 + (0.8731737 - 73.85459)/(1 + pow(((angle_time*0.6)/65.63023), 1.061611))
    # qubic from new data (fits a little bit better, RMSE = 3.173, R^2 = 0.9986 )
    return 0.0003434 * pow(angle_time, 3) - 0.03658 * pow(angle_time, 2) + 2.079 * angle_time - 0.1492
    # quadratic from new data ( RMSE = 3.595, R^2 = 0.9983)
    # return -0.02008*pow(angle_time, 2) + 1.872*angle_time + 0.367

def find_biggest(array):
    biggest = [0.1, 0.1]
    for i in array[:][:]:
        if i[1] > biggest[1]:
            biggest = i
        else:
            pass
    return biggest


def find_static_angle(forces):
    biggest = 0
    static_angle = 0
    for i in forces:
        if i[1] > biggest:
            biggest = i[1]
            static_angle = time_to_angle(i[0])
        else:
            pass
    return static_angle


def find_dynamic_force():
    # take last 20 elements of the list
    # find the median
    if len(forces) > 20:
        median = 0
        for i in range(20):
            median += forces[-(i + 1)][1]
        median /= 20
        return median
    else:
        return 1


def find_loose_string(
        array):  # finds loose string length and returns the amount of data acquired when the string is loose
    biggest = find_biggest(forces)
    index = int(((biggest[0] / sample_time)))
    count = 0
    for i in range(1, index):
        if forces[i - 1][1] == forces[i][1]:
            count += 1
    return count

    pass


def find_static_force_advanced():
    array = []
    array_mean = 0
    if ip_var:
        loose = find_loose_string(forces)
    else:
        loose = 0  # ip gergin değilken hesaplanan kuvvetlerin sayısı

    for i in range(loose, int(loose + (3 / sample_time))):
        array.append(forces[i])  # statik zamanda ölçülen kuvvet listesi
    
    _, max_static_force = find_biggest(array)
    for i in array:
        if i[1] == array[-1][1]:
            index = i[0]
    if index == 0:
        for i in array:
            if (array[-1][1] * 1.01) > i[1] > (array[-1][1] * 0.99):
                index = i[0]
    if index == 0:
        for i in array:
            if (array[-1][1] * 1.1) > i[1] > (array[-1][1] * 0.9):
                index = i[0]
    # start from index and calculate mean of array
    index = int(index / sample_time)

    for i in range(5, len(array)):
        array_mean += array[i][1]
    print("loose:", loose)
    print("index:", index)
    mean_static_force = array_mean / (len(array) - 5)

    return max_static_force, mean_static_force


def find_dynamic_force_advanced():
    if ip_var:
        loose = find_loose_string(forces)
        loose += int(1 / sample_time)
    else:
        loose = int(1 / sample_time)

    array = []
    array_mean = 0
    for i in range(int(loose + (3 / sample_time)), int(len(forces)*(6/10))):
        array_mean += forces[i][1]
        array.append(forces[i])

    _, max_dynamic_force = find_biggest(array)
    mean_dynamic_force = array_mean / len(array)

    return max_dynamic_force, mean_dynamic_force


class TarePop(FloatLayout):
    pass


class ScreenOne(Screen):
    def select_motorized_test(self):
        global test_mode
        test_mode = 0

    def select_angle_test(self):
        global test_mode
        test_mode = 1

    def btn_text(self):
        sample1.name = self.ids.first_name.text

        try:
            sample1.width = float(self.ids.first_width.text)
        except:
            sample1.width = 0.00

        try:
            sample1.height = float(self.ids.first_height.text)
        except:
            sample1.height = 0.00

        try:
            sample1.age = float(self.ids.first_age.text)
        except:
            sample1.age = 0.00

        sample1.company_name = self.ids.company_name.text
        sample1.operator_name = self.ids.operator_name.text
        sample1.testing_weight = normal_force

        if self.ids.switch.active:
            sample2.name = self.ids.second_name.text

            try:
                sample2.width = float(self.ids.second_width.text)
            except:
                sample2.width = 0.00

            try:
                sample2.height = float(self.ids.second_height.text)
            except:
                sample2.height = 0.00

            try:
                sample2.age = float(self.ids.second_age.text)
            except:
                sample2.age = 0.00

    def tare(self):
        hx.tare()

        self.show_popup()

    def show_popup(self):
        show = TarePop()
        self.popupWindow = Popup(title="Tare Completed", content=show, size_hint=(None, None), size=(400, 200))

        self.popupWindow.open()


class ScreenTwo(Screen):
    plot = MeshLinePlot(color=[1, 0, 0, 1])

    def __init__(self, **args):
        Screen.__init__(self, **args)
        self.is_reset = False

        global normal_force
        global sample_time
        global test_speed
        global test_distance
        global calib
        global angle_test_speed
        global angular_speed
        test_distance, test_speed, normal_force, sample_time, calib, angle_test_speed, angular_speed = json_handler.import_save()

    def start(self):

        try:
            gpio.remove_event_detect(stop_switch)
            gpio.cleanup(stop_switch)
        except:
            pass
        try:
            gpio.remove_event_detect(start_switch)
            gpio.cleanup(start_switch)
        except:
            pass
        global forces
        self.time_ = 0
        forces = [[0, 0]]
        self.ids.graph.remove_plot(self.plot)
        self.ids.graph.add_plot(self.plot)

        self.t = threading.Thread(target=self.get_force, args=("task",))
        self.t.start()

        #        signal.signal(signal.SIGALRM, self.timer)
        #        signal.setitimer(signal.ITIMER_REAL, 0.1, 1000)

        self.timer_thread = threading.Thread(target=self.timer, args=("task",))
        self.timer_thread.start()
        self.value_thread = threading.Thread(target=self.get_value, args=("task",))
        self.value_thread.start()
        self.ids.dist_current.text = "0"

        self.drive_time, frequency, direction = md.calculate_ticks(distance=test_distance, speed=test_speed, direction=0)
        md.motor_run(self.drive_time, frequency, direction)
      
        self.max_distance_event()

        return True

    def timer(self, arg):
        t = threading.currentThread()
        while getattr(t, "do_run", True):
            self.time_ = round(self.time_ + 0.12, 2)
            sleep(0.1)

    def get_force(self, arg):
        t = threading.currentThread()
        while getattr(t, "do_run", True):
            start_time = datetime.datetime.now()
            # sleep(sample_time)
            val = hx.get_weight()
            val *= calib
            if val < 0:
                val = 1

            if len(forces) > 1:
                forces.append([self.time_, val])
            else:
                forces.append([0, val])
            
            sleep_time = datetime.datetime.now() - start_time
            sleep_time = sleep_time.total_seconds()
            sleep_time = sample_time - sleep_time
            if sleep_time > 0:
                sleep(sleep_time)
            if self.time_ > (59):
                self.stop()

    def stop_event(self, channel):
        self.stop()
        return True

    def stop(self):

        try:
            self.value_thread.do_run = False
            self.value_thread.join()
            # self.reset()  # reset when test ends
        except:
            pass

        try:
            self.timer_thread.do_run = False
            self.timer_thread.join()
            # self.reset()  # reset when test ends
        except:
            pass
        self.time_ = 0
        try:
            self.t.do_run = False
            self.t.join()
            # self.reset()  # reset when test ends
        except:
            pass
        try:
            gpio.remove_event_detect(stop_switch)
            gpio.cleanup(stop_switch)
        except:
            pass
        
        try:
            gpio.remove_event_detect(start_switch)
            gpio.cleanup(start_switch)
        except:
            pass
        md.stop_motor()
        if self.is_reset:
            self.start()

    def reset(self):
        self.is_reset = False 
        gpio.setup(stop_switch, gpio.IN, pull_up_down=gpio.PUD_UP)
        if gpio.input(stop_switch):
            self.motor_forward()
            signal.signal(signal.SIGALRM, self.reset_)
            signal.setitimer(signal.ITIMER_REAL, 0.5, 0)
        else:
            self.reset_(1,1)

    def reset_(self, signum, _):
        self.is_reset = False
        #        Clock.unschedule(self.reset_)
        md.stop_motor()
        gpio.setup(start_switch, gpio.IN, pull_up_down=gpio.PUD_UP)
        if gpio.input(start_switch):
            self.motor_backward()
            self.min_distance_event()

    def save_graph(self):
        self.ids.graph.export_to_png("/home/pi/Cof-Tabs/graph.png")

    def get_value(self, arg):
        t = threading.currentThread()
        while getattr(t, "do_run", True):
            self.ids.dist_current.text = str(round(self.time_*1.66, 2))  # update current distance

            if forces[-1][0] == 0:
                self.ids.graph.xmax = 1
            elif forces[-1][0] > self.ids.graph.xmax:
                self.ids.graph.xmax = forces[-1][0]

            if len(forces) < 3:
                self.ids.graph.ymax = 1
            elif forces[-1][1] > self.ids.graph.ymax:
                self.ids.graph.ymax = (forces[-1][1] * 1.1)

            self.ids.graph.y_ticks_major = round(self.ids.graph.ymax / 11, -1)

            self.ids.graph.x_ticks_major = round(self.ids.graph.xmax, -1) * sample_time

            self.plot.points = forces

            sleep(0.1)

    def motor_forward(self):
        gpio.setup(stop_switch, gpio.IN, pull_up_down=gpio.PUD_UP)
        if gpio.input(stop_switch):
            self.max_distance_event()
            md.motor_start(8000, 0)

    def motor_backward(self):
        gpio.setup(start_switch, gpio.IN, pull_up_down=gpio.PUD_UP)
        if gpio.input(start_switch):
            self.min_distance_event()
            md.motor_start(8000, 1)

    def max_distance_event(self):
        try:
            gpio.setup(stop_switch, gpio.IN, pull_up_down=gpio.PUD_UP)
            gpio.add_event_detect(stop_switch, gpio.FALLING, callback=self.stop_event, bouncetime=200)
        except:
            pass

    def min_distance_event(self):
        try:
            gpio.setup(start_switch, gpio.IN, pull_up_down=gpio.PUD_UP)
            gpio.add_event_detect(start_switch, gpio.FALLING, callback=self.stop_event, bouncetime=200)
        except:
            pass


class P(FloatLayout):
    pass


class ScreenThree(Screen):
    date_today = datetime.date.today()
    date_text = str(date_today)

    def create_results(self):
        max_dynamic_cof, mean_dynamic_cof = self.find_dynamic_cof()
        max_static_cof, mean_static_cof = self.find_static_cof()
        return max_dynamic_cof, mean_dynamic_cof, max_static_cof, mean_static_cof

    def find_dynamic_cof(self):
        max_dynamic_force, mean_dynamic_force = find_dynamic_force_advanced()
        try:
            mean_dynamic_cof = mean_dynamic_force / (normal_force * 9.81)
            mean_dynamic_cof = round(mean_dynamic_cof, 3)

            max_dynamic_cof = max_dynamic_force / (normal_force * 9.81)
            max_dynamic_cof = round(max_dynamic_cof, 3)
        except TypeError:
            mean_dynamic_cof = "Testing Error (type Error)"
            max_dynamic_cof = "Testing Error (type Error)"
        except:
            mean_dynamic_cof = "Testing Error something"
            max_dynamic_cof = "Testing Error something"
        return max_dynamic_cof, mean_dynamic_cof

    def find_static_cof(self):
        max_static_force, mean_static_force = find_static_force_advanced()

        if test_mode == 0:  # motorize mod
            try:
                max_static_cof = max_static_force / (normal_force * 9.81 * cos(test_angle))
                max_static_cof = round(max_static_cof, 3)

                mean_static_cof = mean_static_force / (normal_force * 9.81 * cos(test_angle))
                mean_static_cof = round(mean_static_cof, 3)
            except TypeError:
                max_static_cof = "Testing Error (type Error)"
                mean_static_cof = "Testing Error (type Error)"
            except:
                max_static_cof = "Error!"
                mean_static_cof = "Error!"

        elif test_mode == 1:  # açı mod
            static_angle = radians(find_static_angle(forces))  # needs to be changed
            try:
                max_static_cof = max_static_force / (normal_force * 9.81 * cos(static_angle))
                max_static_cof = round(max_static_cof, 3)

                mean_static_cof = mean_static_force / (normal_force * 9.81 * cos(static_angle))
                mean_static_cof = round(mean_static_cof, 3)
            except TypeError:
                max_static_cof = "Testing Error (type Error)"
                mean_static_cof = "Testing Error (type Error)"
            except:
                max_static_cof = "Error!"
                mean_static_cof = "Error!"
        else:
            max_static_cof = "Test Mode Select Error!"
            mean_static_cof = "Test Mode Select Error!"

        return max_static_cof, mean_static_cof

    def update_results(self):
        try:
            self.max_dynamic, self.mean_dynamic, self.max_static, self.mean_static = self.create_results()

            self.ids.l_max_static.text = str(self.max_static)
            self.ids.l_mean_static.text = str(self.mean_static)

            self.ids.l_max_dynamic.text = str(self.max_dynamic)
            self.ids.l_mean_dynamic.text = str(self.mean_dynamic)

            if test_mode == 0:
                json_handler.dump_all(self.max_static, self.mean_static, self.max_dynamic, self.mean_dynamic, sample1,
                                      sample2, test_mode, ScreenTwo.plot.points)
            elif test_mode == 1:
                json_handler.dump_all(self.max_static, self.mean_static, self.max_dynamic, self.mean_dynamic, sample1,
                                      sample2, test_mode, ScreenFour.plot.points)
        except:
            pass

    def createPDF(self):
        self.pdf = fpdf_handler()

        self.update_results()

        try:
            self.pdf.create_pdf(self.max_static, self.mean_static, self.max_dynamic, self.mean_dynamic, sample1,
                                sample2, test_mode, ScreenTwo.plot.points)
            self.show_popup()
        except:
            pass

    def show_popup(self):
        show = P()
        self.popupWindow = Popup(title="PDF Saved", content=show, size_hint=(None, None), size=(400, 200))

        self.popupWindow.open()


class ScreenFour(Screen):
    plot = MeshLinePlot(color=[1, 0, 0, 1])

    def __init__(self, **args):
        Screen.__init__(self, **args)
        self.is_reset = False

        # self.reset()  # ilk açılışta otomatik açı resetleme
    
    def get_force_angle(self, arg):
        t = threading.currentThread()
        while getattr(t, "do_run", True):
            start_time = datetime.datetime.now()
            # sleep(sample_time)
            val = hx.get_weight()
            val *= calib
            if val < 0:
                val = 0

            if len(forces) > 1:
                forces.append([time_to_angle(self.time_), val])
            else:
                forces.append([0, val])
            if (forces[-1][1]) > 150:
                global cof_angle_xyz
                cof_angle_xyz = forces[-1][0] - 0.7 # calibration
                self.stop()
            sleep_time = datetime.datetime.now() - start_time
            sleep_time = sleep_time.total_seconds()
            sleep_time = sample_time - sleep_time
            if sleep_time > 0:
                sleep(sleep_time)

    def start(self):
        try:
            gpio.remove_event_detect(angle_switch_start)
            gpio.cleanup(angle_switch_start)

            gpio.remove_event_detect(angle_switch_stop)
            gpio.cleanup(angle_switch_stop)

            gpio.remove_event_detect(start_switch)
            gpio.cleanup(start_switch)

            gpio.remove_event_detect(stop_switch)
            gpio.cleanup(stop_switch)

        except Exception:
            print(Exception)

        global angle_test_normal_motor_distance
        global angle_test_normal_motor_speed
        angle_test_normal_motor_speed = 150
        angle_test_normal_motor_distance = 200

        # if gpio.input(angle_switch_start) or gpio.input(start_switch):
        # self.reset_for_test()
        global forces
        forces = [[0, 0]]

        self.time_ = 0
        self.angle_ = 0
        Clock.schedule_interval(self.timer, 0.1)

        self.ids.graph.remove_plot(self.plot)
        self.ids.graph.add_plot(self.plot)
        self.t = threading.Thread(target=self.get_force_angle, args=("task",))
        self.t.start()

        Clock.schedule_interval(self.get_value,
                                sample_time)  # burada açı test edilebilir, maksimuma geldiğinde durabilir ya da sample
        # kaymaya başlayınca durabilir


        md.start_angle_motor_rise(angle_test_speed)
        self.max_angle_event()


    def timer(self, dt):
        self.time_ = round(self.time_ + 0.1, 2)

    def stop_event(self, channel):
        self.stop()
        return True

    def stop(self):
        try:
            Clock.unschedule(self.get_value)
            Clock.unschedule(self.timer)
            self.time_ = 0
        except:
            pass
        md.stop_motor()
        md.stop_angle_motor()
        # md.stop_motor()
        try:
            gpio.remove_event_detect(angle_switch_start)
            gpio.cleanup(angle_switch_start)

            gpio.remove_event_detect(angle_switch_stop)
            gpio.cleanup(angle_switch_stop)

            gpio.remove_event_detect(start_switch)
            gpio.cleanup(start_switch)

            gpio.remove_event_detect(stop_switch)
            gpio.cleanup(stop_switch)

        except:
            pass
        try:
            self.t.do_run = False
            self.t.join()
        except:
            pass
        if self.is_reset:
            self.start()

    def reset(self):
        self.is_reset = False
        gpio.setup(angle_switch_stop, gpio.IN, pull_up_down=gpio.PUD_UP)
        if gpio.input(angle_switch_stop):
            md.start_angle_motor_rise(angle_test_speed)
            signal.signal(signal.SIGALRM, self.reset_)
            signal.setitimer(signal.ITIMER_REAL, 1, 0)
        else:
            self.reset_(1, 1)

    def reset_(self, signum, _):
        md.stop_angle_motor()
        gpio.setup(angle_switch_start, gpio.IN, pull_up_down=gpio.PUD_UP)
        if gpio.input(angle_switch_start):
            md.start_angle_motor_fall(angle_test_speed)
            self.min_angle_event()

    def save_graph(self):
        self.ids.graph.export_to_png("/home/pi/Cof-Tabs/graph.png")

    def get_value(self, dt):
        if forces[-1][0] == 0:
            self.ids.graph.xmax = 1
        elif forces[-1][0] > self.ids.graph.xmax:
            self.ids.graph.xmax = forces[-1][0]

        if len(forces) < 3:
            self.ids.graph.ymax = 1
        elif forces[-1][1] > self.ids.graph.ymax:
            self.ids.graph.ymax = (forces[-1][1] * 1.1)

        self.ids.graph.y_ticks_major = round(self.ids.graph.ymax / 11, -1)

        self.ids.graph.x_ticks_major = round(self.ids.graph.xmax, -1) * sample_time

        self.plot.points = forces

    def max_angle_event(self):
        try:
            gpio.setup(angle_switch_stop, gpio.IN, pull_up_down=gpio.PUD_UP)
            gpio.add_event_detect(angle_switch_stop, gpio.FALLING, callback=self.stop_event, bouncetime=200)
        except:
            pass

    def min_angle_event(self):
        try:
            gpio.setup(angle_switch_start, gpio.IN, pull_up_down=gpio.PUD_UP)
            gpio.add_event_detect(angle_switch_start, gpio.FALLING, callback=self.stop_event, bouncetime=200)
        except:
            pass

    def motor_forward(self):
        gpio.setup(stop_switch, gpio.IN, pull_up_down=gpio.PUD_UP)
        if gpio.input(stop_switch):
            self.max_distance_event()
            md.motor_start(8000, 0)

    def motor_backward(self):
        gpio.setup(start_switch, gpio.IN, pull_up_down=gpio.PUD_UP)
        if gpio.input(start_switch):
            self.min_distance_event()
            md.motor_start(8000, 1)

    def max_distance_event(self):
        try:
            gpio.setup(stop_switch, gpio.IN, pull_up_down=gpio.PUD_UP)
            gpio.add_event_detect(stop_switch, gpio.FALLING, callback=self.stop_event, bouncetime=200)
        except:
            pass

    def min_distance_event(self):
        try:
            gpio.setup(start_switch, gpio.IN, pull_up_down=gpio.PUD_UP)
            gpio.add_event_detect(start_switch, gpio.FALLING, callback=self.stop_event, bouncetime=200)
        except:
            pass

class ScreenFive(Screen):
    # distance#, speed#, sample time, normal force
    # calibration screen
    def __init__(self, **args):
        Screen.__init__(self, **args)
        self.ids.normal_force.text = str(normal_force)
        self.ids.calib.text = str(calib)

    def save(self):
        count = 0


        if self.ids.normal_force_text.text != "":
            try:
                global normal_force
                normal_force = float(self.ids.normal_force_text.text)
                self.ids.normal_force.text = str(normal_force)
                self.ids.error.color = (0, 0, 0, 0)
            except:
                self.ids.error.text = "Error! (Use only numbers) (use . not ,)"
                self.ids.error.color = (0, 0, 0, 1)
            else:
                count = 1

        if self.ids.calib_text.text != "":
            try:
                global calib
                calib = float(self.ids.calib_text.text)
                self.ids.calib.text = str(calib)
                self.ids.error.color = (0, 0, 0, 0)
            except:
                self.ids.error.text = "Error! (Use only numbers) (use . not ,)"
                self.ids.error.color = (0, 0, 0, 1)
            else:
                count = 1

        if self.ids.normal_force_text.text == "" and self.ids.calib_text.text == "" :
            self.ids.error.color = (0, 0, 0, 0)
        if count == 1:
            self.ids.error.text = "Saved"
            self.ids.error.color = (0, 1, 0, 1)

    def save_for_good(self):
        self.save()
        global test_distance
        global test_speed
        global normal_force
        global sample_time
        global calib
        global angle_test_speed
        global angular_speed
        json_handler.dump_calib_save(distance=test_distance, speed=test_speed, normal_force=normal_force,
                                     sample_time=sample_time, calib=calib, angle_test_speed=angle_test_speed,
                                     angular_speed=angular_speed)

        test_distance, test_speed, normal_force, sample_time, calib, angle_test_speed, angular_speed = json_handler.import_save()

    def reset_to_factory(self):
        global test_distance
        global test_speed
        global normal_force
        global sample_time
        global calib
        global angle_test_speed
        global angular_speed

        test_distance = 24
        test_speed = 24
        normal_force = 199.46
        sample_time = 0.1
        calib = 0.01197
        angle_test_speed = 1250
        angular_speed = 1

        self.ids.normal_force.text = str(normal_force)
        self.ids.calib.text = str(calib)
        json_handler.dump_calib_save(distance=test_distance, speed=test_speed, normal_force=normal_force,
                                     sample_time=sample_time, calib=calib, angle_test_speed=angle_test_speed,
                                     angular_speed=angular_speed)

        test_distance, test_speed, normal_force, sample_time, calib, angle_test_speed, angular_speed = json_handler.import_save()

    def clean_errors(self):
        self.ids.error.color = (0, 0, 0, 0)


class ScreenSix(Screen):
    date_today = datetime.date.today()
    date_text = str(date_today)

    def create_results(self):
        static_cof = str(round(self.find_static_cof(), 3))
        return static_cof

    def find_static_cof(self):
        # find peak
        print(cof_angle_xyz)
        static_cof = (sin((3.1415*cof_angle_xyz)/180)/cos((3.1415*cof_angle_xyz)/180))
        print(static_cof)
        return static_cof

    def update_results(self):
        try:
            self.static_cof = self.create_results()
            self.ids.l_static.text = self.create_results()
            # pdfe de ekle, json düzenle
            self.max_static, self.mean_static, self.max_dynamic, self.mean_dynamic = self.static_cof, self.static_cof, self.static_cof, self.static_cof

            json_handler.dump_all(self.max_static, self.mean_static, self.max_dynamic, self.mean_dynamic, sample1,
                                      sample2, test_mode, ScreenFour.plot.points)
        except:
            pass

    def createPDF(self):
        self.pdf = fpdf_handler()

        self.update_results()

        
        self.pdf.create_pdf_angle(self.max_static, self.mean_static, self.max_dynamic, self.mean_dynamic, sample1,
                                sample2, test_mode, ScreenFour.plot.points)
        self.show_popup()
        
        


    def show_popup(self):
        show = P()
        self.popupWindow = Popup(title="PDF Saved", content=show, size_hint=(None, None), size=(400, 200))

        self.popupWindow.open()


screen_manager = ScreenManager()

screen_manager.add_widget(ScreenOne(name="screen_one"))
screen_manager.add_widget(ScreenTwo(name="screen_two"))
screen_manager.add_widget(ScreenThree(name="screen_three"))
screen_manager.add_widget(ScreenFour(name="screen_four"))
screen_manager.add_widget(ScreenFive(name="screen_five"))
screen_manager.add_widget(ScreenSix(name="screen_six"))


class AwesomeApp(App):
    def build(self):
        Window.clearcolor = (1, 1, 1, 1)
        Window.size = (800, 480)  # pencere boyutu
        Window.fullscreen = True
        return screen_manager


if __name__ == "__main__":
    AwesomeApp().run()
