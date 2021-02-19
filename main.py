from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy_garden.graph import MeshLinePlot
from kivy.clock import Clock

import datetime
from fpdf_handler import fpdf_handler

import RPi.GPIO as gpio
import angle_read
from math import cos, sin

gpio.setmode(gpio.BCM)
from hx711 import HX711
from motor_driver import motor_driver

# set up the load cell

hx = HX711(5, 6)
hx.set_reading_format("MSB", "MSB")
hx.reset()
hx.tare()

Builder.load_file('cof.kv')

md = motor_driver()


class sample:
    name = ""
    width = 0
    height = 0
    age = 0

test_mode = -1 # 0-motorized test
               # 1-angle test


sample1 = sample()
sample2 = sample()

global normal_force # üstte kayan metal malzemenin kütlesi (kg)
normal_force = 0.2
global test_angle
test_angle = 0

global forces
forces = [[0, 0]]

sample_time = 0.1


def get_force():
    val = hx.get_weight(5)
    calib = 1  # kalibrasyon sayısı
    val /= calib
    if val < 0:
        val = 1
    if len(forces) > 1:
        forces.append([round((forces[-1][0] + sample_time), 4), val])
    else:
        forces.append([0, val])

def find_biggest(array):
    biggest = [0.1,0.1]
    for i in array[:][:]:
        if i[1] > biggest[1]:
            biggest = i
        else:
            pass
    return biggest

def find_dynamic_force(array):
    # take last 20 elements of the list
    # find the median
    if len(array) > 10:
        median = 0
        for i in range(20):
            median += forces[-(i + 1)][1]
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
        test_mode  = 1

    def btn_text(self):
        sample1.name = self.ids.first_name.text
        sample1.width = self.ids.first_width.text
        sample1.height = self.ids.first_height.text
        sample1.age = self.ids.first_age.text
        if self.ids.switch.active:
            sample2.name = self.ids.second_name.text
            sample2.width = self.ids.second_width.text
            sample2.height = self.ids.second_height.text
            sample2.age = self.ids.second_age.text


class ScreenTwo(Screen):
    plot = MeshLinePlot(color=[1, 0, 0, 1])

    def __init__(self, **args):
        Screen.__init__(self, **args)
        self.force_current_label = Label(text="Current Force: ")
        self.force_current_label.pos = (-335, 155)
        self.force_current_label.color = (0,0,0,1)
        self.add_widget(self.force_current_label)

        self.force_text = "0"
        self.force_current = Label(text=self.force_text)
        self.force_current.pos = (-225, 155)
        self.force_current.color = (0,0,0,1)
        self.add_widget(self.force_current)

        self.angle_current_label = Label(text="Current Angle: ")
        self.angle_current_label.pos = (200, 170)
        self.angle_current_label.color = (0,0,0,1)
        self.add_widget(self.angle_current_label)

        self.angle_text = str(round(angle_read.get_rotation(1), 2))
        self.angle_current = Label(text=self.angle_text)
        self.angle_current.pos = (300, 170)
        self.angle_current.color = (0,0,0,1)
        self.add_widget(self.angle_current)

    def start(self):
        forces.clear()
        self.ids.graph.remove_plot(self.plot)
        self.ids.graph.add_plot(self.plot)
        Clock.schedule_interval(self.get_value, sample_time)

        if self.ids.distance_text.text == "":
            self.test_distance = 60
        else:
            self.test_distance = float(self.ids.distance_text.text)

        if self.ids.speed_text.text == "":
            self.test_speed = 150
        else:
            self.test_speed = float(self.ids.speed_text.text)

        self.drive_time, self.frequency, self.direction = md.calculate_ticks( self.test_distance, self.test_speed, 1)
        md.motor_run(self.drive_time, self.frequency, self.direction)

    def stop(self):
        Clock.unschedule(self.get_value)
        md.stop_motor()

    def reset(self):
        self.drive_time, self.frequency, self.direction = md.calculate_ticks(self.test_distance, self.test_speed, 0)
        md.motor_run(self.drive_time, self.frequency, self.direction)

    def save_graph(self):
        self.ids.graph.export_to_png("graph.png")

    def get_value(self, dt):
        get_force()

        if forces[-1][0] == 0:
            self.ids.graph.xmax = 1
        elif forces[-1][0] > self.ids.graph.xmax:
            self.ids.graph.xmax = forces[-1][0]

        if forces[-1][1] == 0:
            self.ids.graph.ymax = 1
        elif forces[-1][1] > self.ids.graph.ymax:
            self.ids.graph.ymax = forces[-1][1]

        self.ids.graph.y_ticks_major = round(self.ids.graph.ymax, -1)/10

        self.ids.graph.x_ticks_major = round(self.ids.graph.xmax, -1)/10
        self.plot.points = forces
        self.force_current.text = str(round(forces[-1][1], 2))

    def show_angle(self, angle):

        angle = str(angle)
        self.angle_current.text = angle

    def set_angle(self):
        angle = self.ids.angle_text.text
        if angle != "":
            try:
                angle = int(angle)
                while self.check_angle(angle):
                    val = round(angle_read.get_rotation(1), 2)
                    freq = (angle - val) * 20
                    self.show_angle(val)
                    if freq > 0:
                        md.start_angle_motor_rise(freq)
                    else:
                        freq *= -1
                        md.start_angle_motor_fall(freq)
                md.stop_angle_motor()
            except:
                pass
        else:
            pass

    def check_angle(self, angle):
        val = round(angle_read.get_rotation(1), 2)
        self.show_angle(val)
        if val <= angle + 1 and val >= angle - 1:
            return False
        else:
            return True


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
        self.l_static.color = (0,0,0,1)
        self.add_widget(self.l_static)

        self.dynamic_cof_text = "0"
        self.l_dynamic = Label(text=self.dynamic_cof_text)
        self.l_dynamic.pos = -90, 0
        self.l_dynamic.color = (0,0,0,1)

        self.add_widget(self.l_dynamic)


    def create_results(self):
        dynamic_cof = self.find_dynamic_cof()
        static_cof = self.find_static_cof()
        return dynamic_cof, static_cof

    def find_dynamic_cof(self):
        dynamic_force = find_dynamic_force(forces)
        if test_mode == 0:
            try:
                dynamic_cof = dynamic_force / (normal_force * 9.81 * cos(test_angle))
                dynamic_cof = round(dynamic_cof, 3)
            except TypeError:
                dynamic_cof = "Testing Error (type Error)"
            except:
                dynamic_cof = "Testing Error something"
        elif test_mode == 1:
            try:
                dynamic_cof = dynamic_force / (normal_force * 9.81 * cos(test_angle))
                dynamic_cof = round(dynamic_cof, 3)
            except TypeError:
                dynamic_cof = "Testing Error (type Error)"
            except:
                dynamic_cof = "Testing Error something"
        else:
            dynamic_cof = "Test Mode Select Error!"
        return dynamic_cof

    def find_static_cof(self):
        if test_mode == 0:
            static_angle, static_force = find_biggest(forces)
            static_cof = float(static_force) / (normal_force * 9.81 * cos(test_angle))
            static_cof = round(static_cof, 3)
        elif test_mode == 1:
            static_angle, static_force = find_biggest(forces)
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

    def createPDF(self):
        self.pdf = fpdf_handler()
        self.pdf.create_pdf( self.static, self.dynamic, sample1, sample2, test_mode)

class ScreenFour(Screen):
    plot = MeshLinePlot(color=[1, 0, 0, 1])

    def __init__(self, **args):
        Screen.__init__(self, **args)
        self.angle_current_label = Label(text="Current Angle: ")
        self.angle_current_label.pos = (-335, 170)
        self.angle_current_label.color = (0,0,0,1)
        self.add_widget(self.angle_current_label)

        self.angle_text = str(round(angle_read.get_rotation(1), 2))
        self.angle_current = Label(text=self.angle_text)
        self.angle_current.pos = (-225, 170)
        self.angle_current.color = (0,0,0,1)
        self.add_widget(self.angle_current)

    def start(self):
        forces.clear()
        self.ids.graph.remove_plot(self.plot)
        self.ids.graph.add_plot(self.plot)
        Clock.schedule_interval(self.get_value, sample_time) # burada açı test edilebilir, maksimuma geldiğinde durabilir ya da sample kaymaya başlayınca durabilir

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
            get_force()

            if forces[-1][0] == 0:
                self.ids.graph.xmax = 1
            elif forces[-1][0] > self.ids.graph.xmax:
                self.ids.graph.xmax = forces[-1][0]

            if forces[-1][1] == 0:
                self.ids.graph.ymax = 1
            elif forces[-1][1] > self.ids.graph.ymax:
                self.ids.graph.ymax = forces[-1][1]

            self.ids.graph.y_ticks_major = round(self.ids.graph.ymax,-1)/10

            self.ids.graph.x_ticks_major = round(self.ids.graph.xmax,-1)/10
            self.plot.points = forces
            self.angle_current.text = str(round(forces[-1][1],2))
        else:
            md.stop_angle_motor()
            Clock.unschedule(self.get_value)


    def check_angle(self, angle):
        val = round(angle_read.get_rotation(1), 2)
        if val <= angle + 1 and val >= angle - 1:
            return False
        else:
            return True

screen_manager = ScreenManager()

screen_manager.add_widget(ScreenOne(name="screen_one"))
screen_manager.add_widget(ScreenTwo(name="screen_two"))
screen_manager.add_widget(ScreenThree(name="screen_three"))
screen_manager.add_widget(ScreenFour(name="screen_four"))


class AwesomeApp(App):
    def build(self):
        Window.clearcolor = (1, 1, 1, 1)
        Window.size = (800, 480)  # pencere boyutu
        return screen_manager


if __name__ == "__main__":
    AwesomeApp().run()

