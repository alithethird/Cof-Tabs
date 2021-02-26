import datetime
from math import cos, sin
import threading
from time import sleep
import RPi.GPIO as gpio
from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Config.set('kivy', 'keyboard_mode', 'systemanddock')
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy_garden.graph import MeshLinePlot
from kivy.uix.popup import Popup
from kivy.uix.floatlayout import FloatLayout

import angle_read
from fpdf_handler import fpdf_handler

gpio.setmode(gpio.BCM)
from hx711 import HX711
from motor_driver import motor_driver
from json_dumper import JsonHandler

# set up the load cell

hx = HX711(5, 6)
hx.set_reading_format("MSB", "MSB")
hx.reset()
hx.tare()

start_switch = 12  # start kısmındaki switch
stop_switch = 13  # stop kısmındaki switch
reset_motor_speed = 200
Builder.load_file('cof.kv')

md = motor_driver(3, False) # bir adet dc bir adet açı(step) motor modu seçildi, soft start kapatıldı
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
forces = [[0,0]]

global calib # kalibrasyon sayısı

def get_force(arg):
    t = threading.currentThread()
    while getattr(t, "do_run", True):
        sleep(sample_time)
        val = hx.get_weight(5)
        val *= calib
        if val < 0:
            val = 1

        if len(forces) > 1:
            forces.append([(forces[-1][0] + sample_time), val])
        else:
            forces.append([0, val])


def get_force_angle(arg): # need to reset angle
    t = threading.currentThread()
    while getattr(t, "do_run", True):
        sleep(sample_time)
        val = hx.get_weight(5)
        val /= calib
        if val < 0:
            val = 1
        angle = angle_read.get_rotation(1)
        if len(forces) > 1:
            if angle > forces[-1][0]:
                forces.append([angle, val])
            else:
                pass
        else:
            forces.append([0, val])


def find_biggest(array):
    biggest = [0.1, 0.1]
    for i in array[:][:]:
        if i[1] > biggest[1]:
            biggest = i
        else:
            pass
    return biggest


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

def find_loose_string(array): # finds loose string length and returns the amount of data acquired when the string is loose
    biggest = find_biggest(forces)
    index = int(((biggest[0] / sample_time)))
    count = 0
    for i in range(1, index):
        if forces[i-1][1] == forces[i][1]:
            count += 1
    return count

    pass
def find_static_force_advanced():
    array = []
    array_mean = 0
    loose = find_loose_string(forces) # ip gergin değilken hesaplanan kuvvetlerin sayısı

    for i in range(loose, int(loose + (1 / sample_time))):
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

    for i in range(index - 1, len(array)):
        array_mean += array[i][1]
    mean_static_force = array_mean / (i - 1)

    return max_static_force, mean_static_force


def find_dynamic_force_advanced():

    loose = find_loose_string(forces) # ip gergin değilken hesaplanan kuvvetlerin sayısı
    array = []
    array_mean = 0
    for i in range(loose, len(forces)):
        array_mean += forces[i][1]
        array.append(forces[i])

    _, max_dynamic_force = find_biggest(array)
    mean_dynamic_force = array_mean / len(array)

    return max_dynamic_force, mean_dynamic_force


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

class ScreenTwo(Screen):
    plot = MeshLinePlot(color=[1, 0, 0, 1])

    def __init__(self, **args):
        Screen.__init__(self, **args)
        global normal_force
        global sample_time
        global test_speed
        global test_distance
        global calib
        global angle_test_speed
        test_distance, test_speed, normal_force, sample_time, calib, angle_test_speed = json_handler.import_save()


        self.force_max_label = Label(text="Peak Force: ")
        self.force_max_label.pos = (230, 215)
        self.force_max_label.color = (0, 0, 0, 1)
        self.add_widget(self.force_max_label)

        self.force_max_text = "0"
        self.force_max = Label(text=self.force_max_text)
        self.force_max.pos = (330, 215)
        self.force_max.color = (0, 0, 0, 1)
        self.add_widget(self.force_max)

        self.force_current_label = Label(text="Current Force: ")
        self.force_current_label.pos = (230, 195)
        self.force_current_label.color = (0, 0, 0, 1)
        self.add_widget(self.force_current_label)

        self.force_text = "0"
        self.force_current = Label(text=self.force_text)
        self.force_current.pos = (330, 195)
        self.force_current.color = (0, 0, 0, 1)
        self.add_widget(self.force_current)

        self.angle_current_label = Label(text="Current Angle: ")
        self.angle_current_label.pos = (230, 155)
        self.angle_current_label.color = (0, 0, 0, 1)
        self.add_widget(self.angle_current_label)

        self.angle_text = str(round(angle_read.get_rotation(1), 2))
        self.angle_current = Label(text=self.angle_text)
        self.angle_current.pos = (330, 155)
        self.angle_current.color = (0, 0, 0, 1)
        self.add_widget(self.angle_current)

        self.dist_current_label = Label(text="Current Distance: ")
        self.dist_current_label.pos = (230, 175)
        self.dist_current_label.color = (0, 0, 0, 1)
        self.add_widget(self.dist_current_label)

        self.dist_text = str(0)
        self.dist_current = Label(text=self.dist_text)
        self.dist_current.pos = (330, 175)
        self.dist_current.color = (0, 0, 0, 1)
        self.add_widget(self.dist_current)

        #self.reset()  # reset when program starts

    def start(self):
        global forces
        forces = [[0, 0]]
        self.ids.graph.remove_plot(self.plot)
        self.ids.graph.add_plot(self.plot)
        self.t = threading.Thread(target=get_force, args=("task",))
        self.t.start()

        Clock.schedule_interval(self.get_value, sample_time)
        self.dist_current.text = "0"

        # if self.ids.distance_text.text == "":
        #     pass
        # else:
        #     self.test_distance = float(self.ids.distance_text.text)
        #
        # if self.ids.speed_text.text == "":
        #     pass
        # else:
        #     self.test_speed = float(self.ids.speed_text.text)

        drive_time, frequency, direction = md.calculate_ticks(distance=test_distance, speed=test_speed, direction=0)
        md.motor_run(drive_time, frequency, direction)

    def stop(self):
        md.stop_motor()
        Clock.unschedule(self.get_value)
        try:
            self.t.do_run = False
            self.t.join()
            #self.reset()  # reset when test ends
        except:
            pass

    def reset(self):
        pass
        #while start_switch:
         #   md.motor_start(reset_motor_speed, 0)
        #md.stop_motor()

    def save_graph(self):
        self.ids.graph.export_to_png("graph.png")

    def get_value(self, dt):
        self.dist_current.text = str(float(self.dist_current.text) + 60*(sample_time * test_speed))  # update current distance

        if forces[-1][0] == 0:
            self.ids.graph.xmax = 1
        elif forces[-1][0] > self.ids.graph.xmax:
            self.ids.graph.xmax = forces[-1][0]

        if len(forces) < 3:
            self.ids.graph.ymax = 1
        elif forces[-1][1] > self.ids.graph.ymax:
            self.force_max.text = str(round(forces[-1][1], 3))
            self.ids.graph.ymax = forces[-1][1]

        self.ids.graph.y_ticks_major = round(self.ids.graph.ymax, -1) / 10

        self.ids.graph.x_ticks_major = round(self.ids.graph.xmax, -1) * sample_time

        self.plot.points = forces

        self.force_current.text = str(round(forces[-1][1], 2))

    def show_angle(self, angle):

        angle = str(angle)
        self.angle_current.text = angle

    def motor_forward(self):
        md.motor_start(200, 1)

    def motor_backward(self):
        md.motor_start(200, 0)


class P(FloatLayout):
    pass

class ScreenThree(Screen):
    date_today = datetime.date.today()
    date_text = str(date_today)
    date_text = date_text

    def __init__(self, **args):
        Screen.__init__(self, **args)

        self.max_static_cof_text = "0"
        self.l_max_static = Label(text=self.max_static_cof_text)
        self.l_max_static.pos = (-90, 143)
        self.l_max_static.color = (0, 0, 0, 1)
        self.add_widget(self.l_max_static)

        self.mean_static_cof_text = "0"
        self.l_mean_static = Label(text=self.mean_static_cof_text)
        self.l_mean_static.pos = (-90, 95)
        self.l_mean_static.color = (0, 0, 0, 1)
        self.add_widget(self.l_mean_static)

        self.max_dynamic_cof_text = "0"
        self.l_max_dynamic = Label(text=self.max_dynamic_cof_text)
        self.l_max_dynamic.pos = (-90, 0)
        self.l_max_dynamic.color = (0, 0, 0, 1)
        self.add_widget(self.l_max_dynamic)

        self.mean_dynamic_cof_text = "0"
        self.l_mean_dynamic = Label(text=self.mean_dynamic_cof_text)
        self.l_mean_dynamic.pos = (-90, -48)
        self.l_mean_dynamic.color = (0, 0, 0, 1)
        self.add_widget(self.l_mean_dynamic)

    def create_results(self):
        max_dynamic_cof, mean_dynamic_cof = self.find_dynamic_cof()
        max_static_cof, mean_static_cof = self.find_static_cof()
        return max_dynamic_cof, mean_dynamic_cof, max_static_cof, mean_static_cof

    def find_dynamic_cof(self):
        if test_mode == 0:  # motorize mod
            max_dynamic_force, mean_dynamic_force = find_dynamic_force_advanced()
            try:
                mean_dynamic_cof = mean_dynamic_force / (normal_force * 9.81 * cos(test_angle))
                mean_dynamic_cof = round(mean_dynamic_cof, 3)

                max_dynamic_cof = max_dynamic_force / (normal_force * 9.81 * cos(test_angle))
                max_dynamic_cof = round(max_dynamic_cof, 3)
            except TypeError:
                mean_dynamic_cof = "Testing Error (type Error)"
                max_dynamic_cof = "Testing Error (type Error)"
            except:
                mean_dynamic_cof = "Testing Error something"
                max_dynamic_cof = "Testing Error something"
        elif test_mode == 1:  # açı mod #** ekleme yapılacak max ve mean için
            try:
                dynamic_cof = ScreenFour.plot.points[-1][1] / (normal_force * 9.81 * cos( ScreenFour.plot.points[-1][0])) #en sondaki kuvvet ile o açıdaki normal kuvveti birbirine bölerek
                mean_dynamic_cof = round(dynamic_cof, 3)
                max_dynamic_cof = round(dynamic_cof, 3)
            except TypeError:
                mean_dynamic_cof = "Testing Error (type Error)"
            except:
                mean_dynamic_cof = "Testing Error something"
        else:
            dynamic_cof = "Test Mode Select Error!"
        return max_dynamic_cof, mean_dynamic_cof

    def find_static_cof(self):
        try:
            if test_mode == 0:  # motorize mod
                max_static_force, mean_static_force = find_static_force_advanced()

                max_static_cof = max_static_force / (normal_force * 9.81 * cos(test_angle))
                max_static_cof = round(max_static_cof, 3)

                mean_static_cof = mean_static_force / (normal_force * 9.81 * cos(test_angle))
                mean_static_cof = round(mean_static_cof, 3)

            elif test_mode == 1:  # açı mod
                max_static_force, mean_static_force = find_static_force_advanced()
                static_angle, static_force = find_biggest(forces)

                max_static_cof = max_static_force / (normal_force * 9.81 * cos(static_angle))
                max_static_cof = round(max_static_cof, 3)

                mean_static_cof = mean_static_force / (normal_force * 9.81 * cos(static_angle))
                mean_static_cof = round(mean_static_cof, 3)
            else:
                max_static_cof = "Test Mode Select Error!"
                mean_static_cof = "Test Mode Select Error!"
        except:
            max_static_cof = "Error!"
            mean_static_cof = "Error!"
        return max_static_cof, mean_static_cof

    def update_results(self):
        self.max_dynamic, self.mean_dynamic, self.max_static, self.mean_static = self.create_results()
        self.max_static_cof_text = str(self.max_static)
        self.mean_static_cof_text = str(self.mean_static)

        self.max_dynamic_cof_text = str(self.max_dynamic)
        self.mean_dynamic_cof_text = str(self.mean_dynamic)

        self.l_max_static.text = self.max_static_cof_text
        self.l_mean_static.text = self.mean_static_cof_text

        self.l_max_dynamic.text = self.max_dynamic_cof_text
        self.l_mean_dynamic.text = self.mean_dynamic_cof_text

        if test_mode == 0:
            json_handler.dump_all(self.max_static, self.mean_static, self.max_dynamic, self.mean_dynamic, sample1, sample2, test_mode, ScreenTwo.plot.points)
        elif test_mode == 1:
            json_handler.dump_all(self.max_static, self.mean_static, self.max_dynamic, self.mean_dynamic, sample1, sample2, test_mode, ScreenFour.plot.points)

    def createPDF(self):
        self.pdf = fpdf_handler()

        self.update_results()

        if test_mode == 0:
            self.pdf.create_pdf(self.max_static, self.mean_static, self.max_dynamic, self.mean_dynamic, sample1, sample2, test_mode, ScreenTwo.plot.points)
        else:
            self.pdf.create_pdf(self.max_static, self.mean_static, self.max_dynamic, self.mean_dynamic, sample1, sample2, test_mode, ScreenFour.plot.points)

        self.show_popup()

    def show_popup(self):
        show = P()
        self.popupWindow = Popup(title="Popup Window", content=show, size_hint=(None, None), size=(400, 400))

        self.popupWindow.open()

class ScreenFour(Screen):
    plot = MeshLinePlot(color=[1, 0, 0, 1])

    def __init__(self, **args):
        Screen.__init__(self, **args)

        self.force_max_label = Label(text="Peak Force: ")
        self.force_max_label.pos = (230, 215)
        self.force_max_label.color = (0, 0, 0, 1)
        self.add_widget(self.force_max_label)

        self.force_max_text = "0"
        self.force_max = Label(text=self.force_max_text)
        self.force_max.pos = (330, 215)
        self.force_max.color = (0, 0, 0, 1)
        self.add_widget(self.force_max)

        self.force_current_label = Label(text="Current Force: ")
        self.force_current_label.pos = (230, 195)
        self.force_current_label.color = (0, 0, 0, 1)
        self.add_widget(self.force_current_label)

        self.force_text = "0"
        self.force_current = Label(text=self.force_text)
        self.force_current.pos = (330, 195)
        self.force_current.color = (0, 0, 0, 1)
        self.add_widget(self.force_current)

        self.angle_current_label = Label(text="Current Angle: ")
        self.angle_current_label.pos = (230, 155)
        self.angle_current_label.color = (0, 0, 0, 1)
        self.add_widget(self.angle_current_label)

        self.angle_text = str(round(angle_read.get_rotation(1), 2))
        self.angle_current = Label(text=self.angle_text)
        self.angle_current.pos = (330, 155)
        self.angle_current.color = (0, 0, 0, 1)
        self.add_widget(self.angle_current)

    def start(self):
        global forces
        forces = [[0, 0]]
        self.ids.graph.remove_plot(self.plot)
        self.ids.graph.add_plot(self.plot)
        self.t = threading.Thread(target=get_force_angle, args=("task",))
        self.t.start()

        Clock.schedule_interval(self.get_value,
                                sample_time)  # burada açı test edilebilir, maksimuma geldiğinde durabilir ya da sample kaymaya başlayınca durabilir

        md.start_angle_motor_rise(angle_test_speed)

    def stop(self):
        Clock.unschedule(self.get_value)
        md.stop_angle_motor()
        try:
            self.t.do_run = False
            self.t.join()
        except:
            pass
    def reset(self):
        while self.check_angle(0):
            md.start_angle_motor_fall(angle_test_speed)
        md.stop_angle_motor()

    def save_graph(self):
        self.ids.graph.export_to_png("graph.png")

    def get_value(self, dt):
        max_angle = 30
        if self.check_angle(max_angle):

            if forces[-1][0] == 0:
                self.ids.graph.xmax = 1
            elif forces[-1][0] > self.ids.graph.xmax:
                self.ids.graph.xmax = forces[-1][0]

            if len(forces) < 3:
                self.ids.graph.ymax = 1
            elif forces[-1][1] > self.ids.graph.ymax:
                self.force_max.text = str(round(forces[-1][1],3))
                self.ids.graph.ymax = forces[-1][1]

            self.ids.graph.y_ticks_major = round(self.ids.graph.ymax, -1) / 10

            self.ids.graph.x_ticks_major = round(self.ids.graph.xmax, -1) / 10
            self.plot.points = forces
            self.angle_current.text = str(round(forces[-1][1], 2))
        else:
            md.stop_angle_motor()
            Clock.unschedule(self.get_value)
            self.t.do_run = False
            self.t.join()

    def check_angle(self, angle):
        val = round(angle_read.get_rotation(1), 2)
        if val <= angle + 1 and val >= angle - 1:
            return False
        else:
            return True

    def angle_motor_rise(self):
        md.start_angle_motor_rise(angle_test_speed)

    def angle_motor_fall(self):
        md.start_angle_motor_fall(angle_test_speed)


class ScreenFive(Screen):
    # distance#, speed#, sample time, normal force
    # calibration screen
    def __init__(self, **args):
        Screen.__init__(self, **args)
        self.error_text = "Error! (Use only numbers) (use . not ,)"
        self.error = Label(text=self.error_text)
        self.error.pos = (0, 230)
        self.error.color = (0, 0, 0, 0)
        self.add_widget(self.error)
        self.ids.distance.text = str(test_distance)
        self.ids.speed.text = str(test_speed)
        self.ids.normal_force.text = str(normal_force)
        self.ids.sample_time.text = str(sample_time)
        self.ids.calib.text = str(calib)
        self.ids.angle_test_speed.text = str(angle_test_speed)

    def save(self):
        count = 0
        if self.ids.distance_text.text != "":
            try:
                global test_distance
                test_distance = float(self.ids.distance_text.text)
                self.ids.distance.text = str(test_distance)

                self.error.color = (0, 0, 0, 0)
            except:
                self.error.text = "Error! (Use only numbers) (use . not ,)"
                self.error.color = (0, 0, 0, 1)
            else:
                count = 1

        if self.ids.speed_text.text != "":
            try:
                global test_speed
                test_speed = float(self.ids.speed_text.text)
                self.ids.speed.text = str(test_speed)
                self.error.color = (0, 0, 0, 0)
            except:
                self.error.text = "Error! (Use only numbers) (use . not ,)"
                self.error.color = (0, 0, 0, 1)
            else:
                count = 1

        if self.ids.normal_force_text.text != "":
            try:
                global normal_force
                normal_force = float(self.ids.normal_force_text.text)
                self.ids.normal_force.text = str(normal_force)
                self.error.color = (0, 0, 0, 0)
            except:
                self.error.text = "Error! (Use only numbers) (use . not ,)"
                self.error.color = (0, 0, 0, 1)
            else:
                count = 1

        if self.ids.sample_time_text.text != "":
            try:
                global sample_time
                sample_time = float(self.ids.sample_time_text.text)
                self.ids.sample_time.text = str(sample_time)
                self.error.color = (0, 0, 0, 0)
            except:
                self.error.text = "Error! (Use only numbers) (use . not ,)"
                self.error.color = (0, 0, 0, 1)
            else:
                count = 1

        if self.ids.calib_text.text != "":
            try:
                global calib
                calib = float(self.ids.calib_text.text)
                self.ids.calib.text = str(calib)
                self.error.color = (0, 0, 0, 0)
            except:
                self.error.text = "Error! (Use only numbers) (use . not ,)"
                self.error.color = (0, 0, 0, 1)
            else:
                count = 1

        if self.ids.angle_test_speed_text.text != "":
            try:
                global angle_test_speed
                angle_test_speed = float(self.ids.angle_test_speed_text.text)
                self.ids.angle_test_speed.text = str(angle_test_speed)

                self.error.color = (0, 0, 0, 0)
            except:
                self.error.text = "Error! (Use only numbers) (use . not ,)"
                self.error.color = (0, 0, 0, 1)
            else:
                count = 1

        if self.ids.speed_text.text == "" and self.ids.distance_text.text == "" and self.ids.sample_time_text.text == "" and self.ids.normal_force_text.text == "" and self.ids.calib_text.text == "" and self.ids.angle_test_speed_text.text == "":
            self.error.color = (0, 0, 0, 0)
        if count == 1:
            self.error.text = "Saved"
            self.error.color = (0, 1, 0, 1)

    def save_for_good(self):
        self.save()
        global test_distance
        global test_speed
        global normal_force
        global sample_time
        global calib
        global angle_test_speed
        json_handler.dump_calib_save(distance=test_distance, speed=test_speed, normal_force=normal_force, sample_time=sample_time, calib=calib, angle_test_speed=angle_test_speed)

        test_distance, test_speed, normal_force, sample_time, calib, angle_test_speed = json_handler.import_save()

    def reset_to_factory(self):
        global test_distance
        global test_speed
        global normal_force
        global sample_time
        global calib
        global angle_test_speed

        test_distance = 60
        test_speed = 150
        normal_force = 200
        sample_time = 0.1
        calib = 0.011772
        angle_test_speed = 100

        self.ids.distance.text = str(test_distance)
        self.ids.speed.text = str(test_speed)
        self.ids.normal_force.text = str(normal_force)
        self.ids.sample_time.text = str(sample_time)
        self.ids.calib.text = str(calib)
        self.ids.angle_test_speed.text = str(angle_test_speed)
        json_handler.dump_calib_save(distance=test_distance, speed=test_speed, normal_force=normal_force, sample_time=sample_time, calib=calib, angle_test_speed=angle_test_speed)

        test_distance, test_speed, normal_force, sample_time, calib, angle_test_speed = json_handler.import_save()


    def clean_errors(self):
        self.error.color = (0, 0, 0, 0)


screen_manager = ScreenManager()

screen_manager.add_widget(ScreenOne(name="screen_one"))
screen_manager.add_widget(ScreenTwo(name="screen_two"))
screen_manager.add_widget(ScreenThree(name="screen_three"))
screen_manager.add_widget(ScreenFour(name="screen_four"))
screen_manager.add_widget(ScreenFive(name="screen_five"))


class AwesomeApp(App):
    def build(self):
        Window.clearcolor = (1, 1, 1, 1)
        Window.size = (800, 480)  # pencere boyutu
        Window.fullscreen = True
        return screen_manager


if __name__ == "__main__":
    AwesomeApp().run()
