import datetime
from math import cos, sin

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

md = motor_driver()
json_handler = JsonHandler()


class sample:
    name = ""
    width = 0
    height = 0
    age = 0
    testing_weight = 0
    company_name = ""
    operator_name = ""

test_mode = -1  # 0-motorized test
# 1-angle test

sample1 = sample()
sample2 = sample()

global normal_force  # üstte kayan metal malzemenin kütlesi (kg)
normal_force = 200
global test_angle
test_angle = 0

sample_time = 0.1
sample_time_angle = 0.5

def get_force(forces):
    val = hx.get_weight(5)
    calib = 0.0012* 9.81  # kalibrasyon sayısı
    val *= calib
    if val < 0:
        val = 1

    if len(forces) > 1:
        forces.append([(forces[-1][0] + sample_time), val])
    else:
        forces.append([0, val])


def get_force_angle(forces):
    val = hx.get_weight(5)
    calib = 1  # kalibrasyon sayısı
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


def find_dynamic_force(array):
    # take last 20 elements of the list
    # find the median
    if len(array) > 20:
        median = 0
        for i in range(20):
            median += array[-(i + 1)][1]
        median /= 20
        return median
    else:
        return 1


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
        test_distance, test_speed, normal_force, sample_time = json_handler.import_save()

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
        self.plot.points = [[0, 0]]
        self.ids.graph.remove_plot(self.plot)
        self.ids.graph.add_plot(self.plot)
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
        Clock.unschedule(self.get_value)
        md.stop_motor()
        #self.reset()  # reset when test ends

    def reset(self):
        pass
        #while start_switch:
         #   md.motor_start(reset_motor_speed, 0)
        #md.stop_motor()

    def save_graph(self):
        self.ids.graph.export_to_png("graph.png")

    def get_value(self, dt):
        get_force(self.plot.points)
        self.dist_current.text = str(float(self.dist_current.text) + 60*(sample_time * test_speed))  # update current distance

        if self.plot.points[-1][0] == 0:
            self.ids.graph.xmax = 1
        elif self.plot.points[-1][0] > self.ids.graph.xmax:
            self.ids.graph.xmax = self.plot.points[-1][0]

        if len(self.plot.points) < 3:
            self.ids.graph.ymax = 1
        elif self.plot.points[-1][1] > self.ids.graph.ymax:
            self.force_max.text = str(round(self.plot.points[-1][1], 3))
            self.ids.graph.ymax = self.plot.points[-1][1]

        self.ids.graph.y_ticks_major = round(self.ids.graph.ymax, -1) / 10

        self.ids.graph.x_ticks_major = round(self.ids.graph.xmax, -1) * sample_time

        self.force_current.text = str(round(self.plot.points[-1][1], 2))

    def show_angle(self, angle):

        angle = str(angle)
        self.angle_current.text = angle

    def motor_forward(self):
        md.motor_start(200, 1)
    def motor_backward(self):
        md.motor_start(200, 0)



class ScreenThree(Screen):
    date_today = datetime.date.today()
    date_text = str(date_today)
    date_text = date_text

    def __init__(self, **args):
        Screen.__init__(self, **args)
        self.static_cof_text = "0"
        self.l_static = Label(text=self.static_cof_text)
        self.l_static.pos = (-90, 95)
        self.l_static.pos_hint_x = 0.5
        self.l_static.color = (0, 0, 0, 1)
        self.add_widget(self.l_static)

        self.dynamic_cof_text = "0"
        self.l_dynamic = Label(text=self.dynamic_cof_text)
        self.l_dynamic.pos = -90, 0
        self.l_dynamic.color = (0, 0, 0, 1)

        self.add_widget(self.l_dynamic)

    def create_results(self):
        dynamic_cof = self.find_dynamic_cof()
        static_cof = self.find_static_cof()
        return dynamic_cof, static_cof

    def find_dynamic_cof(self):
        if test_mode == 0:  # motorize mod
            dynamic_force = find_dynamic_force(ScreenTwo.plot.points)
            try:
                dynamic_cof = dynamic_force / (normal_force * 9.81 * cos(test_angle))
                dynamic_cof = round(dynamic_cof, 3)
            except TypeError:
                dynamic_cof = "Testing Error (type Error)"
            except:
                dynamic_cof = "Testing Error something"
        elif test_mode == 1:  # açı mod
            try:
                dynamic_cof = ScreenFour.plot.points[-1][1] / (normal_force * 9.81 * cos( ScreenFour.plot.points[-1][0])) #en sondaki kuvvet ile o açıdaki normal kuvveti birbirine bölerek
                dynamic_cof = round(dynamic_cof, 3)
            except TypeError:
                dynamic_cof = "Testing Error (type Error)"
            except:
                dynamic_cof = "Testing Error something"
        else:
            dynamic_cof = "Test Mode Select Error!"
        return dynamic_cof

    def find_static_cof(self):
        if test_mode == 0:  # motorize mod
            static_angle, static_force = find_biggest(ScreenTwo.plot.points)
            static_cof = float(static_force) / (normal_force * 9.81 * cos(test_angle))
            static_cof = round(static_cof, 3)
        elif test_mode == 1:  # açı mod
            static_angle, static_force = find_biggest(ScreenFour.plot.points)
            static_cof = float(static_force) / (normal_force * 9.81 * cos(static_angle))
            static_cof = round(static_cof, 3)
        else:
            static_cof = "Test Mode Select Error!"
        return static_cof

    def update_results(self):
        self.dynamic, self.static = self.create_results()
        self.static_cof_text = str(self.static)
        self.dynamic_cof_text = str(self.dynamic)

        self.l_dynamic.text = self.dynamic_cof_text
        self.l_static.text = self.static_cof_text
        if test_mode == 0:
            json_handler.dump_all(self.static, self.dynamic, sample1, sample2, test_mode, ScreenTwo.plot.points)
        elif test_mode == 1:
            json_handler.dump_all(self.static, self.dynamic, sample1, sample2, test_mode, ScreenFour.plot.points)

    def createPDF(self):
        self.pdf = fpdf_handler()

        self.update_results()
        if test_mode == 0:
            self.pdf.create_pdf(self.static, self.dynamic, sample1, sample2, test_mode, ScreenTwo.plot.points)
        elif test_mode == 1:
            self.pdf.create_pdf(self.static, self.dynamic, sample1, sample2, test_mode, ScreenFour.plot.points)


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
        self.plot.points = [[0, 0]]
        self.ids.graph.remove_plot(self.plot)
        self.ids.graph.add_plot(self.plot)
        Clock.schedule_interval(self.get_value,
                                sample_time_angle)  # burada açı test edilebilir, maksimuma geldiğinde durabilir ya da sample kaymaya başlayınca durabilir

        md.start_angle_motor_rise(50)

    def stop(self):
        Clock.unschedule(self.get_value)
        md.stop_angle_motor()

    def reset(self):
        while self.check_angle(0):
            md.start_angle_motor_fall(50)
        md.stop_angle_motor()

    def save_graph(self):
        self.ids.graph.export_to_png("graph.png")

    def get_value(self, dt):
        max_angle = 30
        if self.check_angle(max_angle):
            get_force_angle()

            if self.plot.points[-1][0] == 0:
                self.ids.graph.xmax = 1
            elif self.plot.points[-1][0] > self.ids.graph.xmax:
                self.ids.graph.xmax = self.plot.points[-1][0]

            if len(self.plot.points) < 3:
                self.ids.graph.ymax = 1
            elif self.plot.points[-1][1] > self.ids.graph.ymax:
                self.force_max.text = str(round(self.plot.points[-1][1],3))
                self.ids.graph.ymax = self.plot.points[-1][1]

            self.ids.graph.y_ticks_major = round(self.ids.graph.ymax, -1) / 10

            self.ids.graph.x_ticks_major = round(self.ids.graph.xmax, -1) / 10

            self.angle_current.text = str(round(self.plot.points[-1][1], 2))
        else:
            md.stop_angle_motor()
            Clock.unschedule(self.get_value)

    def check_angle(self, angle):
        val = round(angle_read.get_rotation(1), 2)
        if val <= angle + 1 and val >= angle - 1:
            return False
        else:
            return True

    def angle_motor_rise(self):
        md.start_angle_motor_rise(50)

    def angle_motor_fall(self):
        md.start_angle_motor_fall(50)



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
    def save(self):
        count = 0
        if self.ids.distance_text.text != "":
            try:
                global test_distance
                test_distance = float(self.ids.distance_text.text)
                self.ids.distance.text = str(test_distance)

                self.error.color = (0,0,0,0)
            except:
                self.error.text = "Error! (Use only numbers) (use . not ,)"
                self.error.color = (0,0,0,1)
            else:
                count = 1

        if self.ids.speed_text.text != "":
            try:
                global test_speed
                test_speed = float(self.ids.speed_text.text)
                self.ids.speed.text = str(test_speed)
                self.error.color = (0,0,0,0)
            except:
                self.error.text = "Error! (Use only numbers) (use . not ,)"
                self.error.color = (0,0,0,1)
            else:
                count = 1

        if self.ids.normal_force_text.text != "": #normal force nerede lo
            try:
                global normal_force
                normal_force = float(self.ids.normal_force_text.text)
                self.ids.normal_force.text = str(normal_force)
                self.error.color = (0,0,0,0)
            except:
                self.error.text = "Error! (Use only numbers) (use . not ,)"
                self.error.color = (0,0,0,1)
            else:
                count = 1

        if self.ids.sample_time_text.text != "":  # normal force nerede lo
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

        if self.ids.speed_text.text == "" and self.ids.distance_text.text == "" and self.ids.sample_time_text.text == "" and self.ids.normal_force_text.text == "":
            self.error.color = (0,0,0,0)
        if count == 1:
            self.error.text = "Saved"
            self.error.color = (0,0,0,1)
    def save_for_good(self):
        self.save()
        json_handler.dump_calib_save(distance=test_distance, speed=test_speed, normal_force=normal_force, sample_time=sample_time)
        json_handler.import_save()
    def clean_errors(self):
        self.error.color = (0,0,0,0)


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
